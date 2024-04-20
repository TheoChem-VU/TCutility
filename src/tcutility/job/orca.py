from tcutility import log, results, ensure_list, spell_check, slurm
from tcutility.job.generic import Job
import subprocess as sp
import os
from typing import List, Union
from scm import plams


j = os.path.join


class ORCAJob(Job):
    def __init__(self, use_tmpdir=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings.main = set()
        self._charge = 0
        self._multiplicity = 1
        self._ghosts = []
        self._method = None
        self.memory = None
        self.processes = None
        self.orca_path = None
        self.use_tmpdir = use_tmpdir

        self.single_point()

    def main(self, val: Union[str, List[str]]):
        '''
        Add main options for this ORCA calculation, they will be added to the input prepended with exclamation marks.

        Args:
            val: the main options to add. This can be a string or a list of strings with the main options.
        '''
        # we want to split a string such as 'CC-pVTZ Opt CCSD(T)' into loose parts and add them separately
        # this should always return a list
        if isinstance(val, str):
            val = val.split()
        # add each 
        [self.settings.main.add(key) for key in val]

    def remove_main(self, val: Union[str, List[str]]):
        if isinstance(val, str):
            val = val.split()

        lower_main = {key.casefold(): key for key in self.settings.main}
        for v in val:
            if v.casefold() in lower_main:
                self.settings.main.discard(lower_main[v.casefold()])

    def __remove_task(self):
        [self.remove_main(task) for task in ['sp', 'opt', 'tsopt', 'neb-ts']]

    def method(self, method):
        spell_check.check(method, ['MP2', 'CCSD', 'CCSD(T)', 'CCSDT'])
        self.settings.main.append(method)
        self._method = method

    def reference(self, ref):
        spell_check.check(ref, ['UHF', 'UKS', 'RHF', 'RKS', 'ROHF', 'ROKS'])
        self.settings.main.append(ref)
        self._method = ref

    def QRO(self, enable=True):
        self.settings.MDCI.UseQROs = enable

    def basis_set(self, value):
        self.settings.main.append(value)

    def single_point(self):
        self.__remove_task()
        self.settings.main.add('SP')

    def transition_state(self):
        self.__remove_task()
        self.vibrations()
        self.settings.main.add('OptTS')

    def optimization(self):
        self.__remove_task()
        self.vibrations()
        self.settings.main.add('Opt')

    def vibrations(self, enable=True, numerical=False):
        self.remove_main('NumFreq')
        self.remove_main('Freq')
        if not enable:
            return
        if numerical:
            self.settings.main.add('NumFreq')
        else:
            self.settings.main.add('Freq')

    def charge(self, val):
        self._charge = val

    def spin_polarization(self, val):
        self._multiplicity = val + 1

    def multiplicity(self, val):
        self._multiplicity = val

    def ghost_atoms(self, indices: Union[int, List[int]]):
        self._ghosts.extend(ensure_list(indices))

    def get_memory_usage(self):
        mem = self.memory or self._sbatch.mem or None

        ntasks = self.processes
        if ntasks is None:
            if self._sbatch.n:
                ntasks = self._sbatch.n
            if self._sbatch.ntasks:
                ntasks = self._sbatch.ntasks
            if self._sbatch.ntasks_per_node:
                ntasks = self._sbatch.ntasks_per_node * self._sbatch.get('N', 1) * self._sbatch.get('nodes', 1)

        return mem, ntasks

    def molecule(self, mol: Union[str, plams.Molecule, plams.Atom, list[plams.Atom]], natoms: int = None):
        '''
        Add a molecule to this calculation in various formats.

        Args:
            mol: the molecule to read, can be a path (str). If the path exists already we read it. If it does not exist yet, it will be read in later. mol can also be a plams.Molecule object or a single or a list of plams.Atom objects.
            natoms: If the molecule is supplied as a path you should also give the number of atoms.
        '''
        super().molecule(mol)
        self.natoms = natoms

    def get_input(self):
        # set the correct memory usage and processes
        mem, ntasks = self.get_memory_usage()
        if ntasks and mem:
            if self._molecule is not None:
                natoms = len(self._molecule) - len(self._ghosts)
            else:
                if not hasattr(self, 'natoms') or self.natoms is None:
                    raise ValueError('You set the molecule as a path and did not supply the number of atoms.')
                natoms = self.natoms

            ntasks = min(ntasks, (natoms - 1) * 3)
            self.settings.PAL.nprocs = ntasks
            self.settings.maxcore = int(mem / ntasks * 0.75)
        else:
            log.warn('MaxCore and nprocs not specified. Please use SBATCH settings or set job.processes and job.memory.')

        ret = ''
        for key in self.settings.main:
            ret += f'!{key}\n'
        ret += '\n'

        for option, block in self.settings.items():
            if option == 'main':
                continue

            if isinstance(block, results.Result):
                ret += f'%{option}\n'

                for key, val in block.items():
                    ret += f'    {key} {val}\n'

                ret += 'END\n\n'
            else:
                ret += f'%{option} {block}\n'

        ret += '\n'

        if self._molecule_path:
            ret += f'* xyzfile {self._charge} {self._multiplicity} {os.path.abspath(self._molecule_path)}\n'

        else:
            ret += f'* xyz {self._charge} {self._multiplicity}\n'
            for i, atom in enumerate(self._molecule, start=1):
                if i in self._ghosts:
                    ret += f'    {atom.symbol:2}: {atom.x: >13f} {atom.y: >13f} {atom.z: >13f}\n'
                else:
                    ret += f'    {atom.symbol:3} {atom.x: >13f} {atom.y: >13f} {atom.z: >13f}\n'
            ret += '*\n'

        return ret

    def _setup_job(self):
        try:
            if self.orca_path is None and not self.test_mode:
                self.orca_path = sp.check_output(['which', 'orca']).decode().strip()
        except sp.CalledProcessError:
            log.warn(f'Could not find the orca path. Set the {self.__class__.__name__}.orca_path attribute to add it. Now setting it to "$(which orca)", make sure the orca executable is findable.')
            self.orca_path = '$(which orca)'

        if not self._molecule and not self._molecule_path:
            log.error(f'You did not supply a molecule for this job. Call the {self.__class__.__name__}.molecule method to add one.')
            return

        os.makedirs(self.workdir, exist_ok=True)
        with open(self.inputfile_path, 'w+') as inp:
            inp.write(self.get_input())

        with open(self.runfile_path, 'w+') as runf:
            runf.write('#!/bin/sh\n\n')
            runf.write('\n'.join(self._preambles) + '\n\n')
            
            # when using temporary directories for SLURM we need to do some extra setup
            # this is mainly moving the calculation directory to the TMPDIR location
            # and after the jobs is finished we copy back the results and remove the TMPDIR
            if self.use_tmpdir and slurm.has_slurm():
                runf.write('export TMPDIR="$TMPDIR/$SLURM_JOB_ID"\n')
                runf.write('mkdir -p $TMPDIR\n')
                runf.write('cd $TMPDIR\n')
                runf.write(f'cp {self.inputfile_path} $TMPDIR\n')

                runf.write(f'{self.orca_path} $TMPDIR/{self.name}.in\n')

                runf.write(f'cp $TMPDIR/* {self.workdir}\n')
                runf.write('rm -rf $TMPDIR\n')
                
            else:
                runf.write(f'{self.orca_path} {self.inputfile_path}.in\n')

            runf.write('\n'.join(self._postambles))

        return True

    @property
    def output_mol_path(self):
        '''
        The default file path for output molecules when running ADF calculations. It will not be created for singlepoint calculations.
        '''
        return j(self.workdir, 'OPT.xyz')




if __name__ == '__main__':
    job = ORCAJob()
    job.main('OPT cc-pVTZ')
    job.remove_main('OPT OPTTS NEB')
