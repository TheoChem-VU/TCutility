from tcutility import log, results, slurm
import subprocess as sp
import os
import stat
from typing import Union

j = os.path.join


class Job:
    '''This is the base Job class used to build more advanced classes such as ADFJob and ORCAJob.
    The base class contains an empty DotDict object that holds the settings. It also provides __enter__ and __exit__ methods to make use of context manager syntax.'''
    def __init__(self, test_mode=False, overwrite=False):
        self.settings = results.Result()
        self._sbatch = results.Result()
        self._molecule = None
        self.slurm_job_id = None
        self.name = 'calc'
        self.rundir = 'tmp'
        self.test_mode = test_mode
        self.overwrite = overwrite
        self._preambles = []
        self._postambles = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.run()

    def can_skip(self):
        '''
        Check whether the job can be skipped. We check this by loading the calculation and checking if the job status was fatal.
        Fatal in this case means that the job failed, canceled or could not be found. In those cases we want to run the job.
        '''
        res = results.read(self.workdir)
        return not res.status.fatal

    def __repr__(self):
        return f'{type(self)}(name={self.name}, rundir={self.rundir})'

    def sbatch(self, **kwargs):
        '''
        Change slurm settings, for example, to change the partition or change the number of cores to use.
        The arguments are the same as you would use for sbatch. E.g. to change the partition to 'tc' call:
        job.sbatch(p='tc') or job.sbatch(partition='tc').
        '''
        for key, value in kwargs.items():
            if key == 'dependency' and 'dependency' in self._sbatch:
                value = self._sbatch['dependency'] + ',' + value
            self._sbatch[key] = value

    def get_sbatch_command(self):
        '''
        Create an sbatch command that can be used to run the job.
        Extra options that are added:
            -D {self.workdir}               to make sure the job starts in the correct directory
            -J {self.rundir}/{self.name}    to give a nicer job-name when calling squeue
            -o {self.name}.out              to redirect the output from the default slurm-{id}.out
        '''
        self._sbatch.prune()
        c = 'sbatch '
        for key, val in self._sbatch.items():
            key = key.replace('_', '-')
            if len(key) > 1:
                c += f'--{key}={val} '
            else:
                c += f'-{key} {val} '
        return c + f'-D {self.workdir} -J {self.rundir}/{self.name} -o {self.name}.out {os.path.split(self.runfile_path)[1]}'

    def setup_job(self):
        '''
        Set up the current job. This method should create the working directory, runscript and input file.
        '''
        NotImplemented

    def run(self):
        '''
        Run this job. We detect if we are using slurm. If we are we submit this job using sbatch. Otherwise, we will run the job locally.
        '''
        if self.can_skip() and not self.overwrite:
            log.info(f'Skipping calculation {j(self.rundir, self.name)}, it is already finished or currently pending or running.')
            return

        self.setup_job()

        if self.test_mode:
            return

        # we call the run command here and redirect all output to devnull so that the job runs silently without printing a bunch of stuff
        # errors should still be printed.
        with open(os.devnull, 'wb') as devnull:
            if slurm.has_slurm():
                cmd = self.get_sbatch_command()
                # we will write the sbatch command to a file so that we can resubmit the job later on
                with open(j(self.workdir, 'submit'), 'w+') as cmd_file:
                    cmd_file.write(cmd)
                sp.run(cmd.split(), stdout=devnull, stderr=sp.STDOUT)
                # set the slurm job id for this calculation, we use this in order to set dependencies between jobs.
                self.slurm_job_id = slurm.workdir_info(self.workdir).id
            else:
                # if we are not using slurm, we can execute the file. For this we need special permissions, so we have to set that first.
                os.chmod(self.runfile_path, stat.S_IRWXU)
                sp.run(self.runfile_path, cwd=os.path.split(self.runfile_path)[0], stdout=devnull, stderr=sp.STDOUT)

    def add_preamble(self, line):
        '''
        Add a preamble for the runscript. This should come after the shebang, but before the calculation is ran by the program (ADF or ORCA).
        This can used, for example, to load some modules. E.g. to load a specific version of AMS we can call:
        job.add_preamble('module load ams/2023.101')
        '''
        self._preambles.append(line)

    def add_postamble(self, line):
        '''
        Add a postamble for the runscript. This should come after the calculation is ran by the program (ADF or ORCA).
        This can be used, for example, to remove or copy some files. E.g. to remove all t12.* files we can call:
        job.add_postamble('rm t12.*')
        '''
        self._postambles.append(line)

    def dependency(self, otherjob: 'Job'):
        '''
        Set a dependency between this job and another job. This means that this job will run after the other job is finished running succesfully.
        '''
        if hasattr(otherjob, 'slurm_job_id'):
            self.sbatch(dependency=f'afterok:{otherjob.slurm_job_id}')

    @property
    def workdir(self):
        return j(os.path.abspath(self.rundir), self.name)

    @property
    def runfile_path(self):
        return j(self.workdir, f'{self.name}.run')

    @property
    def inputfile_path(self):
        return j(self.workdir, f'{self.name}.in')

    @property
    def output_mol_path(self):
        '''
        This method should return the name of the output molecule if it makes sense to give it back.
        E.g. for ADF it will be output.xyz in the workdir for optimization jobs.
        '''
        NotImplemented
