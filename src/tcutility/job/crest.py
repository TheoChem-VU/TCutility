from scm import plams
from tcutility.data import molecules
from tcutility.job.generic import Job
from tcutility import log
import os


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

    def _setup_job(self):
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

        options = [
            'coords.xyz',
            f'-xnam "{self.xtb_path}"',
            '--noreftopo',
            f'-c {self._charge}',
            f'-u {self._spinpol}',
            f'-tnmd {self._temp}',
            f'-mdlen {self._mdlen}',
        ]

        options = ' '.join(options)

        with open(self.runfile_path, 'w+') as runf:
            runf.write('#!/bin/sh\n\n')  # the shebang is not written by default by ADF
            runf.write('\n'.join(self._preambles) + '\n\n')
            runf.write(f'{self.crest_path} {options}\n')
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
        
        1) singlet
        2) doublet
        3) triplet
        4) ...

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

    def get_conformer_xyz(self, number: int = None):
        '''
        Return paths to conformer xyz files for this job.

        Args:
            number: the number of files to return, defaults to 10. If the directory already exists, for example if the job was already run, we will return up to `number` files.
        '''
        if os.path.exists(self.conformer_directory):
            return [j(self.conformer_directory, file) for i, file in enumerate(sorted(os.listdir(self.conformer_directory)))]

        for i in range(number or 10):
            yield j(self.conformer_directory, f'{str(i).zfill(5)}.xyz')

    def get_rotamer_xyz(self, number: int = None):
        '''
        Return paths to rotamer xyz files for this job.

        Args:
            number: the number of files to return, defaults to 10. If the directory already exists, for example if the job was already run, we will return up to `number` files.
        '''
        if os.path.exists(self.rotamer_directory):
            return [j(self.rotamer_directory, file) for i, file in enumerate(os.listdir(self.rotamer_directory))]

        for i in range(number or 10):
            yield j(self.rotamer_directory, f'{str(i).zfill(5)}.xyz')


class QCGJob(CRESTJob):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crest_path = 'crest'
        self._nsolv = 10
        self._fix_solute = False
        self._ensemble_generation_mode = 'NCI-MTD'
        self._solvent = None
        self._nofix = True

    def solvent(self, mol, nsolv=None):
        if self._nsolv:
            self._nsolv = nsolv

        if isinstance(mol, plams.Molecule):
            self._solvent = mol

        elif isinstance(mol, str) and os.path.exists(mol):
            self._solvent = plams.Molecule(mol)

        elif isinstance(mol, str):
            # here we can get the molecule name using tcutility.data.molecules
            self._solvent = molecules.get(mol)
            # we can check if the alpb solvent name is defined in the xyz file
            alpb = self._solvent.flags.get('alpb', None)
            if alpb:
                self.alpb(alpb)

        elif isinstance(mol, list) and isinstance(mol[0], plams.Atom):
            self._solvent = plams.Molecule()
            [self._solvent.add_atom(atom) for atom in mol]

        elif isinstance(mol, plams.Atom):
            self._solvent = plams.Molecule()
            self._solvent.add_atom(mol)

    def nsolv(self, nsolv):
        self._nsolv = nsolv

    def alpb(self, solvent):
        self._alpb = solvent

    def ensemble_mode(self, mode):
        self._ensemble_generation_mode = mode

    def nofix(self, enable=True):
        self._nofix = enable

    def _setup_job(self):
        self.add_postamble('mkdir ensemble/ensemble')
        self.add_postamble(f'split -d -l {len(self._molecule.atoms) + len(self._solvent.atoms) * self._nsolv + 2} -a 5 ensemble/final_ensemble.xyz ensemble/ensemble')

        self.add_postamble('for file in ensemble/ensemble/*')
        self.add_postamble('do')
        self.add_postamble('    mv "$file" "$file.xyz"')
        self.add_postamble('done')

        if not self._solvent:
            log.error(f'Did not provide a solvent molecule for this job. Call the {self.__class__.__name__}.solvent method to add one.')

        os.makedirs(self.workdir, exist_ok=True)

        self._molecule.write(j(self.workdir, 'coords.xyz'))
        self._solvent.write(j(self.workdir, 'solvent.xyz'))

        ensemble_mode_option = {
            'NCI-MTD': '--ncimtd',
            'MD': '--md',
            'MTD': '--mtd',
        }.get(self._ensemble_generation_mode, self._ensemble_generation_mode)

        options = [
            'coords.xyz',
            f'-xnam "{self.xtb_path}"',
            '--qcg solvent.xyz',
            '--ensemble',
            f'--nsolv {self._nsolv}',
            f'--chrg {self._charge}',
            f'--uhf {self._spinpol}',
            f'--tnmd {self._temp}',
            f'--mdlen {50 * float(self._mdlen[1:])}',
            ensemble_mode_option,
        ]

        if self._alpb:
            options.append(f'--alpb {self._alpb}')

        if self._nofix:
            options.append('--nofix')

        options = ' '.join(options)

        with open(self.runfile_path, 'w+') as runf:
            runf.write('#!/bin/sh\n\n')
            runf.write('\n'.join(self._preambles) + '\n\n')
            runf.write(f'{self.crest_path} {options}\n')
            runf.write('\n'.join(self._postambles))

        return True

    @property
    def ensemble_directory(self):
        return j(self.workdir, 'ensemble', 'ensemble')

    def get_ensemble_xyz(self, number: int = None):
        '''
        Return paths to conformer xyz files for this job.

        Args:
            number: the number of files to return, defaults to 10. If the directory already exists, for example if the job was already run, we will return up to `number` files.
        '''
        if os.path.exists(self.ensemble_directory):
            return [j(self.ensemble_directory, file) for i, file in enumerate(sorted(os.listdir(self.ensemble_directory)))]

        for i in range(number or 10):
            yield j(self.ensemble_directory, f'{str(i).zfill(5)}.xyz')

    @property
    def best_ensemble_path(self):
        return j(self.workdir, 'ensemble', 'ensemble', 'crest_best.xyz')


if __name__ == '__main__':
    # with CRESTJob() as job:
    #     job.rundir = 'tmp/SN2'
    #     job.name = 'CREST'
    #     job.molecule('../../../test/fixtures/xyz/transitionstate_radical_addition.xyz')
    #     job.sbatch(p='tc', ntasks_per_node=32)

    with QCGJob(test_mode=True) as job:
        job.rundir = 'calculations/Ammonia'
        job.name = 'QCG'
        job.molecule('ammonia.xyz')
        job.solvent('water', 10)
        print(job._solvent)
        job.sbatch(p='tc', n=32)

    # for i in range(40):
    #     with CRESTJob(test_mode=False, overwrite=True) as job:
    #         job.rundir = 'tmp/SN2'
    #         job.name = 'CREST'
    #         job.molecule('../../../test/fixtures/xyz/transitionstate_radical_addition.xyz')
    #         job.sbatch(p='tc', ntasks_per_node=32)
