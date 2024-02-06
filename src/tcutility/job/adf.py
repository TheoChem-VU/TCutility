from scm import plams
from tcutility import log, results, formula, spell_check, data
from tcutility.job.ams import AMSJob
import os


j = os.path.join


class ADFJob(AMSJob):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._functional = None
        self.solvent('vacuum')
        self.basis_set('TZ2P')
        self.quality('Good')
        self.SCF_convergence(1e-8)
        self.single_point()

    def __str__(self):
        return f'{self._task}({self._functional}/{self._basis_set}), running in {os.path.join(os.path.abspath(self.rundir), self.name)}'

    def basis_set(self, typ: str = 'TZ2P', core: str = 'None'):
        '''
        Set the basis-set type and frozen core approximation for this calculation.

        Args:
            typ: the type of basis-set to use. Default is TZ2P.
            core: the size of the frozen core approximation. Default is None.

        Raises:
            ValueError: if the basis-set name or core is incorrect.

        .. note:: If the selected functional is the r2SCAN-3c functional, then the basis-set will be set to mTZ2P.

        .. seealso:: 
            :mod:`tcutility.data.basis_sets` for an overview of the available basis-sets in ADF.
        '''
        spell_check.check(typ, data.basis_sets.available_basis_sets['ADF'], ignore_case=True)
        spell_check.check(core, ['None', 'Small', 'Large'], ignore_case=True)
        if self._functional == 'r2SCAN-3c' and typ != 'mTZ2P':
            log.warn(f'Basis set {typ} is not allowed with r2SCAN-3c, switching to mTZ2P.')
            typ = 'mTZ2P'
        self._basis_set = typ
        self.settings.input.adf.basis.type = typ
        self.settings.input.adf.basis.core = core

    def spin_polarization(self, val: int):
        '''
        Set the spin-polarization of the system. If the value is not zero the calculation will also be unrestricted.
        '''
        self.settings.input.adf.SpinPolarization = val
        if val != 0:
            self.settings.input.adf.Unrestricted = 'Yes'

    def multiplicity(self, val: int):
        '''
        Set the multiplicity of the system. If the value is not one the calculation will also be unrestricted.
        We use the following values:
        
        1) singlet
        2) doublet
        3) triplet
        4) ...
    
        The multiplicity is equal to 2*S+1 for spin-polarization S.
        '''
        self.settings.input.adf.SpinPolarization = (val - 1)//2
        if val != 1:
            self.settings.input.adf.Unrestricted = 'Yes'

    def unrestricted(self, val: bool):
        '''
        Whether the calculation should be unrestricted.
        '''
        self.settings.input.adf.Unrestricted = 'Yes' if val else 'No'

    def quality(self, val: str = 'Good'):
        '''
        Set the numerical quality of the calculation.

        Args:
            val: the numerical quality value to set to. This is the same as the ones used in the ADF GUI. Defaults to Good.

        Raises:
            ValueError: if the quality value is incorrect.
        '''
        spell_check.check(val, ['Basic', 'Normal', 'Good', 'VeryGood', 'Excellent'], ignore_case=True)
        self.settings.input.adf.NumericalQuality = val

    def SCF_convergence(self, thresh: float = 1e-8):
        '''
        Set the SCF convergence criteria for the job.

        Args:
            thresh: the convergence criteria for the SCF procedure. Defaults to 1e-8.

        .. deprecated:: 0.9.2
            Please use :meth:`ADFJob.SCF` instead of this method.
        '''
        log.warn('This method has been deprecated, please use ADFJob.SCF instead.')
        self.SCF(thresh=thresh)

    def SCF(self, iterations: int = 300, thresh: float = 1e-8):
        '''
        Set the SCF settings for this calculations.

        Args:
            iterations: number of iterations to perform for this calculation. Defaults to 300.
            thresh: the convergence criteria for the SCF procedure. Defaults to 1e-8.
        '''
        self.settings.input.adf.SCF.Iterations = iterations
        self.settings.input.adf.SCF.Converge = thresh

    def functional(self, funtional_name: str, dispersion: str = None):
        '''
        Set the functional to be used by the calculation. This also sets the dispersion if it is specified in the functional name.

        Args:
            funtional_name: the name of the functional. The value can be the same as the ones used in the ADF GUI.
            dispersion: dispersion setting to use with the functional. This is used when you want to use a functional from LibXC.

        Raises:
            ValueError: if the functional name is not recognized.

        .. note:: Setting the functional to r2SCAN-3c will automatically set the basis-set to mTZ2P.

        .. seealso::
            :mod:`tcutility.data.functionals` for an overview of the available functionals in ADF.
        '''
        # before adding the new functional we should clear any previous functional settings
        self.settings.input.adf.pop('XC', None)

        functional = funtional_name.strip()
        functional = functional.replace('-D4(EEQ)', '-D4')  # D4(EEQ) and D4 are the same, unlike D3 and D3(BJ)
        self._functional = functional

        if functional == 'r2SCAN-3c' and self._basis_set != 'mTZ2P':
            log.warn(f'Switching basis set from {self._basis_set} to mTZ2P for r2SCAN-3c.')
            self.basis_set('mTZ2P')

        if functional == 'SSB-D':
            log.error('There are two functionals called SSB-D, please use "GGA:SSB-D" or "MetaGGA:SSB-D".')
            return

        if not data.functionals.get(functional):
            log.warn(f'XC-functional {functional} not found. Please ask a TheoCheM developer to add it. Adding functional as LibXC.')
            self.settings.input.adf.XC.LibXC = functional
        else:
            func = data.functionals.get(functional)
            self.settings.input.adf.update(func.adf_settings)

    def relativity(self, level: str = 'Scalar'):
        '''
        Set the treatment of relativistic effects for this calculation.

        Args:
            level: the level to set. Can be the same as the values in the ADF GUI and documentation. By default it is set to Scalar.

        Raises:
            ValueError: if the relativistic correction level is not correct.
        '''
        spell_check.check(level, ['Scalar', 'None', 'Spin-Orbit'], ignore_case=True)
        self.settings.input.adf.relativity.level = level

    def solvent(self, name: str = None, eps: float = None, rad: float = None, use_klamt: bool = False):
        '''
        Model solvation using COSMO for this calculation.

        Args:
            name: the name of the solvent you want to use. Please see the ADF manual for a list of available solvents.
            eps: the dielectric constant of your solvent. You can use this in place of the solvent name if you need more control over COSMO.
            rad: the radius of the solvent molecules. You can use this in place of the solvent name if you need more control over COSMO.
            use_klamt: whether to use the klamt atomic radii. This is usually used when you have charged species (?).

        Raises:
            ValueError: if the solvent name is given, but incorrect.

        .. seealso::
            :mod:`tcutility.data.cosmo` for an overview of the available solvent names and formulas.
        '''
        if name:
            spell_check.check(name, data.cosmo.available_solvents, ignore_case=True, insertion_cost=0.3)
            self._solvent = name
        else:
            self._solvent = f'COSMO(eps={eps} rad={rad})'

        if name == 'vacuum':
            self.settings.input.adf.pop('Solvation', None)
            return

        self.settings.input.adf.Solvation.Surf = 'Delley'
        solv_string = ''
        if name:
            solv_string += f'name={name} '
        else:
            self.settings.input.adf.Solvation.Solv = f'eps={eps} rad={rad} '
        if use_klamt:
            solv_string += 'cav0=0.0 cav1=0.0'
        else:
            solv_string += 'cav0=0.0 cav1=0.0067639'
        self.settings.input.adf.Solvation.Solv = solv_string

        self.settings.input.adf.Solvation.Charged = 'method=CONJ corr'
        self.settings.input.adf.Solvation['C-Mat'] = 'POT'
        self.settings.input.adf.Solvation.SCF = 'VAR ALL'
        self.settings.input.adf.Solvation.CSMRSP = None

        if use_klamt:
            radii = {
                'H': 1.30,
                'C': 2.00,
                'N': 1.83,
                'O': 1.72,
                'F': 1.72,
                'Si': 2.48,
                'P': 2.13,
                'S': 2.16,
                'Cl': 2.05,
                'Br': 2.16,
                'I': 2.32
            }
            self.settings.input.adf.solvation.radii = radii


class ADFFragmentJob(ADFJob):
    def __init__(self, *args, **kwargs):
        self.childjobs = {}
        super().__init__(*args, **kwargs)
        self.name = 'complex'

    def add_fragment(self, mol, name=None):
        # in case of giving fragments as indices we dont want to add the fragment to the molecule later
        add_frag_to_mol = True  
        # we can be given a list of atoms
        if isinstance(mol, list) and isinstance(mol[0], plams.Atom):
            mol_ = plams.Molecule()
            [mol_.add_atom(atom) for atom in mol]
            mol = mol_

        # or a list of integers
        if isinstance(mol, list) and isinstance(mol[0], int):
            if not self._molecule:
                log.error(f'Trying to add fragment based on atom indices, but main job does not have a molecule yet. Call the {self.__class__.__name__}.molecule method to add one.')
                return
            mol_ = plams.Molecule()
            [mol_.add_atom(self._molecule[i]) for i in mol]
            mol = mol_.copy()
            add_frag_to_mol = False

        name = name or f'fragment{len(self.childjobs) + 1}'
        self.childjobs[name] = ADFJob(test_mode=self.test_mode)
        self.childjobs[name].molecule(mol)
        setattr(self, name, self.childjobs[name])

        if not add_frag_to_mol:
            return

        if self._molecule is None:
            self._molecule = self.childjobs[name]._molecule.copy()
        else:
            self._molecule = self._molecule + self.childjobs[name]._molecule.copy()

    def run(self):
        mol_str = " + ".join([formula.molecule(child._molecule) for child in self.childjobs.values()])
        log.flow(f'ADFFragmentJob [{mol_str}]', ['start'])
        # obtain some system wide properties of the molecules
        charge = sum([child.settings.input.ams.System.charge or 0 for child in self.childjobs.values()])
        unrestricted = any([(child.settings.input.adf.Unrestricted or 'no').lower() == 'yes' for child in self.childjobs.values()])
        spinpol = sum([child.settings.input.adf.SpinPolarization or 0 for child in self.childjobs.values()])
        log.flow(f'Level:             {self._functional}/{self._basis_set}')
        log.flow(f'Solvent:           {self._solvent}')
        log.flow(f'Charge:            {charge}', ['straight'])
        log.flow(f'Unrestricted:      {unrestricted}', ['straight'])
        log.flow(f'Spin-Polarization: {spinpol}', ['straight'])
        log.flow()
        # this job and all its children should have the same value for unrestricted
        [child.unrestricted(unrestricted) for child in self.childjobs.values()]

        # we now update the child settings with the parent settings
        # this is because we have to propagate settings such as functionals, basis sets etc.
        sett = self.settings.as_plams_settings()  # first create a plams settings object
        # same for the children
        child_setts = {name: child.settings.as_plams_settings() for name, child in self.childjobs.items()}
        # update the children using the parent settings
        [child_sett.update(sett) for child_sett in child_setts.values()]
        # same for sbatch settings
        [child.sbatch(**self._sbatch) for child in self.childjobs.values()]

        # now set the charge, spinpol, unrestricted for the parent 
        self.charge(charge)
        self.spin_polarization(spinpol)
        self.unrestricted(unrestricted)
        if unrestricted:
            self.settings.input.adf.UnrestrictedFragments = 'Yes'

        # now we are going to run each child job
        for i, (childname, child) in enumerate(self.childjobs.items(), start=1):
            log.flow(f'Child job ({i}/{len(self.childjobs)}) {childname} [{formula.molecule(child._molecule)}]', ['split'])
            log.flow(f'Charge:            {child.settings.input.ams.System.charge or 0}', ['straight', 'straight'])
            log.flow(f'Spin-Polarization: {child.settings.input.adf.SpinPolarization or 0}', ['straight', 'straight'])
            # the child name will be prepended with SP showing that it is the singlepoint calculation
            child.name = f'frag_{childname}'
            child.rundir = self.rundir

            # add the path to the child adf.rkf file as a dependency to the parent job
            self.settings.input.adf.fragments[childname] = j(child.workdir, 'adf.rkf')

            if child.can_skip():
                log.flow(log.Emojis.warning + ' Already ran, skipping', ['straight', 'end'])
                log.flow()
                continue

            log.flow(log.Emojis.good + ' Submitting', ['straight', 'end'])
            # recast the plams.Settings object into a Result object as that is what run expects
            child.settings = results.Result(child_setts[childname])
            child.run()
            self.dependency(child)

            log.flow(f'SlurmID:  {child.slurm_job_id}', ['straight', 'skip', 'end'])
            log.flow(f'Work dir: {child.workdir}', ['straight', 'skip', 'end'])
            log.flow()

        # in the parent job the atoms should have the region and adf.f defined as options
        atom_lines = []
        # for each atom we check which child it came from
        for atom in self._molecule:
            for childname, child in self.childjobs.items():
                for childatom in child._molecule:
                    # we check by looking at the symbol and coordinates of the atom
                    if (atom.symbol, atom.x, atom.y, atom.z) == (childatom.symbol, childatom.x, childatom.y, childatom.z):
                        # now write the symbol and coords as a string with the correct suffix
                        atom_lines.append(f'\t\t{atom.symbol} {atom.x} {atom.y} {atom.z} region={childname} adf.f={childname}')

        # write the atoms block as a string with new line characters
        self.settings.input.ams.system.atoms = ('\n' + '\n'.join(atom_lines) + '\n\tEnd').expandtabs(4)
        # set the _molecule to None, otherwise it will overwrite the atoms block
        self._molecule = None
        # run this job
        log.flow(log.Emojis.good + ' Submitting parent job', ['split'])
        super().run()
        log.flow(f'SlurmID: {self.slurm_job_id}', ['straight', 'end'])
        log.flow()

        # also do the calculation with SCF cycles set to 1
        self.settings.input.adf.SCF.Iterations = 1
        self.settings.input.adf.print = 'FMatSFO'  # by default print the fock matrix for each SCF cycle
        self.settings.input.adf.AllPoints = 'Yes'
        self.settings.input.adf.FullFock = 'Yes'
        self.name = self.name + '_SCF1'
        log.flow(log.Emojis.good + ' Submitting extra job with 1 SCF cycle', ['split'])

        super().run()
        log.flow(f'SlurmID: {self.slurm_job_id}', ['straight', 'end'])
        log.flow()
        log.flow(log.Emojis.finish + ' Done, bye!', ['startinv'])


if __name__ == '__main__':
    with ADFJob(test_mode=True) as job:
        job.rundir = 'tmp/SN2/EDA'
        job.molecule('../../../test/fixtures/xyz/pyr.xyz')
        job.sbatch(p='tc', ntasks_per_node=15)
        job.solvent('')
        job.basis_set('tz2p')
        job.quality('veryGood')
        job.functional('LYP-D3BJ')
