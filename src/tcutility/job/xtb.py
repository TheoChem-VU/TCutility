from tcutility.job.generic import Job
from tcutility import spell_check
import os
from typing import Union


j = os.path.join


class XTBJob(Job):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.xtb_path = 'xtb'
        self._options = ['coords.xyz']
        self._scan = {}

    def _setup_job(self):
        os.makedirs(self.workdir, exist_ok=True)

        self._molecule.write(j(self.workdir, 'coords.xyz'))

        if self._scan:
            with open(j(self.workdir, 'scan.inp'), 'w+') as scaninp:
                for key, value in self._scan.items():
                    scaninp.write(f'${key}\n')
                    for line in value:
                        scaninp.write(f'    {line}\n')
                scaninp.write('$end\n')

        options = ' '.join(self._options)
        with open(self.runfile_path, 'w+') as runf:
            runf.write('#!/bin/sh\n\n')  # the shebang is not written by default by ADF
            runf.write('\n'.join(self._preambles) + '\n\n')
            runf.write(f'{self.xtb_path} {options}\n')
            runf.write('\n'.join(self._postambles))

        return True

    def model(self, method: Union[str, int]):
        '''
        Set the method used by XTB. This includes GFN0-xTB, GFN1-xTB, GFN2-xTB and GFNFF.

        Args:
            method: the method to use. Can be specified by its full name, e.g. 'GFN2-xTB', is the same as 'GFN2' or simply 2.
        '''
        if isinstance(method, int):
            if not 0 >= method >= 2:
                raise ValueError(f'GFN{method}-xTB does not exist. Please choose one of GFN[0, 1, 2]-xTB.')
            self._options.append(f'--gfn {method}')
            return

        if method.lower() in ['gfn0', 'gfn0-xtb']:
            self._options.append('--gfn 0')
            return

        if method.lower() in ['gfn1', 'gfn1-xtb']:
            self._options.append('--gfn 1')
            return

        if method.lower() in ['gfn2', 'gfn2-xtb']:
            self._options.append('--gfn 2')
            return

        if method.lower() in ['gfnff', 'ff']:
            self._options.append('--gfnff')
            return

        raise ValueError(f'Did not recognize the method {method} for XTB.')
    
    def solvent(self, name: str = None, model: str = 'alpb'):
        '''
        Model solvation using the ALPB or GBSA model.

        Args:
            name: the name of the solvent you want to use. Must be ``None``, ``Acetone``, ``Acetonitrile``, ``CHCl3``, ``CS2``, ``DMSO``, ``Ether``, ``H2O``, ``Methanol``, ``THF`` or ``Toluene``.
            grid_size: the size of the grid used to construct the solvent accessible surface. Must be ``230``, ``974``, ``2030`` or ``5810``.
        '''
        spell_check.check(model, ['alpb', 'gbsa'], ignore_case=True)
        self._options.append(f'--{model} {name}')

    def spin_polarization(self, val: int):
        '''
        Set the spin-polarization of the system.
        '''
        self._options.append(f'-u {val}')

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
        self._options.append(f'-u {(val - 1)//2}')

    def charge(self, val: int):
        '''
        Set the charge of the system.
        '''
        self._options.append(f'-c {val}')

    def vibrations(self, enable: bool = True):
        self._options.append('--hess')

    def optimization(self, quality: str = 'Normal', calculate_hess: bool = True):
        '''
        Do a geometry optimization and calculate the normal modes of the input structure.
        
        Args:
            quality: the convergence criteria of the optimization. 
                See https://xtb-docs.readthedocs.io/en/latest/optimization.html#optimization-levels.
            calculate_hess: whether to calculate the Hessian and do a normal mode analysis after optimization.
        '''
        spell_check.check(quality, ['crude', 'sloppy', 'loose', 'lax', 'normal', 'tight', 'vtight', 'extreme'], ignore_case=True)

        if calculate_hess:
            self._options.append(f'--ohess {quality}')
        else:
            self._options.append(f'--opt {quality}')

    def PESScan(self, distances: list = [], angles: list = [], dihedrals: list = [], npoints: int = 20, quality: str = 'Normal', mode: str = 'concerted'):
        '''
        Set the task of the job to potential energy surface scan (PESScan).

        Args:
            distances: sequence of tuples or lists containing ``[atom_index1, atom_index2, start, end]``. 
                Atom indices start at 1. Distances are given in |angstrom|.
            angles: sequence of tuples or lists containing ``[atom_index1, atom_index2, atom_index3, start, end]``. 
                Atom indices start at 1. Angles are given in degrees
            dihedrals: sequence of tuples or lists containing ``[atom_index1, atom_index2, atom_index3, atom_index4, start, end]``. 
                Atom indices start at 1. Angles are given in degrees
            npoints: the number of PES points to optimize.

        .. note::
            Currently we only support generating settings for 1-dimensional PESScans. 
            We will add support for N-dimensional PESScans later.
        '''
        self.optimization(quality=quality, calculate_hess=False)
        self._options.append('--input scan.inp')

        self._scan.setdefault('scan', [f'mode={mode}'])
        # self._scan.setdefault('opt', [f'maxcycles=50'])
        for i, d in enumerate(distances):
            self._scan['scan'].append(f'distance: {d[0]},{d[1]},{d[2]}; {d[2]}, {d[3]}, {npoints}')
        for i, a in enumerate(angles, start=i):
            self._scan['scan'].append(f'angle: {a[0]},{a[1]},{a[2]},{a[3]}; {a[3]}, {a[4]}, {npoints}')
        for i, a in enumerate(dihedrals, start=i):
            self._scan['scan'].append(f'dihedral: {a[0]},{a[1]},{a[2]},{a[3]},{a[4]}; {a[4]}, {a[5]}, {npoints}')

    @property
    def output_mol_path(self):
        return f'{self.workdir}/xtbopt.xyz'

