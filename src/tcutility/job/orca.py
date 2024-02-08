from tcutility import log, results, ensure_list, spell_check
from tcutility.job.generic import Job
import subprocess as sp
import os
from typing import List, Union


j = os.path.join


class ORCAJob(Job):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._charge = 0
        self._multiplicity = 1
        self._ghosts = []
        self._method = None
        self.memory = None
        self.processes = None
        self.orca_path = None
        self.main = set()
        self.single_point()

    def add_main(self, key: str):
        '''
        Add a keyword to the main input of the ORCA input.
        '''
        self.main.add(key)

    def __casefold_main(self):
        self.main = {key.casefold() for key in self.main}

    def __remove_task(self):
        self.__casefold_main()
        [self.main.discard(task) for task in ['sp', 'opt', 'tsopt', 'neb-ts']]

    def method(self, method):
        spell_check.check(method, ['MP2', 'CCSD', 'CCSD(T)', 'CCSDT'])
        self.main.append(method)
        self._method = method

    def reference(self, ref):
        spell_check.check(ref, ['UHF', 'UKS', 'RHF', 'RKS', 'ROHF', 'ROKS'])
        self.main.append(ref)
        self._reference = ref

    def QRO(self, enable=True):
        self.settings.MDCI.UseQROs = enable

    def basis_set(self, value):
        self.main.append(value)

    def single_point(self):
        self.__remove_task()
        self.main.add('sp')

    def transition_state(self):
        self.__remove_task()
        self.vibrations()
        self.main.add('optts')

    def optimization(self):
        self.__remove_task()
        self.vibrations()
        self.main.add('opt')

    def vibrations(self, enable=True, numerical=False):
        self.__casefold_main()
        self.main.discard('numfreq')
        self.main.discard('freq')
        if not enable:
            return
        if numerical:
            self.main.add('numfreq')
        else:
            self.main.add('freq')

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

    def get_input(self):
        # set the correct memory usage and processes
        mem, ntasks = self.get_memory_usage()
        if ntasks and mem:
            natoms = len(self._molecule)
            ntasks = min(ntasks, (natoms - 1) * 3)
            self.settings.PAL.nprocs = ntasks
            self.settings.maxcore = int(mem / ntasks * 0.75)
        else:
            log.warn('MaxCore and nprocs not specified. Please use SBATCH settings or set job.processes and job.memory.')

        ret = ''
        for key in self.main:
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
            ret += f'* xyz {self._charge} {self._multiplicity} {os.path.abspath(self._molecule_path)}\n'

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
            log.error('Could not find the orca path. Please set it manually.')
            return

        if not self._molecule and not self._molecule_path:
            log.error(f'You did not supply a molecule for this job. Call the {self.__class__}.molecule method to add one.')
            return

        os.makedirs(self.workdir, exist_ok=True)
        with open(self.inputfile_path, 'w+') as inp:
            inp.write(self.get_input())

        with open(self.runfile_path, 'w+') as runf:
            runf.write('#!/bin/sh\n\n')  # the shebang is not written by default by ADF
            runf.write('\n'.join(self._preambles) + '\n\n')
            runf.write(f'{self.orca_path} {self.inputfile_path}\n')
            runf.write('\n'.join(self._postambles))

        return True




if __name__ == '__main__':
    job = ORCAJob()
    job.molecule('water.xyz')
    job._setup_job()
