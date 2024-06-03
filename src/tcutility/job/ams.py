from scm import plams
import tcutility
from tcutility import log
from tcutility.job.generic import Job
import os
import numpy as np
from typing import List

j = os.path.join


class AMSJob(Job):
    '''
    This is the AMS base job which will serve as the parent class for ADFJob, DFTBJob and the future BANDJob.
    It holds all methods related to changing the settings at the AMS level. It also handles preparing the jobs, e.g. writing runfiles and inputs.
    '''
    def __str__(self):
        return f'{self._task}({self._functional}/{self._basis_set}), running in {os.path.join(os.path.abspath(self.rundir), self.name)}'

    def single_point(self):
        '''
        Set the task of the job to single point.
        '''
        self._task = 'SP'
        self.settings.input.ams.task = 'SinglePoint'

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
        Set the task of the job to geometry optimization. By default also calculates the normal modes after convergence.
        '''
        self._task = 'GO'
        self.settings.input.ams.task = 'GeometryOptimization'
        self.settings.input.ams.GeometryOptimization.InitialHessian.Type = 'CalculateWithFastEngine'
        self.vibrations(True)

    def IRC(self, direction: str = 'both', hess_file: str = None, step_size: float = 0.2, min_path_length: float = 0.1, max_points: int = 300):
        '''
        Set the task of the job to intrinsic reaction coordinate (IRC).

        Args:
            direction: the direction to take the first step into. By default it will be set to ``both``.
            hess_file: the path to a ``.rkf`` file to read the Hessian from. This is the ``adf.rkf`` file for ADF calculations. 
                If set to ``None`` the Hessian will be calculated prior to starting the IRC calculation.
            step_size: the size of the step taken between each constrained optimization. By default it will be set to ``0.2`` :math:`a_0\\sqrt{Da}`.
            min_path_length: the length of the IRC path before switching to minimization. By default it will be set to ``0.1`` |angstrom|.
            max_points: the maximum number of IRC points in a direction. Be default it is set to ``300``.
        '''
        self._task = 'IRC'
        self.settings.input.ams.task = 'IRC'
        self.settings.input.ams.IRC.Direction = direction
        if hess_file:
            self.settings.input.ams.IRC.InitialHessian.File = hess_file
            self.settings.input.ams.IRC.InitialHessian.Type = 'FromFile'
        self.settings.input.ams.IRC.Step = step_size
        self.settings.input.ams.IRC.MinPathLength = min_path_length
        self.settings.input.ams.IRC.MaxPoints = max_points

        self.add_postscript(tcutility.job.postscripts.clean_workdir)
        self.add_postscript(tcutility.job.postscripts.write_converged_geoms)

    def PESScan(self, distances: list = None, angles: list = None, dihedrals: list = None, sumdists: list = None, difdists: list = None, npoints: int = 10):
        '''
        Set the task of the job to potential energy surface scan (PESScan).

        Args:
            distances: sequence of tuples or lists containing ``[atom_index1, atom_index2, start, end]``. 
                Atom indices start at 1. Distances are given in |angstrom|.
            angles: sequence of tuples or lists containing ``[atom_index1, atom_index2, atom_index3, start, end]``. 
                Atom indices start at 1. Angles are given in degrees
            dihedrals: sequence of tuples or lists containing ``[atom_index1, atom_index2, atom_index3, atom_index4, start, end]``. 
                Atom indices start at 1. Angles are given in degrees
            sumdists: sequence of tuples or lists containing ``[atom_index1, atom_index2, atom_index3, atom_index4, start, end]``. 
                Atom indices start at 1. Sum of distances is given in |angstrom|.
            difdists: sequence of tuples or lists containing ``[atom_index1, atom_index2, atom_index3, atom_index4, start, end]``. 
                Atom indices start at 1. Difference of distances is given in |angstrom|.
            npoints: the number of PES points to optimize.

        .. note::
            Currently we only support generating settings for 1-dimensional PESScans. 
            We will add support for N-dimensional PESScans later.
        '''
        self._task = 'PESScan'
        self.settings.input.ams.task = 'PESScan'
        self.settings.input.ams.PESScan.ScanCoordinate.nPoints = npoints
        if distances is not None:
            self.settings.input.ams.PESScan.ScanCoordinate.Distance = [" ".join([str(x) for x in dist]) for dist in distances]
        if angles is not None:
            self.settings.input.ams.PESScan.ScanCoordinate.Angle = [" ".join([str(x) for x in ang]) for ang in angles]
        if dihedrals is not None:
            self.settings.input.ams.PESScan.ScanCoordinate.Dihedral = [" ".join([str(x) for x in dihedral]) for dihedral in dihedrals]
        if sumdists is not None:
            self.settings.input.ams.PESScan.ScanCoordinate.SumDist = [" ".join([str(x) for x in dist]) for dist in sumdists]
        if difdists is not None:
            self.settings.input.ams.PESScan.ScanCoordinate.DifDist = [" ".join([str(x) for x in dist]) for dist in difdists]
            
        self.add_postscript(tcutility.job.postscripts.clean_workdir)
        self.add_postscript(tcutility.job.postscripts.write_converged_geoms)

    def vibrations(self, enable: bool = True, NegativeFrequenciesTolerance: float = -5):
        '''
        Set the calculation of vibrational modes. 

        Args:
            enable: whether to calculate the vibrational modes.
            NegativeFrequenciesTolerance: the tolerance for negative modes. 
                Modes with frequencies above this value will not be counted as imaginary. 
                Use this option when you experience a lot of numerical noise.
        '''
        self.settings.input.ams.Properties.NormalModes = 'Yes' if enable else 'No'
        self.settings.input.ams.Properties.PESPointCharacter = 'Yes'
        self.settings.input.ams.PESPointCharacter.NegativeFrequenciesTolerance = NegativeFrequenciesTolerance
        self.settings.input.ams.NormalModes.ReScanFreqRange = '-10000000.0 10.0'

    def geometry_convergence(self, gradients: float = 1e-5, energy: float = 1e-5, step: float = 1e-2, stress: float = 5e-4):
        '''
        Set the convergence criteria for the geometry optimization.

        Args:
            gradients: the convergence criteria for the gradients during geometry optimizations. Defaults to ``1e-5``.
            energy: the convergence criteria for the energy during geometry optimizations. Defaults to ``1e-5``.
            step: the convergence criteria for the step-size during geometry optimizations. Defaults to ``1e-2``.
            stress: the convergence criteria for the stress-energy per atom during geometry optimizations. Defaults to ``5e-4``
        '''
        self.settings.input.ams.GeometryOptimization.Convergence.Gradients = gradients
        self.settings.input.ams.GeometryOptimization.Convergence.Energy = energy
        self.settings.input.ams.GeometryOptimization.Convergence.Step = step
        self.settings.input.ams.GeometryOptimization.Convergence.StressEnergyPerAtom = stress

    def charge(self, val: int):
        '''
        Set the charge of the system.
        '''
        self.settings.input.ams.System.Charge = val

    def electric_field(self, direction: List[float], magnitude: float = None):
        '''
        Set an electric field for this system.

        Args:
            direction: the vector with the direction and strength of the electric field.
            magnitude: if given, the direction will be normalized and magnitude will be used as the field strength.
        '''
        # if magnitude is given we normalize the direction vector and give it the correct length
        if magnitude is not None:
            direction = np.array(direction)/np.linalg.norm(direction) * magnitude

        ex, ey, ez = tuple(direction)
        self.settings.input.ams.System.ElectrostaticEmbedding.ElectricField = f'{ex} {ey} {ez}'

    def _setup_job(self):
        '''
        Set up the calculation. This will create the working directory and write the runscript and input file for ADF to use.
        '''
        os.makedirs(self.rundir, exist_ok=True)

        # clean the workdir if it contains files
        for file in os.listdir(self.workdir):
            p = os.path.join(self.workdir, file)
            if p.endswith('.rkf'):
                os.remove(p)
            if 'ams.kid' in p:
                os.remove(p)
            if p.startswith('t21.'):
                os.remove(p)
            if p.startswith('t12.'):
                os.remove(p)



        if not self._molecule and not self._molecule_path and 'atoms' not in self.settings.input.ams.system:
            log.error(f'You did not supply a molecule for this job. Call the {self.__class__.__name__}.molecule method to add one.')
            return

        if not self._molecule:
            self.settings.input.ams.system.GeometryFile = self._molecule_path

        # sometimes we have to check if a job is able to run or requires some special consideration
        # those types of checks should be defined in _check_job
        self._check_job()

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

        # in case we are rerunning a calculation we need to remove ams.log
        if os.path.exists(j(self.workdir, 'ams.log')):
            os.remove(j(self.workdir, 'ams.log'))

        return True

    def _check_job(self):
        ...

    @property
    def output_mol_path(self):
        '''
        The default file path for output molecules when running ADF calculations. It will not be created for singlepoint calculations.
        '''
        return j(self.workdir, 'output.xyz')
