from scm import plams
from tcutility import log
from tcutility.job.generic import Job
import os


j = os.path.join


class AMSJob(Job):
    '''
    This is the AMS base job which will serve as the parent class for ADFJob, DFTBJob and the future BANDJob.
    It holds all methods related to changing the settings at the AMS level. It also handles preparing the jobs, e.g. writing runfiles and inputs.
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.single_point()
        self.geometry_convergence(gradients=1e-5, energy=1e-5)

    def __str__(self):
        return f'{self._task}({self._functional}/{self._basis_set}), running in {os.path.join(os.path.abspath(self.rundir), self.name)}'

    def single_point(self):
        '''
        Set the task of the job to single point.
        '''
        self._task = 'SP'
        self.settings.input.ams.task = 'SinglePoint'

    def geometry_convergence(self, gradients: float = 1e-5, energy: float = 1e-5):
        '''
        Set the convergence criteria for the geometry optimization.

        Args:
            gradients: the convergence criteria for the gradients during geometry optimizations. Defaults to 1e-5.
            energy: the convergence criteria for the energy during geometry optimizations. Default to 1e-5.
        '''
        self.settings.input.ams.GeometryOptimization.Convergence.Gradients = gradients
        self.settings.input.ams.GeometryOptimization.Convergence.Energy = energy

    def transition_state(self, distances: list = None, angles: list = None, dihedrals: list = None, ModeToFollow: int = 1):
        '''
        Set the task of the job to transition state search. Optionally you can give some TS coordinates to accelerate convergence.
        By default also calculates the normal modes after convergence.

        Args:
            distances: sequence of tuples or lists containing [atom_index1, atom_index2, factor]. Atom indices start at 1. 
            angles: sequence of tuples or lists containing [atom_index1, atom_index2, atom_index3, factor]. Atom indices start at 1.
            dihedrals: sequence of tuples or lists containing [atom_index1, atom_index2, atom_index3, atom_index4, factor]. Atom indices start at 1.
            ModeToFollow: the vibrational mode to follow during optimization.
        '''
        self._task = 'TS'
        self.settings.input.ams.task = 'TransitionStateSearch'

        self.settings.input.ams.TransitionStateSearch.ModeToFollow = ModeToFollow

        if distances is not None:
            self.settings.input.ams.TransitionStateSearch.ReactionCoordinate.Distance = [" ".join([str(x) for x in dist]) for dist in distances]
        if angles is not None:
            self.settings.input.ams.TransitionStateSearch.ReactionCoordinate.Angle = [" ".join([str(x) for x in ang]) for ang in angles]
        if dihedrals is not None:
            self.settings.input.ams.TransitionStateSearch.ReactionCoordinate.Dihedral = [" ".join([str(x) for x in dihedral]) for dihedral in dihedrals]

        # for TS searches we quickly calculate the hessian with DFTB
        self.settings.input.ams.GeometryOptimization.InitialHessian.Type = 'CalculateWithFastEngine'
        self.vibrations(True)  # also calculate vibrations by default

    def optimization(self):
        '''
        Set the task of the job to transition state search. By default also calculates the normal modes after convergence.
        '''
        self._task = 'GO'
        self.settings.input.ams.task = 'GeometryOptimization'
        self.settings.input.ams.GeometryOptimization.InitialHessian.Type = 'CalculateWithFastEngine'
        self.vibrations(True)

    def vibrations(self, enable: bool = True, PESPointCharacter: bool = True, NegativeFrequenciesTolerance: float = -5, ReScanFreqRange: tuple[float ,float] = [-10000000.0, 10.0]):
        '''
        Set the calculation of vibrational modes. 

        Args:
            enable: whether to calculate the vibrational modes.
            PESPointCharacter: whether to report the PES character in the output.
            NegativeFrequenciesTolerance: the tolerance for negative modes. Modes above this value will not be counted as imaginary. Use this option when you experience a lot of numerical noise.
            ReScanFreqRange: the rescan range. Any mode that has a frequency in this range will be refined.
        '''
        self.settings.input.ams.Properties.NormalModes = 'Yes' if enable else 'No'
        self.settings.input.ams.Properties.PESPointCharacter = 'Yes' if enable else 'No'
        self.settings.input.ams.PESPointCharacter.NegativeFrequenciesTolerance = NegativeFrequenciesTolerance
        self.settings.input.ams.NormalModes.ReScanFreqRange = ' '.join([str(x) for x in ReScanFreqRange])

    def charge(self, val: int):
        '''
        Set the charge of the system.
        '''
        self.settings.input.ams.System.Charge = val

    def _setup_job(self):
        '''
        Set up the calculation. This will create the working directory and write the runscript and input file for ADF to use.
        '''
        os.makedirs(self.rundir, exist_ok=True)

        if not self._molecule and not self._molecule_path and 'atoms' not in self.settings.input.ams.system:
            log.error(f'You did not supply a molecule for this job. Call the {self.__class__.__name__}.molecule method to add one.')
            return

        if not self._molecule:
            self.settings.input.ams.system.GeometryFile = self._molecule_path

        # we will use plams to write the input and runscript
        sett = self.settings.as_plams_settings()
        job = plams.AMSJob(name=self.name, molecule=self._molecule, settings=sett)

        os.makedirs(self.workdir, exist_ok=True)
        with open(self.inputfile_path, 'w+') as inpf:
            inpf.write(job.get_input())

        with open(self.runfile_path, 'w+') as runf:
            runf.write('#!/bin/sh\n\n')  # the shebang is not written by default by ADF
            runf.write('\n'.join(self._preambles) + '\n\n')
            runf.write(job.get_runscript())
            runf.write('\n'.join(self._postambles))

        return True

    @property
    def output_mol_path(self):
        '''
        The default file path for output molecules when running ADF calculations. It will not be created for singlepoint calculations.
        '''
        return j(self.workdir, 'output.xyz')
