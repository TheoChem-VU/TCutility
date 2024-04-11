from tcutility import log, results, slurm, molecule
import subprocess as sp
import os
import stat
from typing import Union
from scm import plams
import shutil

j = os.path.join


def _python_path():
    '''
    Sometimes it is necessary to have the Python path as some environments don't have its path.
    This function attempts to find the Python path and returns it.
    '''
    python = sp.run('which python', shell=True, capture_output=True).stdout.decode().strip()

    if python == '' or not os.path.exists(python):
        python = sp.run('which python3', shell=True, capture_output=True).stdout.decode().strip()

    # we default to the python executable 
    if python == '' or not os.path.exists(python):
        python = 'python'

    return python

class Job:
    '''This is the base Job class used to build more advanced classes such as :class:`AMSJob <tcutility.job.ams.AMSJob>` and :class:`ORCAJob <tcutility.job.orca.ORCAJob>`.
    The base class contains an empty :class:`Result <tcutility.results.result.Result>` object that holds the settings. 
    It also provides :meth:`__enter__` and :meth:`__exit__` methods to make use of context manager syntax.
    
    All class methods are in principle safe to overwrite, but the :meth:`_setup_job` method **must** be overwritten.

    Args:
        test_mode: whether to enable the testing mode. If enabled, the job will be setup like normally, but the running step is skipped. This is useful if you want to know what the job settings look like before running the real calculations.
        overwrite: whether to overwrite a previously run job in the same working directory.
        wait_for_finish: whether to wait for this job to finish running before continuing your runscript.
    '''
    def __init__(self, test_mode: bool = False, overwrite: bool = False, wait_for_finish: bool = False, delete_on_finish: bool = False):
        self.settings = results.Result()
        self._sbatch = results.Result()
        self._molecule = None
        self._molecule_path = None
        self.slurm_job_id = None
        self.name = 'calc'
        self.rundir = 'tmp'
        self.test_mode = test_mode
        self.overwrite = overwrite
        self.wait_for_finish = wait_for_finish
        self.delete_on_finish = delete_on_finish
        self._preambles = []
        self._postambles = []
        self._postscripts = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.run()

    def can_skip(self):
        '''
        Check whether the job can be skipped. We check this by loading the calculation and checking if the job status was fatal.
        Fatal in this case means that the job failed, canceled or could not be found. In those cases we want to run the job.

        .. note::
            This method works for the :class:`ADFJob <tcutility.job.adf.ADFJob>`, :class:`ADFFragmentJob <tcutility.job.adf.ADFFragmentJob>`, 
            :class:`DFTBJob <tcutility.job.dftb.DFTBJob>` and :class:`ORCAJob <tcutility.job.orca.ORCAJob>` objects, but not
            yet for :class:`CRESTJob <tcutility.job.crest.CRESTJob>` and :class:`QCGJob <tcutility.job.crest.QCGJob>`. For the latter objects the job will always be rerun. 
            This will be fixed in a later version of TCutility.
        '''
        res = results.read(self.workdir)
        return not res.status.fatal

    def __repr__(self):
        return f'{type(self)}(name={self.name}, rundir={self.rundir})'

    def sbatch(self, **kwargs):
        '''
        Change slurm settings, for example, to change the partition or change the number of cores to use.
        The arguments are the same as you would use for sbatch (`see sbatch manual <https://slurm.schedmd.com/sbatch.html>`_). E.g. to change the partition to 'tc' call:

        ``job.sbatch(p='tc')`` or ``job.sbatch(partition='tc')``

        .. warning::

            Note that some sbatch options, such as ``--job-name`` contain a dash, which cannot be used in Python arguments.
            To use these options you should use an underscore, like ``job.sbatch(job_name='water_dimer_GO')``.

        .. note::

            When running the job using sbatch we add a few extra default options:

            * ``-D/--chdir {self.workdir}``                to make sure the job starts in the correct directory
            * ``-J/--job-name {self.rundir}/{self.name}``  to give a nicer job-name when calling squeue
            * ``-o/--output {self.name}.out``              to redirect the output from the default slurm-{id}.out

            You can still overwrite them if you wish.
        '''
        for key, value in kwargs.items():
            if key == 'dependency' and 'dependency' in self._sbatch:
                value = self._sbatch['dependency'] + ',' + value
            self._sbatch[key] = value

    def _setup_job(self):
        '''
        Set up the current job. This method should create the working directory, runscript and input file.
        Method must return True if it was successful.
        '''
        NotImplemented

    def run(self):
        '''
        Run this job. We detect if we are using slurm. If we are we submit this job using sbatch. Otherwise, we will run the job locally.
        '''
        if self.overwrite:
            shutil.rmtree(self.workdir)
            os.makedirs(self.workdir, exist_ok=True)

        if self.can_skip():
            log.info(f'Skipping calculation {j(self.rundir, self.name)}, it is already finished or currently pending or running.')
            return

        # write the post-script calls to the post-ambles:
        if self.delete_on_finish:
            self.add_postamble(f'rm -r {self.workdir}')

        for postscript in self._postscripts:
            self._postambles.append(f'{_python_path()} {postscript[0]} {" ".join(postscript[1])}')

        # setup the job and check if it was successfull
        setup_success = self._setup_job()

        if self.test_mode or not setup_success:
            return

        if slurm.has_slurm():
            # set some default sbatch settings
            if any(option not in self._sbatch for option in ['D', 'chdir']):
                self._sbatch.setdefault('D', self.workdir)
            if any(option not in self._sbatch for option in ['J', 'job_name']):
                self._sbatch.setdefault('J', f'{self.rundir}/{self.name}')
            if any(option not in self._sbatch for option in ['o', 'output']):
                self._sbatch.setdefault('o', f'{self.name}.out')
            self._sbatch.prune()

            # submit the job with sbatch
            sbatch_result = slurm.sbatch(os.path.split(self.runfile_path)[1], **self._sbatch)

            # store the slurm job ID
            self.slurm_job_id = sbatch_result.id
            # and write the command to a file so we can rerun it later
            with open(j(self.workdir, 'submit.sh'), 'w+') as cmd_file:
                cmd_file.write(sbatch_result.command)
            # make the submit command executable
            os.chmod(j(self.workdir, 'submit.sh'), stat.S_IRWXU)

            # if we requested the job to hold we will wait for the slurm job to finish
            if self.wait_for_finish:
                slurm.wait_for_job(self.slurm_job_id)
        else:
            # if we are not using slurm, we can execute the file. For this we need special permissions, so we have to set that first.
            os.chmod(self.runfile_path, stat.S_IRWXU)
            with open(f'{os.path.split(self.runfile_path)[0]}/{self.name}.out', 'w+') as out:
                sp.run(self.runfile_path, cwd=os.path.split(self.runfile_path)[0], stdout=out)

    def add_preamble(self, line: str):
        '''
        Add a preamble for the runscript. This should come after the shebang, but before the calculation is ran by the program (ADF or ORCA).
        This can used, for example, to load some modules. E.g. to load a specific version of AMS we can call:
        job.add_preamble('module load ams/2023.101')
        '''
        self._preambles.append(line)

    def add_postamble(self, line: str):
        '''
        Add a postamble for the runscript. This should come after the calculation is ran by the program (ADF or ORCA).
        This can be used, for example, to remove or copy some files. E.g. to remove all t12.* files we can call:
        job.add_postamble('rm t12.*')
        '''
        self._postambles.append(line)

    def add_postscript(self, script, *args):
        '''
        Add a post-script to this calculation. 
        This should be either a Python module with a __file__ attribute or the path to a Python script.
        The post-script will be called with Python and any given args will be added as arguments when calling the script.

        Args:
            script: a Python object with a __file__ attribute or the file-path to a script.
            *args: positional arguments to pass to the post-script.
        '''
        if not isinstance(script, str):
            script = script.__file__
        self._postscripts.append((script, args))

    def dependency(self, otherjob: 'Job'):
        '''
        Set a dependency between this job and otherjob. 
        This means that this job will run after the other job is finished running succesfully.
        '''
        if hasattr(otherjob, 'slurm_job_id'):
            self.sbatch(dependency=f'afterok:{otherjob.slurm_job_id}')
            self.sbatch(kill_on_invalid_dep='Yes')

    @property
    def workdir(self):
        '''
        The working directory of this job. All important files are written here, for example the input file and runscript.
        '''
        return j(os.path.abspath(self.rundir), self.name)

    @property
    def runfile_path(self):
        '''
        The file path to the runscript of this job.
        '''
        return j(self.workdir, f'{self.name}.run')

    @property
    def inputfile_path(self):
        '''
        The file path to the input file of this job.
        '''
        return j(self.workdir, f'{self.name}.in')

    @property
    def output_mol_path(self):
        '''
        This method should return the name of the output molecule if it makes sense to give it back.
        E.g. for ADF it will be output.xyz in the workdir for optimization jobs.
        '''
        NotImplemented

    def molecule(self, mol: Union[str, plams.Molecule, plams.Atom, list[plams.Atom]]):
        '''
        Add a molecule to this calculation in various formats.

        Args:
            mol: the molecule to read, can be a path (str). If the path exists already we read it. If it does not exist yet, it will be read in later. mol can also be a plams.Molecule object or a single or a list of plams.Atom objects.
        '''
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
