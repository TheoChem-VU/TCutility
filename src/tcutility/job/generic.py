import os
import stat
import subprocess as sp
from typing import List, Union
import numpy as np

import dictfunc
from scm import plams

from tcutility import log, molecule, results, slurm, connect, cache
from tcutility.environment import OSName, get_os_name
from tcutility.errors import TCJobError

j = os.path.join

@cache.cache
def _python_path(server: connect.Server = connect.Local()):
    """
    Sometimes it is necessary to have the Python path as some environments don't have its path.
    This function attempts to find the Python path and returns it.
    """
    python = server.execute("which python")
    if python == "" or not server.path_exists(python):
        python = server.execute("which python3")

    # we default to the python executable
    if python == "" or not server.path_exists(python):
        python = "python"

    return python


class Job:
    """This is the base Job class used to build more advanced classes such as :class:`AMSJob <tcutility.job.ams.AMSJob>` and :class:`ORCAJob <tcutility.job.orca.ORCAJob>`.
    The base class contains an empty :class:`Result <tcutility.results.result.Result>` object that holds the settings.
    It also provides :meth:`__enter__` and :meth:`__exit__` methods to make use of context manager syntax.

    All class methods are in principle safe to overwrite, but the :meth:`_setup_job` method **must** be overwritten.

    Args:
        test_mode: whether to enable the testing mode. If enabled, the job will be setup like normally, but the running step is skipped. This is useful if you want to know what the job settings look like before running the real calculations.
        overwrite: whether to overwrite a previously run job in the same working directory.
        wait_for_finish: whether to wait for this job to finish running before continuing your runscript.
        delete_on_finish: whether to remove the workdir for this job after it is finished running.
    """
    def __init__(
        self, *base_jobs: List["Job"], test_mode: bool = None, overwrite: bool = None, wait_for_finish: bool = None, delete_on_finish: bool = None, delete_on_fail: bool = None, use_slurm: bool = True
    ):
        self._sbatch = results.Result()
        self._molecule = None
        self._molecule_path = None
        self.slurm_job_id = None
        self.name = "calc"
        self.rundir = "tmp"
        self._preambles = []
        self._postambles = []
        self._postscripts = []
        self._servers = [connect.Local()]
        self._server_weights = [1]
        self._selected_server = None

        self.test_mode = test_mode
        self.overwrite = overwrite
        self.wait_for_finish = wait_for_finish
        self.delete_on_finish = delete_on_finish
        self.delete_on_fail = delete_on_fail
        self.use_slurm = use_slurm if use_slurm is not None else True

        # update this job with base_jobs
        for base_job in base_jobs:
            self.__dict__.update(base_job.copy().__dict__)

        self.test_mode = self.test_mode if test_mode is None else test_mode
        self.overwrite = self.overwrite if overwrite is None else overwrite
        self.wait_for_finish = self.wait_for_finish if wait_for_finish is None else wait_for_finish
        self.delete_on_finish = self.delete_on_finish if delete_on_finish is None else delete_on_finish
        self.delete_on_fail = delete_on_fail if delete_on_fail is None else delete_on_fail
        self.use_slurm = self.use_slurm if use_slurm is None else use_slurm

        # self.server = connect.get_current_server()
        # if self.server != connect.Local:
        #     self.sbatch(**self.server.sbatch_defaults)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type:
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            log.error(f'Job set-up failed with exception: {exc_type.__name__}({exc_value}) in File "{fname}", line {exc_tb.tb_lineno}.')
            return True
        self.run()

    def _select_server(self) -> connect.Server:
        """
        Select a server to run on based on the currently selected servers and their weights, 
        this will only choose a server once.
        """
        if self._selected_server is None:
            p = np.array(self._server_weights) / sum(self._server_weights)
            self._selected_server = np.random.choice(self._servers, p=p)
            for k, v in self._selected_server.sbatch_defaults.items():
                self._sbatch.setdefault(k, v)
        return self._selected_server

    def can_skip(self):
        """
        Check whether the job can be skipped. We check this by loading the calculation and checking if the job status was fatal.
        Fatal in this case means that the job failed, canceled or could not be found. In those cases we want to run the job.

        .. note::
            This method works for the :class:`ADFJob <tcutility.job.adf.ADFJob>`, :class:`ADFFragmentJob <tcutility.job.adf.ADFFragmentJob>`,
            :class:`DFTBJob <tcutility.job.dftb.DFTBJob>` and :class:`ORCAJob <tcutility.job.orca.ORCAJob>` objects, but not
            yet for :class:`CRESTJob <tcutility.job.crest.CRESTJob>` and :class:`QCGJob <tcutility.job.crest.QCGJob>`. For the latter objects the job will always be rerun.
            This will be fixed in a later version of TCutility.
        """
        for server in self._servers:
            if isinstance(server, connect.Local):
                res = results.quick_status(self.workdir)
                if not res.fatal:
                    return True

            res = server.execute(f'tcutility read -s {j(server.pwd(), self.rundir, self.name)}')
            if res in ['SUCCESS', 'SUCCESS(W)', 'COMPLETING', 'CONFIGURING', 'PENDING', 'RUNNING']:
                return True

        return False

    def in_queue(self):
        """
        Check whether the job is currently managed by slurm.
        We check this by loading the calculation and checking if the job status is 'RUNNING', 'COMPLETING', 'CONFIGURING' or 'PENDING'.
        """
        res = results.quick_status(self.workdir)
        return res.status.name in ["RUNNING", "COMPLETING", "CONFIGURING", "PENDING"]

    def __repr__(self):
        return f"{type(self)}(name={self.name}, rundir={self.rundir})"

    def sbatch(self, **kwargs):
        """
        Change slurm settings, for example, to change the partition or change the number of cores to use.
        The arguments are the same as you would use for sbatch (`see sbatch manual <https://slurm.schedmd.com/sbatch.html>`_). E.g. to change the partition to 'tc' call:

        ``job.sbatch(p='tc')`` or ``job.sbatch(partition='tc')``.

        Flags can be set as arguments with a boolean to enable or disable them:

        ``job.sbatch(exclusive=True)`` will set the ``--exclusive`` flag.

        .. warning::

            Note that some sbatch options, such as ``--job-name`` contain a dash, which cannot be used in Python arguments.
            To use these options you should use an underscore, like ``job.sbatch(job_name='water_dimer_GO')``.

        .. note::

            When running the job using sbatch we add a few extra default options:

            * ``-D/--chdir {self.workdir}``                to make sure the job starts in the correct directory
            * ``-J/--job-name {self.rundir}/{self.name}``  to give a nicer job-name when calling squeue
            * ``-o/--output {self.name}.out``              to redirect the output from the default slurm-{id}.out

            You can still overwrite them if you wish.
        """
        for key, value in kwargs.items():
            if key == "dependency" and "dependency" in self._sbatch:
                value = self._sbatch["dependency"] + "," + value
            self._sbatch[key] = value

    def _setup_job(self):
        """
        Set up the current job. This method should create the working directory, runscript and input file.
        Method must return True if it was successful.
        """
        raise NotImplementedError("You must implement the _setup_job method in your subclass.")

    def run(self):
        """
        Run this job. We detect if we are using slurm. If we are we submit this job using sbatch. Otherwise, we will run the job locally.
        """
        # print(results.quick_status(self.workdir))
        # print(self._servers)
        print(f'workdir: {self.workdir}, rundir: {self.rundir}')
        print(self.can_skip())
        for server in self._servers:
            print(server.execute(f'tcutility read -s {self.workdir}'))
        if self.can_skip():
            log.info(f"Skipping calculation {j(self.rundir, self.name)}, it is already finished or currently pending or running.")
            return

        server = self._select_server()
        if self.overwrite:
            server.rmtree(self.workdir)
            server.mkdir(self.workdir)

        # write the post-script calls to the post-ambles:
        if self.delete_on_finish:
            self.add_postamble(f"rm -r {self.workdir}")

        if self.delete_on_fail:
            self.add_postamble("# this will delete the calculation if it failed")
            self.add_postamble(f"if [[ `tcutility read -s {self.workdir}` = FAILED || `tcutility read -s {self.workdir}` = UNKNOWN ]]; then rm -r {self.workdir}; fi;")

        for postscript in self._postscripts:
            self._postambles.append(f'{_python_path(server)} {postscript[0]} {" ".join(postscript[1])}')

        # setup the job and check if it was successfull
        setup_success = self._setup_job()

        if self.test_mode or not setup_success:
            return

        if slurm.has_slurm(server) and self.use_slurm:
            # set some default sbatch settings
            if any(option not in self._sbatch for option in ["D", "chdir"]):
                self._sbatch.setdefault("D", self.workdir)
            if any(option not in self._sbatch for option in ["J", "job_name"]):
                self._sbatch.setdefault("J", f"{self.rundir}/{self.name}")
            if any(option not in self._sbatch for option in ["o", "output"]):
                self._sbatch.setdefault("o", f"{self.name}.out")
            self._sbatch.prune()

            # submit the job with sbatch
            sbatch_result = slurm.sbatch(os.path.split(self.runfile_path)[1], server=server, **self._sbatch)

            # store the slurm job ID
            self.slurm_job_id = sbatch_result.id
            # and write the command to a file so we can rerun it later
            with server.open_file(j(self.workdir, "submit.sh")) as cmd_file:
                cmd_file.write(sbatch_result.command)
            # make the submit command executable
            server.chmod(744, j(self.workdir, "submit.sh"))

            # if we requested the job to hold we will wait for the slurm job to finish
            if self.wait_for_finish:
                slurm.wait_for_job(self.slurm_job_id, server=server)
        else:
            os_name = get_os_name()

            if os_name == OSName.WINDOWS:
                raise TCJobError("Generic Job", "Running jobs on Windows is not supported.")

            # if we are not using slurm, we can execute the file. For this we need special permissions, so we have to set that first.
            os.chmod(self.runfile_path, os.stat(self.runfile_path).st_mode | stat.S_IEXEC)

            runfile_dir, runscript = os.path.split(self.runfile_path)
            command = ["./" + runscript] if os.name == "posix" else ["sh", runscript]
            print(f"Running command: {command} in directory: {runfile_dir}")

            with open(f"{os.path.split(self.runfile_path)[0]}/{self.name}.out", "w+") as out:
                sp.run(command, cwd=runfile_dir, stdout=out, shell=True)

    def add_preamble(self, line: str):
        """
        Add a preamble for the runscript. This should come after the shebang, but before the calculation is ran by the program (ADF or ORCA).
        This can used, for example, to load some modules. E.g. to load a specific version of AMS we can call:
        job.add_preamble('module load ams/2023.101')
        """
        self._preambles.append(line)

    def add_postamble(self, line: str):
        """
        Add a postamble for the runscript. This should come after the calculation is ran by the program (ADF or ORCA).
        This can be used, for example, to remove or copy some files. E.g. to remove all t12.* files we can call:
        job.add_postamble('rm t12.*')
        """
        self._postambles.append(line)

    def add_postscript(self, script, *args):
        """
        Add a post-script to this calculation.
        This should be either a Python module with a __file__ attribute or the path to a Python script.
        The post-script will be called with Python and any given args will be added as arguments when calling the script.

        Args:
            script: a Python object with a __file__ attribute or the file-path to a script.
            *args: positional arguments to pass to the post-script.
        """
        if not isinstance(script, str):
            script = script.__file__
        self._postscripts.append((script, args))

    def dependency(self, otherjob: "Job"):
        """
        Set a dependency between this job and otherjob.
        This means that this job will run after the other job is finished running succesfully.
        """
        if otherjob.can_skip() and not otherjob.in_queue():
            return

        if hasattr(otherjob, "slurm_job_id"):
            self.sbatch(dependency=f"afterany:{otherjob.slurm_job_id}")
            self.sbatch(kill_on_invalid_dep="Yes")

    @property
    def workdir(self):
        """
        The working directory of this job. All important files are written here, for example the input file and runscript.
        """
        return j(self._select_server().pwd(), self.rundir, self.name)

    @property
    def runfile_path(self):
        """
        The file path to the runscript of this job.
        """
        return j(self.workdir, f"{self.name}.run")

    @property
    def inputfile_path(self):
        """
        The file path to the input file of this job.
        """
        return j(self.workdir, f"{self.name}.in")

    @property
    def output_mol_path(self):
        """
        This method should return the name of the output molecule if it makes sense to give it back.
        E.g. for ADF it will be output.xyz in the workdir for optimization jobs.
        """
        raise NotImplementedError("You must implement the _setup_job method in your subclass.")

    def molecule(self, mol: Union[str, plams.Molecule, plams.Atom, List[plams.Atom]]):
        """
        Add a molecule to this calculation in various formats.
        If the molecule has a populated ``{mol}.flags.charge``, ``{mol}.flags.spin_polarization``
        or ``{mol}.flags.solvent`` object. This method will automatically try to apply them to this
        job.

        Args:
            mol: the molecule to read, can be a path (str). 
                If the path exists already we read it. If it does not exist yet, 
                it will be read in later. mol can also be a ``plams.Molecule`` object 
                or a single ``plams.Atom`` object or a list of ``plams.Atom`` objects.

        Examples:
            
            .. tabs::

                .. group-tab:: Job script

                    .. code-block::

                        import tcutility

                        with tcutility.jobs.ADFJob() as job:
                            job.molecule('example.xyz')
                            job.charge(1)
                            job.spin_polarization(-1)
                            job.solvent('water')

                .. group-tab:: example.xyz

                    .. code-block::

                        8

                        N       0.00000000       0.00000000      -0.81474153
                        B      -0.00000000      -0.00000000       0.83567034
                        H       0.47608351      -0.82460084      -1.14410295
                        H       0.47608351       0.82460084      -1.14410295
                        H      -0.95216703       0.00000000      -1.14410295
                        H      -0.58149793       1.00718395       1.13712667
                        H      -0.58149793      -1.00718395       1.13712667
                        H       1.16299585      -0.00000000       1.13712667

            This is equivalent to 

            .. tabs::

                .. group-tab:: Job script

                    .. code-block::

                        import tcutility

                        with tcutility.jobs.ADFJob() as job:
                            job.molecule('example2.xyz')


                .. group-tab:: example2.xyz

                    .. code-block::

                        8

                        N       0.00000000       0.00000000      -0.81474153
                        B      -0.00000000      -0.00000000       0.83567034
                        H       0.47608351      -0.82460084      -1.14410295
                        H       0.47608351       0.82460084      -1.14410295
                        H      -0.95216703       0.00000000      -1.14410295
                        H      -0.58149793       1.00718395       1.13712667
                        H      -0.58149793      -1.00718395       1.13712667
                        H       1.16299585      -0.00000000       1.13712667

                        charge = 1
                        spin_polarization = -1
                        solvent = water
        """
        if isinstance(mol, plams.Molecule):
            self._molecule = mol

        elif isinstance(mol, str) and os.path.exists(mol):
            self._molecule = molecule.load(mol)

        elif isinstance(mol, str):
            self._molecule_path = os.path.abspath(mol)

        elif isinstance(mol, list) and isinstance(mol[0], plams.Atom):
            self._molecule = plams.Molecule()
            [self._molecule.add_atom(atom) for atom in mol]

        elif isinstance(mol, plams.Atom):
            self._molecule = plams.Molecule()
            self._molecule.add_atom(mol)

        # check for settings in the molecule
        if isinstance(mol, plams.Molecule):
            if not hasattr(mol, 'flags'):
                return
            if mol.flags.charge:
                if callable(getattr(self, 'charge', None)):
                    self.charge(mol.flags.charge)
            if mol.flags.spin_polarization:
                if callable(getattr(self, 'spin_polarization', None)):
                    self.spin_polarization(mol.flags.charge)
            if mol.flags.solvent:
                if callable(getattr(self, 'solvent', None)):
                    self.charge(mol.flags.solvent)


    def copy(self):
        """
        Make and return a copy of this object.
        """
        import copy

        cp = Job()
        # cast this object to a list of keys and values
        lsts = dictfunc.dict_to_list(self.__dict__)
        # copy everthing in the lists
        lsts = [[copy.copy(x) for x in lst] for lst in lsts]
        # and return a new result object
        cp.__dict__.update(results.Result(dictfunc.list_to_dict(lsts)))
        return cp

    def add_server(self, server: connect.Server, weight: float = 1):
        """
        Add a server to connect to and run the calculation on.
        Job statuses will also be checked on the server.

        Args:
            server: the server to connect to.
            weight: how much weight is given to selecting this server.
        """
        if any(isinstance(server, connect.Local) for server in self._servers):
            self._servers = []
            self._server_weights = []

        self._servers.append(server)
        self._server_weights.append(weight)
