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

    def get_conformer_xyz(self, number: int = 10):
        '''
        Return paths to conformer xyz files for this job.

        Args:
            number: the number of files to return, defaults to 10
        '''
        for i in range(number):
            yield j(self.workdir, 'conformers', f'{str(i).zfill(5)}.xyz')

    def get_rotamer_xyz(self, number: int = 10):
        '''
        Return paths to rotamer xyz files for this job.

        Args:
            number: the number of files to return, defaults to 10
        '''
        for i in range(number):
            yield j(self.workdir, 'rotamers', f'{str(i).zfill(5)}.xyz')



class QCGJob(CRESTJob):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crest_path = 'crest'
        self._nsolv = 10
        self._fix_solute = False
        self._ensemble_generation_mode = 'NCI-MTD'
        self._solvent = None

    def solvent(self, mol):
        if isinstance(mol, plams.Molecule):
            self._solvent = mol

        elif isinstance(mol, str) and os.path.exists(mol):
            self._solvent = plams.Molecule(mol)

        elif isinstance(mol, str):
            self._solvent_path = os.path.abspath(mol)

        elif isinstance(mol, list) and isinstance(mol[0], plams.Atom):
            self._solvent = plams.Molecule()
            [self._solvent.add_atom(atom) for atom in mol]

        elif isinstance(mol, plams.Atom):
            self._solvent = plams.Molecule()
            self._solvent.add_atom(mol)

    def ensemble_mode(self, mode):
        self._ensemble_generation_mode = mode

    def setup_job(self):
        os.makedirs(self.workdir, exist_ok=True)

        self._molecule.write(j(self.workdir, 'coords.xyz'))
        self._solvent.write(j(self.workdir, 'solvent.xyz'))

        ensemble_mode_option = '--' + {
            'NCI-MTD': 'ncimtd',
            'MD': 'md',
            'MTD': 'mtd',
        }.get(self._ensemble_generation_mode, self._ensemble_generation_mode)

        with open(self.runfile_path, 'w+') as runf:
            runf.write('#!/bin/sh\n\n')  # the shebang is not written by default by ADF
            runf.write('\n'.join(self._preambles) + '\n\n')
            runf.write(f'{self.crest_path} coords.xyz -xnam "{self.xtb_path}" -qcg solvent.xyz --nsolv {self._nsolv} --chrg {self._charge} --uhf {self._spinpol} --tnmd {self._temp} --mdlen {50 * float(self._mdlen[1:])} {ensemble_mode_option}\n')
            runf.write('\n'.join(self._postambles))

        return True


if __name__ == '__main__':
    # with CRESTJob() as job:
    #     job.rundir = 'tmp/SN2'
    #     job.name = 'CREST'
    #     job.molecule('../../../test/fixtures/xyz/transitionstate_radical_addition.xyz')
    #     job.sbatch(p='tc', ntasks_per_node=32)

    with QCGJob() as job:
        job.rundir = 'calculations/Ammonia'
        job.name = 'QCG'
        job.crest_path = 'crestlatest'
        job.molecule('ammonia.xyz')
        job.solvent('water.xyz')
        job.sbatch(p='tc', n=32)


    # for i in range(40):
    #     with CRESTJob(test_mode=False, overwrite=True) as job:
    #         job.rundir = 'tmp/SN2'
    #         job.name = 'CREST'
    #         job.molecule('../../../test/fixtures/xyz/transitionstate_radical_addition.xyz')
    #         job.sbatch(p='tc', ntasks_per_node=32)
