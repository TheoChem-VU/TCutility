import os

from scm import plams
from typing import Dict, Optional, TYPE_CHECKING
from tcutility import data, formula, log, molecule, results, spell_check, timer
from tcutility.errors import TCCompDetailsError, TCJobError
from tcutility.job.ams import AMSJob
from tcutility.job.generic import Job
from typing import List

j = os.path.join

if TYPE_CHECKING:
    import pyfmo


class ADFJob(AMSJob):
    def __init__(self, *args, **kwargs):
        self.settings = results.Result()
        self._functional = None
        self._core = None
        self.solvent("vacuum")
        self.basis_set("TZ2P")
        self.quality("Good")
        self.SCF(thresh=1e-8)
        self.single_point()

        super().__init__(*args, **kwargs)

    def __str__(self):
        return f"{self._task}({self._functional}/{self._basis_set}), running in {os.path.join(os.path.abspath(self.rundir), self.name)}"

    def basis_set(self, typ: str = "TZ2P", core: str = "None"):
        """
        Set the basis-set type and frozen core approximation for this calculation.

        Args:
            typ: the type of basis-set to use. Default is TZ2P.
            core: the size of the frozen core approximation. Default is None.

        Raises:
            ValueError: if the basis-set name or core is incorrect.

        .. note:: If the selected functional is the r2SCAN-3c functional, then the basis-set will be set to mTZ2P.

        .. seealso::
            :mod:`tcutility.data.basis_sets` for an overview of the available basis-sets in ADF.
        """
        spell_check.check(typ, data.basis_sets.available_basis_sets["ADF"], ignore_case=True)
        spell_check.check(core, ["None", "Small", "Large"], ignore_case=True)
        if self._functional == "r2SCAN-3c" and typ != "mTZ2P":
            log.warn(f"Basis set {typ} is not allowed with r2SCAN-3c, switching to mTZ2P.")
            typ = "mTZ2P"
        self._basis_set = typ
        self._core = core
        self.settings.input.adf.basis.type = typ
        self.settings.input.adf.basis.core = core

    def spin_polarization(self, val: int):
        """
        Set the spin-polarization of the system. If the value is not zero the calculation will also be unrestricted.
        """
        self.settings.input.adf.SpinPolarization = val
        if val != 0:
            self.settings.input.adf.Unrestricted = "Yes"

    def multiplicity(self, val: int):
        """
        Set the multiplicity of the system. If the value is not one the calculation will also be unrestricted.
        We use the following values:

        1) singlet
        2) doublet
        3) triplet
        4) ...

        The multiplicity is equal to 2*S+1 for spin-polarization S.
        """
        self.settings.input.adf.SpinPolarization = (val - 1) // 2
        if val != 1:
            self.settings.input.adf.Unrestricted = "Yes"

    def unrestricted(self, val: bool):
        """
        Whether the calculation should be unrestricted.
        """
        self.settings.input.adf.Unrestricted = "Yes" if val else "No"

    def occupations(self, strategy: str):
        """
        Set the orbital filling strategy for ADF.

        Args:
            strategy: the name of the filling strategy. This can contain multiple of the options allowed.

        .. seealso::
            The SCM documentation can be found at https://www.scm.com/doc/ADF/Input/Electronic_Configuration.html#aufbau-smearing-freezing
        """
        self.settings.input.adf.Occupations = strategy

    def irrep_occupations(self, irrep: str, orbital_numbers: str):
        """
        Set the orbital occupations per irrep.

        Args:
            irrep: the irrep to set occupations for.
            orbital_numbers: the orbital occupation numbers as you would write in an input file.s
        """
        self.settings.input.adf.IrrepOccupations[irrep] = orbital_numbers

    def quality(self, val: str = "Good"):
        """
        Set the numerical quality of the calculation.

        Args:
            val: the numerical quality value to set to. This is the same as the ones used in the ADF GUI. Defaults to Good.

        Raises:
            ValueError: if the quality value is incorrect.
        """
        spell_check.check(val, ["Basic", "Normal", "Good", "VeryGood", "Excellent"], ignore_case=True)
        self.settings.input.adf.NumericalQuality = val

    def SCF_convergence(self, thresh: float = 1e-8):
        """
        Set the SCF convergence criteria for the job.

        Args:
            thresh: the convergence criteria for the SCF procedure. Defaults to 1e-8.

        .. deprecated:: 0.9.2
            Please use :meth:`ADFJob.SCF` instead of this method.
        """
        log.warn("This method has been deprecated, please use ADFJob.SCF instead.")
        self.SCF(thresh=thresh)

    def SCF(self, iterations: int = 300, thresh: float = 1e-8):
        """
        Set the SCF settings for this calculations.

        Args:
            iterations: number of iterations to perform for this calculation. Defaults to 300.
            thresh: the convergence criteria for the SCF procedure. Defaults to 1e-8.

        .. note::
            When setting the number of iterations to 0 or 1 the ``AlwaysClaimSuccess`` key will also be set to ``Yes``.
            This is to prevent the job from being flagged as a failure when reading it using :mod:`tcutility.results`.
        """
        self.settings.input.adf.SCF.Iterations = iterations
        self.settings.input.adf.SCF.Converge = thresh

        if iterations in [0, 1]:
            self.settings.input.ams.EngineDebugging.AlwaysClaimSuccess = "Yes"

    def functional(self, funtional_name: str, dispersion: str = None):
        """
        Set the functional to be used by the calculation. This also sets the dispersion if it is specified in the functional name.

        Args:
            funtional_name: the name of the functional. The value can be the same as the ones used in the ADF GUI.
            dispersion: dispersion setting to use with the functional. This is used when you want to use a functional from LibXC.

        Raises:
            ValueError: if the functional name is not recognized.

        .. note:: Setting the functional to r2SCAN-3c will automatically set the basis-set to mTZ2P.

        .. seealso::
            :mod:`tcutility.data.functionals` for an overview of the available functionals in ADF.
        """
        # before adding the new functional we should clear any previous functional settings
        self.settings.input.adf.pop("XC", None)

        functional = funtional_name.strip()
        functional = functional.replace("-D4(EEQ)", "-D4")  # D4(EEQ) and D4 are the same, unlike D3 and D3(BJ)
        self._functional = functional

        if functional == "r2SCAN-3c" and self._basis_set != "mTZ2P":
            log.info(f"Switching basis set from {self._basis_set} to mTZ2P for r2SCAN-3c.")
            self.basis_set("mTZ2P")

        if functional == "SSB-D":
            raise TCCompDetailsError(section="Functional", message='There are two functionals called SSB-D, please use "GGA:SSB-D" or "MetaGGA:SSB-D".')

        if not data.functionals.get(functional):
            raise TCCompDetailsError(section="Functional", message=f"XC-functional {functional} not found.")
        else:
            func = data.functionals.get(functional)
            self.settings.input.adf.update(func.adf_settings)

    def relativity(self, level: str = "Scalar"):
        """
        Set the treatment of relativistic effects for this calculation.

        Args:
            level: the level to set. Can be the same as the values in the ADF GUI and documentation. By default it is set to Scalar.

        Raises:
            ValueError: if the relativistic correction level is not correct.
        """
        spell_check.check(level, ["Scalar", "None", "Spin-Orbit"], ignore_case=True)
        self.settings.input.adf.relativity.level = level

    def solvent(self, name: str = None, eps: float = None, rad: float = None, use_klamt: bool = False, radii: Optional[Dict[str, float]] = None):
        """
        Model solvation using COSMO for this calculation.

        Args:
            name: the name of the solvent you want to use. Please see the ADF manual for a list of available solvents.
            eps: the dielectric constant of your solvent. You can use this in place of the solvent name if you need more control over COSMO.
            rad: the radius of the solvent molecules. You can use this in place of the solvent name if you need more control over COSMO.
            use_klamt: whether to use the klamt atomic radii. This is usually used when you have charged species (?).
            radii: the atomic radii to use for the COSMO calculation. A dictionary such as {Cl: 1.04} will be converted to Cl = 0.01 in the input script. This gets (partially) overwritten if use_klamt is enables.

        Raises:
            ValueError: if the solvent name is given, but incorrect.

        .. seealso::
            :mod:`tcutility.data.cosmo` for an overview of the available solvent names and formulas.
        """
        if name:
            spell_check.check(name, data.cosmo.available_solvents, ignore_case=True, insertion_cost=0.3)
            self._solvent = name
        else:
            self._solvent = f"COSMO(eps={eps} rad={rad})"

        if name == "vacuum":
            self.settings.input.adf.pop("Solvation", None)
            return

        self.settings.input.adf.Solvation.Surf = "Delley"
        solv_string = ""
        if name:
            solv_string += f"name={name} "
        else:
            self.settings.input.adf.Solvation.Solv = f"eps={eps} rad={rad} "
        if use_klamt:
            solv_string += "cav0=0.0 cav1=0.0"
        else:
            solv_string += "cav0=0.0 cav1=0.0067639"
        self.settings.input.adf.Solvation.Solv = solv_string

        self.settings.input.adf.Solvation.Charged = "method=CONJ corr"
        self.settings.input.adf.Solvation["C-Mat"] = "POT"
        self.settings.input.adf.Solvation.SCF = "VAR ALL"
        self.settings.input.adf.Solvation.CSMRSP = None

        if radii is not None:
            self.settings.input.adf.solvation.radii = radii

        if use_klamt:
            radii = {"H": 1.30, "C": 2.00, "N": 1.83, "O": 1.72, "F": 1.72, "Si": 2.48, "P": 2.13, "S": 2.16, "Cl": 2.05, "Br": 2.16, "I": 2.32}
            self.settings.input.adf.solvation.radii = radii

    def symmetry(self, group: str):
        """
        Specify the symmetry group to be used by ADF.

        Args:
            group: the symmetry group to be used.
        """
        self.settings.input.adf.Symmetry = group

    def _check_job(self):
        # if we have spinpolarization we do not want to use DFTB to calculate the initial hessian
        if self.settings.input.adf.SpinPolarization != 0 and self.settings.input.ams.GeometryOptimization.InitialHessian.Type == "CalculateWithFastEngine":
            # we simply remove it from the geometryoptimization block
            self.settings.input.ams.GeometryOptimization.pop("InitialHessian", None)

    def excitations(self, excitation_number: int = 10, excitation_type: str = '', method: str = 'Davidson', use_TDA: bool = False, energy_gap: List[float] = None):
        """
        Calculate the electronic excitations using TD-DFT.

        Args:
            excitation_number: the number of excitations to include. Defaults to ``10``.
            excitation_type: the type of excitations to include. 
                Defaults to an empty string, indicating the default value for ADF.
            method: the excitation methodology to use. Defaults to ``Davidson``.
                If set to the ``None``, the excitations are disabled.
            use_TDA: whether to enable the Tamm-Dancoff approximation. Defaults to ``False``.
            energy_gap: list with two variables from which to limit excitations calculated i.e. ``(0, 0.3)`` in Hartrees. Defaults to ``None``.
        """
        # clean the input first
        [self.settings.input.adf.Excitations.pop(key, None) for key in ['davidson', 'exact', 'bse', 'singleorbtrans', 'stda', 'stddft', 'tda-dftb', 'td-dftb']]
        [self.settings.input.adf.pop(key, None) for key in ['cvndft', 'tda']]
        [self.settings.input.adf.Excitations.pop(key, None) for key in ['allowed', 'onlysing', 'onlytrip', 'sopert']]

        if method is None:
            return

        _allowed_methods = [
            'Davidson',
            'Exact',
            'BSE',
            'CV(n)-DFT',
            'Delta Eps',
            'sTDA',
            'sTDDFT',
            'TDA-DFT+TB',
            'TD-DFT+TB',
            ]
        spell_check.check(method, _allowed_methods, ignore_case=True)

        if method.lower() == 'davidson':
            self.settings.input.adf.Excitations.davidson = '\n    End'
        elif method.lower() == 'exact':
            self.settings.input.adf.Excitations.exact = '\n    End'
        elif method.lower() == 'bse':
            self.settings.input.adf.Excitations.bse = 'Yes'
        elif method.lower() == 'cv(n)-dft':
            self.settings.input.adf.Excitations.davidson = '\n    End'
            self.settings.input.adf.CVnDFT.R_CV_DFT = '&'
            self.settings.input.adf.CVnDFT.SubEnd = ''
        elif method.lower() == 'delta eps':
            self.settings.input.adf.Excitations.SingleOrbTrans = 'Yes'
        elif method.lower() == 'stda':
            self.settings.input.adf.Excitations.STDA = 'Yes'
        elif method.lower() == 'stddft':
            self.settings.input.adf.Excitations.STDDFT = 'Yes'
        elif method.lower() == 'tda-dft+tb':
            self.settings.input.adf.Excitations['TDA-DFTB'] = 'Yes'
        elif method.lower() == 'td-dft+tb':
            self.settings.input.adf.Excitations['TD-DFTB'] = 'Yes'

        _allowed_types = [
            'None',
            'AllowedOnly',
            'SingletOnly',
            'TripletOnly',
            'SingletAndTriplet',
            'Spin-Orbit (Perturbative)',
            'Spin-Orbit (SCF)',
            'Default',
            '',
            ]
        spell_check.check(excitation_type, _allowed_types, ignore_case=True)

        if excitation_type.lower() == 'allowedonly':
            self.settings.input.adf.Excitations.Allowed = 'Yes'
        elif excitation_type.lower() == 'singletonly':
            self.settings.input.adf.Excitations.OnlySing = 'Yes'
        elif excitation_type.lower() == 'tripletonly':
            self.settings.input.adf.Excitations.OnlyTrip = 'Yes'
        elif excitation_type.lower() == 'spin-orbit (perturbative)':
            self.settings.input.adf.Excitations.SOPert = ''
        # these values all do not have specific keys in the Excitation block
        elif excitation_type.lower() in ['singletandtriplet', 'default', '', 'spin-orbit (scf)']:
            pass

        self.settings.input.adf.Excitations.Lowest = excitation_number

        if use_TDA:
            self.settings.input.adf.TDA = 'Yes'

        if energy_gap is not None:
            self.settings.input.adf.MODIFYEXCITATION.UseOccVirtRange = f'{energy_gap[0]} {energy_gap[1]}'
            if self.settings.input.adf.relativity.level.lower() == 'scalar'  or 'spin-orbit':
                self.settings.input.adf.MODIFYEXCITATION.UseScaledZORA = ' '


def copy_atom(atom):
    s, c = atom.symbol, atom.coords
    return plams.Atom(symbol=s, coords=c)


class ADFFragmentJob(ADFJob):
    def __init__(self, *args, **kwargs):
        self.decompose_elstat = kwargs.pop('decompose_elstat', False)
        self.counter_poise = kwargs.pop('counter_poise', False)
        self.scf0_calculation = kwargs.pop('sfo0_calculation', False)
        self.child_jobs = {}
        super().__init__(*args, **kwargs)
        self.name = "EDA"


    def add_fragment(self, mol: plams.Molecule, name: str = None, charge: int = 0, spin_polarization: int = 0):
        """
        Add a fragment to this job. Optionally give the name, charge and spin-polarization of the fragment as well.

        Args:
            mol: the molecule corresponding to the fragment.
            name: the name of the fragment. By default it will be set to ``fragment{N+1}`` if ``N`` is the number of fragments already present.
            charge: the charge of the fragment to be added.
            spin_polarization: the spin-polarization of the fragment to be added.
        """
        # in case of giving fragments as indices we dont want to add the fragment to the molecule later
        add_frag_to_mol = True
        # we can be given a list of atoms
        if isinstance(mol, list) and isinstance(mol[0], plams.Atom):
            mol_ = plams.Molecule()
            [mol_.add_atom(copy_atom(atom)) for atom in mol]
            mol = mol_

        # or a list of integers
        if isinstance(mol, list) and isinstance(mol[0], int):
            if not self._molecule:
                log.error(f"Trying to add fragment based on atom indices, but main job does not have a molecule yet. Call the {self.__class__.__name__}.molecule method to add one.")
                return
            mol_ = plams.Molecule()

            [mol_.add_atom(copy_atom(self._molecule[i])) for i in mol]
            mol = mol_.copy()
            add_frag_to_mol = False

        # check if the atoms in the new fragment are already present in the other fragments.
        # if it is we should raise an error
        for child in self.child_jobs.values():
            if any((atom.symbol, atom.coords) == (myatom.symbol, myatom.coords) for atom in child._molecule for myatom in mol):
                raise TCJobError(job_class=self.__class__.__name__, message="The atoms in the new fragment are already present in the other fragments.")

        name = name or f"fragment{len(self.child_jobs) + 1}"
        self.child_jobs[name] = ADFJob(test_mode=self.test_mode)
        self.child_jobs[name].molecule(mol)
        if charge:
            self.child_jobs[name].charge(charge)
        if spin_polarization:
            self.child_jobs[name].spin_polarization(spin_polarization)
        setattr(self, name, self.child_jobs[name])

        if not add_frag_to_mol:
            return

        if self._molecule is None:
            self._molecule = plams.Molecule()
            [self._molecule.add_atom(copy_atom(atom)) for atom in self.child_jobs[name]._molecule]
        else:
            for atom in self.child_jobs[name]._molecule:
                if any((atom.symbol, atom.coords) == (myatom.symbol, myatom.coords) for myatom in self._molecule):
                    continue
                self._molecule.add_atom(copy_atom(atom))

    def guess_fragments(self):
        """
        Guess what the fragments are based on data stored in the molecule provided for this job.
        This will automatically set the correct fragment molecules, names, charges and spin-polarizations.

        .. seealso::
            | :func:`tcutility.molecule.guess_fragments` for an explanation of the xyz-file format required to guess the fragments.
            | :meth:`ADFFragmentJob.add_fragment` to manually add a fragment.

        .. note::
            This function will be automatically called if there were no fragments given to this calculation.
        """
        frags = molecule.guess_fragments(self._molecule)
        if frags is None:
            log.error("Could not load fragment data for the molecule.")
            return False

        for fragment_name, fragment in frags.items():
            charge = fragment.flags.get("charge", 0)
            spin_polarization = fragment.flags.get("spinpol", 0)
            self.add_fragment(fragment, fragment_name, charge=charge, spin_polarization=spin_polarization)

        return True

    def remove_virtuals(self, frag=None, subspecies=None, nremove=None):
        """
        Remove virtual orbitals from the fragments.

        Args:
            frag: the fragment to remove virtuals from. If set to ``None`` we remove all virtual orbitals of all fragments.
            subspecies: the symmetry subspecies to remove virtuals from. If set to ``None`` we assume we have ``A`` subspecies.
            nremove: the number of virtuals to remove. If set to ``None`` we will guess the number of virtuals based on the basis-set chosen.
        """
        if frag is None:
            self.settings.input.adf.RemoveAllFragVirtuals = "Yes"
            return

        # if nremove is not given we will get it from the atoms in the fragment
        if nremove is None:
            # guess the virtual numbers only works for non-frozen-core calculations
            if self._core.lower() != "none":
                raise TCJobError(job_class=self.__class__.__name__, message="Cannot guess number of virtual orbitals for calculations with a frozen core.")
            # the basis-set has to be present in the prepared data
            if self._basis_set.lower() not in [bs.lower() for bs in data.basis_sets._number_of_orbitals.keys()]:
                raise TCJobError(job_class=self.__class__.__name__, message=f"Cannot guess number of virtual orbitals for calculations with the {self._basis_set} basis-set.")

            # sum up the number of virtuals per atom in the fragment
            nremove = 0
            for atom in self.child_jobs[frag]._molecule:
                nremove += data.basis_sets.number_of_virtuals(atom.symbol, self._basis_set)
            # positive charge adds a virtual and negative removes a virtual
            nremove += self.child_jobs[frag].settings.input.ams.System.charge or 0

        self.settings.input.adf.setdefault("RemoveFragOrbitals", "")
        self.settings.input.adf.RemoveFragOrbitals += f"""
    {frag}
      {subspecies or 'A'} {nremove}
    SubEnd
  End
        """

    def frag_occupations(self, frag=None, subspecies=None, alpha=None, beta=None):
        """
        Set the occupations of the fragments.

        Args:
            frag: the fragment to set the occupations for.
            subspecies: the symmetry subspecies to set the occupations for. If set to ``None`` we assume we have ``A`` subspecies.
            alpha: the number of alpha electrons. If set to ``None`` we will guess the number of electrons based on the spin-polarization set.
            beta: the number of beta electrons. If set to ``None`` we will guess the number of electrons based on the spin-polarization set.
        """

        child_job = self.child_jobs[frag]

        if alpha is None and beta is None:
            spinpol = child_job.settings.input.adf.SpinPolarization or 0
            charge = child_job.settings.input.ams.system.charge or 0
            nelectrons = sum(atom.atnum for atom in child_job._molecule) - charge
            alpha = nelectrons // 2 + spinpol
            beta  = nelectrons // 2

        self.settings.input.adf.setdefault("FragOccupations", "")
        self.settings.input.adf.FragOccupations = self.settings.input.adf.FragOccupations.replace(" End", "")
        self.settings.input.adf.FragOccupations += f"""
    {frag}
      {subspecies or 'A'} {alpha} // {beta}
    SubEnd
  End
        """

    def run(self):
        """
        Run the ``ADFFragmentJob``. This involves setting up the calculations for each fragment as well as the parent job.
        It will also submit a calculation with the SCF iterations set to 0 in order to facilitate investigation of the field effects using PyOrb.
        """
        # check if the user defined fragments for this job

        if len(self.child_jobs) == 0:
            log.warn("Fragments were not specified yet, trying to read them from the xyz file ...")

            # if they did not define the fragments, try to guess them using the xyz-file
            if not self.guess_fragments():
                log.error("Please specify the fragments using ADFFragmentJob.add_fragment or specify them in the xyz file.")
                raise

        mol_str = " + ".join([formula.molecule(child._molecule) for child in self.child_jobs.values()])
        log.flow(f"ADFFragmentJob [{mol_str}]", ["start"])
        # obtain some system wide properties of the molecules
        charge = sum([child.settings.input.ams.System.charge or 0 for child in self.child_jobs.values()])
        unrestricted = any([(child.settings.input.adf.Unrestricted or "no").lower() == "yes" for child in self.child_jobs.values()]) or (self.settings.input.adf.Unrestricted or "no").lower() == "yes"
        spinpol = sum([child.settings.input.adf.SpinPolarization or 0 for child in self.child_jobs.values()])
        log.flow(f"Level:             {self._functional}/{self._basis_set}")
        log.flow(f"Solvent:           {self._solvent}")
        log.flow(f"Charge:            {charge}", ["straight"])
        log.flow(f"Unrestricted:      {unrestricted}", ["straight"])
        log.flow(f"Spin-Polarization: {spinpol}", ["straight"])
        log.flow()

        # this job and all its children should have the same value for unrestricted
        # [child.unrestricted(unrestricted) for child in self.child_jobs.values()]

        # propagate the post- and preambles to the child_jobs
        [child.add_preamble(preamble) for preamble in self._preambles for child in self.child_jobs.values()]
        [child.add_postamble(postamble) for postamble in self._postambles for child in self.child_jobs.values()]

        # we now update the child settings with the parent settings
        # this is because we have to propagate settings such as functionals, basis sets etc.
        sett = self.settings.as_plams_settings()  # first create a plams settings object
        # same for the children
        child_setts = {name: child.settings.as_plams_settings() for name, child in self.child_jobs.items()}
        # update the children using the parent settings
        [child_sett.update(sett) for child_sett in child_setts.values()]
        [child_sett.input.adf.pop("RemoveFragOrbitals", None) for child_sett in child_setts.values()]
        [child_sett.input.adf.pop("RemoveAllFragVirtuals", None) for child_sett in child_setts.values()]
        [child_sett.input.adf.pop("FragOccupations", None) for child_sett in child_setts.values()]
        # remove settings related to electronic excitations
        [child_sett.input.adf.pop("Excitations", None) for child_sett in child_setts.values()]
        [child_sett.input.adf.pop("TDA", None) for child_sett in child_setts.values()]
        # same for sbatch settings
        [child.sbatch(**self._sbatch) for child in self.child_jobs.values()]

        # now set the charge, spinpol, unrestricted for the parent
        if charge:
            self.charge(charge)
        if spinpol:
            self.spin_polarization(spinpol)
        if unrestricted:
            self.unrestricted(unrestricted)
            self.settings.input.adf.UnrestrictedFragments = "Yes"

        elstat_jobs = {}

        # now we are going to run each child job
        for i, (child_name, child) in enumerate(self.child_jobs.items(), start=1):
            # the child name will be prepended with SP showing that it is the singlepoint calculation
            child.name = f"frag_{child_name}"
            child.rundir = j(self.rundir, self.name)

            # # add the path to the child adf.rkf file as a dependency to the parent job
            self.settings.input.adf.fragments[child_name] = j(child.workdir, "adf.rkf")

            # recast the plams.Settings object into a Result object as that is what run expects
            child.settings = results.Result(child_setts[child_name])

            log.flow(f'Fragment ({i}/{len(self.child_jobs)}) {child_name} [{formula.molecule(child._molecule)}]', ['split'])
            log.flow(f'Charge:            {child.settings.input.ams.System.charge or 0}', ['straight', 'straight'])
            log.flow(f'Spin-Polarization: {child.settings.input.adf.SpinPolarization or 0}', ['straight', 'straight'])
            log.flow(f'Work dir:          {child.workdir}', ['straight', 'straight'])

            if child.can_skip():
                log.flow(log.Emojis.warning + " Already ran, skipping", ["straight", "end"])
                log.flow()
            else:
                log.flow(log.Emojis.good + " Submitting", ["straight", "end"])
                [child._sbatch.pop(key, None) for key in ["D", "chdir", "J", "job_name", "o", "output"]]
                child.run()
                self.dependency(child)
                log.flow(f"SlurmID:  {child.slurm_job_id}", ["straight", "skip", "end"])
                log.flow()

            if self.decompose_elstat:
                child_STOFIT = ADFJob(child)
                child_STOFIT.name += "_STOFIT"
                elstat_jobs[child_STOFIT.name] = child_STOFIT
                child_STOFIT.settings.input.adf.STOFIT = ""
                child_STOFIT.settings.input.adf.PRINT += " Elstat"
                child_STOFIT.settings.input.adf.pop("NumericalQuality")
                child_STOFIT.settings.input.adf.BeckeGrid.Quality = "Excellent"

                log.flow(f'Fragment ({i}/{len(self.child_jobs)}) {child_name} [{formula.molecule(child._molecule)}] with STOFIT', ['split'])
                log.flow(f'Charge:            {child_STOFIT.settings.input.ams.System.charge or 0}', ['straight', 'straight'])
                log.flow(f'Spin-Polarization: {child_STOFIT.settings.input.adf.SpinPolarization or 0}', ['straight', 'straight'])
                log.flow(f'Work dir:          {child_STOFIT.workdir}', ['straight', 'straight'])

                if child_STOFIT.can_skip():
                    log.flow(log.Emojis.warning + " Already ran, skipping", ["straight", "end"])
                    log.flow()
                else:
                    log.flow(log.Emojis.good + " Submitting", ["straight", "end"])
                    [child_STOFIT._sbatch.pop(key, None) for key in ["D", "chdir", "J", "job_name", "o", "output"]]
                    child_STOFIT.run()
                    self.dependency(child_STOFIT)
                    log.flow(f"SlurmID:  {child_STOFIT.slurm_job_id}", ["straight", "skip", "end"])
                    log.flow()

                child_NoElectrons = ADFJob(child)
                child_NoElectrons.name += "_NoElectrons"
                elstat_jobs[child_NoElectrons.name] = child_NoElectrons

                child_NoElectrons.settings.input.adf.STOFIT = ''
                child_NoElectrons.settings.input.adf.PRINT += ' Elstat'
                child_NoElectrons.charge(molecule.number_of_electrons(child_NoElectrons._molecule))
                child_NoElectrons.spin_polarization(0)
                child_NoElectrons.settings.input.adf.pop("NumericalQuality")
                child_NoElectrons.settings.input.adf.BeckeGrid.Quality = "Excellent"


                log.flow(f'Fragment ({i}/{len(self.child_jobs)}) {child_name} [{formula.molecule(child._molecule)}] without Electrons', ['split'])
                log.flow(f'Charge:            {child_NoElectrons.settings.input.ams.System.charge or 0}', ['straight', 'straight'])
                log.flow(f'Spin-Polarization: {child_NoElectrons.settings.input.adf.SpinPolarization or 0}', ['straight', 'straight'])
                log.flow(f'Work dir:          {child_NoElectrons.workdir}', ['straight', 'straight'])

                if child_NoElectrons.can_skip():
                    log.flow(log.Emojis.warning + " Already ran, skipping", ["straight", "end"])
                    log.flow()
                else:
                    log.flow(log.Emojis.good + " Submitting", ["straight", "end"])
                    [child_NoElectrons._sbatch.pop(key, None) for key in ["D", "chdir", "J", "job_name", "o", "output"]]
                    child_NoElectrons.run()
                    self.dependency(child_NoElectrons)
                    log.flow(f"SlurmID:  {child_NoElectrons.slurm_job_id}", ["straight", "skip", "end"])
                    log.flow()

        # in the parent job the atoms should have the region and adf.f defined as options
        atom_lines = []
        # for each atom we check which child it came from
        for atom in self._molecule:
            for child_name, child in self.child_jobs.items():
                for childatom in child._molecule:
                    # we check by looking at the symbol and coordinates of the atom
                    if (atom.symbol, atom.x, atom.y, atom.z) == (childatom.symbol, childatom.x, childatom.y, childatom.z):
                        # now write the symbol and coords as a string with the correct suffix
                        atom_lines.append(f"\t\t{atom.symbol} {atom.x} {atom.y} {atom.z} region={child_name} adf.f={child_name}")

        old_name = self.name
        # write the atoms block as a string with new line characters
        self.settings.input.ams.system.atoms = ("\n" + "\n".join(atom_lines) + "\n\tEnd").expandtabs(4)
        # set the _molecule to None, otherwise it will overwrite the atoms block
        self._molecule = None
        # run this job
        self.rundir = j(self.rundir, old_name)
        self.name = "complex"
        log.flow(log.Emojis.good + " Submitting parent job", ["split"])

        super().run()
        log.flow(f"SlurmID: {self.slurm_job_id}", ["straight", "end"])
        log.flow()

        # also do the calculation with SCF cycles set to 1 if desired
        if self.scf0_calculation:
            old_iters = self.settings.input.adf.SCF.Iterations or 300
            self.SCF(iterations=0)
            # we must repopulate the sbatch settings for the new run
            [self._sbatch.pop(key, None) for key in ["D", "chdir", "J", "job_name", "o", "output"]]
            self.name = "complex_SCF0"
            log.flow(log.Emojis.good + " Submitting extra job with 0 SCF iterations", ["split"])

            super().run()
            log.flow(f"SlurmID: {self.slurm_job_id}", ["straight", "end"])
            log.flow()

            # reset the SCF iterations
            self.SCF(iterations=old_iters)

        # also do the calculation with no electrons on the fragments if the user requested a elstat decomposition
        if self.decompose_elstat:
            frag_names = self.child_jobs.keys()
            self.settings.input.adf.pop("NumericalQuality")
            self.settings.input.adf.BeckeGrid.Quality = "Excellent"
            [self._sbatch.pop(key, None) for key in ["D", "chdir", "J", "job_name", "o", "output"]]
            self.name = "complex_STOFIT"

            # set the region and fragment files correctly
            atom_lines_ = []
            for line in atom_lines:
                for frag in frag_names:
                    line = line.replace(frag, f"{frag}_STOFIT")
                atom_lines_.append(line)

            self.settings.input.ams.system.atoms = ("\n" + "\n".join(atom_lines_) + "\n\tEnd").expandtabs(4)
            # set the fragment references correctly
            self.settings.input.adf.pop("fragments")
            for frag_name in frag_names:
                self.settings.input.adf.fragments[frag_name + "_STOFIT"] = j(elstat_jobs["frag_" + frag_name + "_STOFIT"].workdir, "adf.rkf")
            self.settings.input.adf.STOFIT = ""
            self.settings.input.adf.PRINT += " Elstat"
            [self._sbatch.pop(key, None) for key in ["D", "chdir", "J", "job_name", "o", "output"]]
            log.flow(log.Emojis.good + " Submitting complex with STOFIT", ["split"])
            super().run()
            log.flow(f"SlurmID: {self.slurm_job_id}", ["straight", "end"])
            log.flow()

            for frag in frag_names:
                # other_frags stores fragment names for fragments that keep their electrons
                other_frags = [frag_ for frag_ in frag_names if frag_ != frag]

                # we must repopulate the sbatch settings for the new run
                [self._sbatch.pop(key, None) for key in ["D", "chdir", "J", "job_name", "o", "output"]]
                self.name = f"complex_{frag}_NoElectrons"

                # set the region and fragment files correctly
                atom_lines_ = []
                for line in atom_lines:
                    line = line.replace(frag, f"{frag}_NoElectrons")
                    for other_frag in other_frags:
                        line = line.replace(other_frag, f"{other_frag}_STOFIT")
                    atom_lines_.append(line)
                self.settings.input.ams.system.atoms = ("\n" + "\n".join(atom_lines_) + "\n\tEnd").expandtabs(4)

                # set the fragment references correctly
                self.settings.input.adf.pop("fragments")
                self.settings.input.adf.fragments[frag + "_NoElectrons"] = j(elstat_jobs["frag_" + frag + "_NoElectrons"].workdir, "adf.rkf")
                for other_frag in other_frags:
                    self.settings.input.adf.fragments[other_frag + "_STOFIT"] = j(elstat_jobs["frag_" + other_frag + "_STOFIT"].workdir, "adf.rkf")

                other_charge = sum([elstat_jobs["frag_" + other_frag + "_STOFIT"].settings.input.ams.System.charge for other_frag in other_frags])
                total_charge = other_charge + (elstat_jobs["frag_" + frag + "_NoElectrons"].settings.input.ams.System.charge)
                self.charge(total_charge)

                other_spin_polarization = sum([elstat_jobs["frag_" + other_frag + "_STOFIT"].settings.input.adf.SpinPolarization for other_frag in other_frags])
                total_spin_polarization = other_spin_polarization + (elstat_jobs["frag_" + frag + "_NoElectrons"].settings.input.adf.SpinPolarization)
                self.spin_polarization(total_spin_polarization)

                log.flow(log.Emojis.good + f" Submitting complex with 0 electrons in fragment {frag}", ["split"])
                [self._sbatch.pop(key, None) for key in ["D", "chdir", "J", "job_name", "o", "output"]]
                super().run()
                log.flow(f"SlurmID: {self.slurm_job_id}", ["straight", "end"])
                log.flow()

        if self.counter_poise:
            self.settings.input.ams.EngineDebugging.pop('AlwaysClaimSuccess', None)
            self.settings.input.adf.pop('fragments', None)
            for frag, frag_job in self.child_jobs.items():
                atoms = [atom for job in self.child_jobs.values() for atom in job._molecule]

                # in the parent job the atoms should have the region and adf.f defined as options
                atom_lines = []
                # for each atom we check which child it came from
                for atom in atoms:
                    for child_name, child in self.child_jobs.items():
                        for childatom in child._molecule:
                            # we check by looking at the symbol and coordinates of the atom
                            if (atom.symbol, atom.x, atom.y, atom.z) == (childatom.symbol, childatom.x, childatom.y, childatom.z):
                                # now write the symbol and coords as a string with the correct suffix and ghost indicator
                                if child_name == frag:
                                    atom_lines.append(f'\t\t{atom.symbol} {atom.x} {atom.y} {atom.z}')
                                else:
                                    atom_lines.append(f'\t\tGh.{atom.symbol} {atom.x} {atom.y} {atom.z}')

                # write the atoms block as a string with new line characters
                self.settings.input.ams.system.atoms = ("\n" + "\n".join(atom_lines) + "\n\tEnd").expandtabs(4)
                self.spin_polarization(frag_job.settings.input.adf.SpinPolarization or 0)
                self.charge(frag_job.settings.input.ams.System.charge or 0)
                self.unrestricted((frag_job.settings.input.adf.Unrestricted or 'no').lower() == 'yes')

                # we must repopulate the sbatch settings for the new run
                self.name = f'complex_{frag}_Ghost'
                log.flow(log.Emojis.good + f' Submitting {frag} with the basis-set of the complex', ['split'])
                [self._sbatch.pop(key, None) for key in ["D", "chdir", "J", "job_name", "o", "output"]]
                super().run()
                log.flow(f'SlurmID: {self.slurm_job_id}', ['straight', 'end'])
                log.flow()

        log.flow(log.Emojis.finish + ' Done, bye!', ['startinv'])


class DensfJob(Job):
    def __init__(self, overwrite: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = results.Result()
        self.rundir = "tmp"
        self.name = "densf"
        self.gridsize()
        self._mos = []
        self._sfos = []
        self._extras = []
        self.settings.ADFFile = None
        self.overwrite = overwrite

    def __str__(self):
        return f"Densf({self.target}), running in {self.workdir}"

    def gridsize(self, size="medium", grid_extend=7.5):
        """
        Set the size of the grid to be used by Densf.

        Args:
            size: either "coarse", "medium", "fine". Defaults to "medium".
        """
        spell_check.check(size, ["coarse", "medium", "fine"], ignore_case=True)
        self.settings.grid = size
        self.settings.grid_extend = grid_extend

    def grid(self, args):
        self.settings.grid = '\n' + '\n'.join(args) + 'EXTEND 7.5\n'

    def orbital(self, orbital: "pyfmo.orbitals.sfo.SFO" or "pyfmo.orbitals.mo.MO"):  # noqa: F821
        """
        Add a PyOrb orbital for Densf to calculate.
        """
        import pyfmo

        if isinstance(orbital, (pyfmo.orbitals.sfo.SFO, pyfmo.orbitals2.objects.SFO)):
            self._sfos.append(orbital)
        elif isinstance(orbital, (pyfmo.orbitals.mo.MO, pyfmo.orbitals2.objects.MO)):
            self._mos.append(orbital)
        else:
            raise TCJobError(job_class=self.__class__.__name__, message=f"Unknown object {orbital} of type{type(orbital)}. It should be a pyfmo.orbitals.sfo.SFO or pyfmo.orbitals.mos.MO object.")

        # check if the ADFFile is the same for all added orbitals
        if self.settings.ADFFile is None:
            self.settings.ADFFile = orbital.kfpath

        elif self.settings.ADFFile != orbital.kfpath:
            raise TCJobError(job_class=self.__class__.__name__, message="RKF file that was previously set not the same as the one being set now. Please start a new job for each RKF file.")


    def density(self, orbitals: 'pyfmo.orbitals.Orbitals'):  # noqa: F821

        # check if the ADFFile is the same for all added orbitals
        if self.settings.ADFFile is None:
            self.settings.ADFFile = orbitals.kfpath

        elif self.settings.ADFFile != orbitals.kfpath:
            raise ValueError("RKF file that was previously set not the same as the one being set now. Please start a new job for each RKF file.")

        self._extras.append("Density SCF")

    def NCI(self, density: str = 'both', rhovdw=0.02, rdg=0.5):
        '''
        Setup calculation of NCI values.

        Args:
            density: the density to calculate for, either "FIT" or  "BOTH", default is "BOTH".
            rhovdw: threshold of density for detection of weak interaction regions, default is `0.02`.
            rdg: threshold of reduced density gradient, default is `0.5`.
        '''
        self._extras.append(f'NCI {density} RHOVDW={rhovdw} RDG={rdg}')

    def _setup_job(self):
        os.makedirs(self.workdir, exist_ok=True)

        # set up the input file. This should always contain calling of the densf program, as per the SCM documentation
        with open(self.inputfile_path, "w+") as inpf:
            inpf.write("$AMSBIN/densf << eor\n")
            inpf.write(f"ADFFile {os.path.abspath(self.settings.ADFFile)}\n")
            inpf.write(f"GRID {self.settings.grid}\n")
            inpf.write("END\n")
            if self.settings.grid_extend:
                inpf.write(f"EXTEND {self.settings.grid_extend}\n")

            if len(self._mos) > 0:
                inpf.write("Orbitals SCF\n")
                for orb in self._mos:
                    if orb.spin in ['A', 'B']:
                        spin = {'A': 'alpha', 'B': 'beta'}[orb.spin]
                        inpf.write(f"    {spin}\n")
                    inpf.write(f"    {orb.symmetry} {orb.symmetry_index}\n")
                inpf.write("END\n")

            if len(self._sfos) > 0:
                inpf.write("Orbitals SFO\n")
                for orb in self._sfos:
                    if orb.spin in ['A', 'B']:
                        spin = {'A': 'alpha', 'B': 'beta'}[orb.spin]
                        inpf.write(f"    {spin}\n")
                    inpf.write(f"    {orb.symmetry} {orb.symmetry_index}\n")
                inpf.write("END\n")
                print(inpf.read())

            for line in self._extras:
                inpf.write(line + "\n")

            # cuboutput prefix is always the original run directory containing the adf.rkf file and includes the grid size
            outname = self.settings.grid if self.settings.grid.lower() in ['coarse', 'medium', 'fine'] else 'custom_grid'
            inpf.write(f"CUBOUTPUT {os.path.split(os.path.abspath(self.settings.ADFFile))[0]}/{outname}\n")
            inpf.write("eor\n")

        # the runfile should simply execute the input file.
        with open(self.runfile_path, "w+") as runf:
            runf.write("#!/bin/sh\n\n")
            runf.write("\n".join(self._preambles) + "\n\n")
            runf.write(f"sh {self.inputfile_path}\n")
            runf.write("\n".join(self._postambles))

        return True

    @property
    def output_cub_paths(self):
        """
        The output cube file paths that will be/were calculated by this job.
        """
        paths = []
        cuboutput = f"{os.path.split(os.path.abspath(self.settings.ADFFile))[0]}/{self.settings.grid}"

        for mo in self._mos:
            spin_part = "" if mo.spin == "AB" else f"_{mo.spin}"
            paths.append(f"{cuboutput}%SCF_{mo.symmetry.replace(':', '_')}{spin_part}%{mo.symmetry_index}.cub")

        for sfo in self._sfos:
            spin_part = "" if sfo.spin == "AB" else f"_{sfo.spin}"
            paths.append(f"{cuboutput}%SFO_{sfo.symmetry.replace(':', '_')}{spin_part}%{sfo.symmetry_index}.cub")

        for extra in self._extras:
            if extra == "Density SCF":
                paths.append(f"{cuboutput}%SCF%Density.cub")

            if extra.startswith('NCI'):
                paths.append(f'{cuboutput}%SCF%FitDenSigned.cub')
                paths.append(f'{cuboutput}%SCF%Fitdensity.cub')
                paths.append(f'{cuboutput}%SCF%FitNCI.cub')
                paths.append(f'{cuboutput}%SCF%FitRDG.cub')
                paths.append(f'{cuboutput}%SCF%FitRDGforNCI.cub')
                if 'both' in extra.lower():
                    paths.append(f'{cuboutput}%SCF%DenSigned.cub')
                    paths.append(f'{cuboutput}%SCF%Density.cub')
                    paths.append(f'{cuboutput}%SCF%NCI.cub')
                    paths.append(f'{cuboutput}%SCF%RDG.cub')
                    paths.append(f'{cuboutput}%SCF%RDGforNCI.cub')


        return paths

    def can_skip(self):
        if self.overwrite:
            return False
            
        return all(os.path.exists(path) for path in self.output_cub_paths)


if __name__ == "__main__":
    # import pyfmo

    # orbs = pyfmo.orbitals.Orbitals('/Users/yumanhordijk/PhD/MM2024/calculations/IRC/pi_beta_trans_TS1/pi_beta/pi_beta_trans/complex.00039/adf.rkf')
    # with DensfJob() as job:
    #     job.orbital(orbs.sfos['frag1(HOMO)'])

    # with ADFFragmentJob() as job:
    #     ...

    # timer.timer_level = 40

    with ADFJob(test_mode=True) as job:
        job.irrep_occupations('A', '28 // 26')
        job.molecule('exammple.xyz')


    # with ADFFragmentJob(test_mode=True) as job:
    #     job.frag_occupations('A', '28 // 26')
    #     job.molecule('exammple.xyz')
