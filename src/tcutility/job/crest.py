from scm import plams
from tcutility import log, results, formula, slurm
from tcutility.data import functionals
from tcutility.job.generic import Job
import subprocess as sp
import os
from typing import Union


j = os.path.join

class CRESTJob(Job):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crest_path = 'crest'
        self.xtb_path = 'xtb'
        self._charge = 0
        self._spinpol = 0
        self._temp = 400
        self._mdlen = 'x1'

    def setup_job(self):
        self.add_postamble('mkdir rotamers')
        self.add_postamble('mkdir conformers')
        self.add_postamble(f'split -d -l {len(self._molecule.atoms) + 2} -a 5 crest_conformers.xyz conformers/')
        self.add_postamble(f'split -d -l {len(self._molecule.atoms) + 2} -a 5 crest_rotamers.xyz rotamers/')

        self.add_postamble('for file in conformers/* rotamers/*')
        self.add_postamble('do')
        self.add_postamble('    mv "$file" "$file.xyz"')
        self.add_postamble('done')

        os.makedirs(self.workdir, exist_ok=True)

        self._molecule.write(j(self.workdir, 'coords.xyz'))

        with open(self.runfile_path, 'w+') as runf:
            runf.write('#!/bin/sh\n\n')  # the shebang is not written by default by ADF
            runf.write('\n'.join(self._preambles) + '\n\n')
            runf.write(f'{self.crest_path} coords.xyz -xnam "{self.xtb_path}" --noreftopo -rthr 1 -c {self._charge} -u {self._spinpol} -tnmd {self._temp} -mdlen {self._mdlen}\n')
            runf.write('\n'.join(self._postambles))

        return True

    def spin_polarization(self, val: int):
        '''
        Set the spin-polarization of the system.
        '''
        self._spinpol = val

    def multiplicity(self, val: int):
        '''
        Set the multiplicity of the system. If the value is not one the calculation will also be unrestricted.
        We use the following values:
            1: singlet
            2: doublet
            3: triplet
            ...
        The multiplicity is equal to 2*S+1 for spin-polarization of S.
        '''
        self._spinpol = (val - 1)//2

    def charge(self, val: int):
        '''
        Set the charge of the system.
        '''
        self._charge = val

    def md_temperature(self, val: float):
        '''
        Set the temperature of the molecular dynamics steps. Defaults to 400K.
        '''
        self._temp = val

    def md_length(self, val: float):
        '''
        Set the length of the molecular dynamics steps. The default length will be multiplied by this value, e.g. the default value is 1.
        '''
        self._mdlen = f'x{val}'

    @property
    def best_conformer_path(self):
        return j(self.workdir, 'crest_best.xyz')

    @property
    def conformer_directory(self):
        return j(self.workdir, 'conformers')

    @property
    def rotamer_directory(self):
        return j(self.workdir, 'rotamers')



if __name__ == '__main__':
    with CRESTJob(test_mode=False, overwrite=True) as job:
        job.rundir = 'tmp/SN2'
        job.name = 'CREST'
        job.molecule('../../../test/fixtures/xyz/transitionstate_radical_addition.xyz')
        job.sbatch(p='tc', ntasks_per_node=32)

    for i in range(4):
        with CRESTJob(test_mode=False, overwrite=True) as job:
            job.rundir = 'tmp/SN2'
            job.name = 'CREST'
            job.molecule('../../../test/fixtures/xyz/transitionstate_radical_addition.xyz')
            job.sbatch(p='tc', ntasks_per_node=32)