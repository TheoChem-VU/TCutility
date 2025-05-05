from typing import Dict, List

import numpy as np
from scm.plams import KFReader

from tcutility import constants, ensure_list
from tcutility.results import Result, cache
from tcutility.tc_typing import arrays

# ------------------------------------------------------------- #
# ------------------- Calculation Settings -------------------- #
# ------------------------------------------------------------- #


def get_calc_settings(info: Result) -> Result:
    """Function to read calculation settings for an ADF calculation.

    Args:
        info: Result object containing ADF calculation settings.

    Returns:
        :Result object containing properties from the ADF calculation:

            - **task (str)** – the task that was set for the calculation.
            - **relativistic (bool)** – whether or not relativistic effects were enabled.
            - **relativistic_type (str)** – the name of the relativistic approximation used.
            - **unrestricted_sfos (bool)** – whether or not SFOs are treated in an unrestricted manner.
            - **unrestricted_mos (bool)** – whether or not MOs are treated in an unrestricted manner.
            - **symmetry.group (str)** – the symmetry group selected for the molecule.
            - **symmetry.labels (list[str])** – the symmetry labels associated with the symmetry group.
            - **used_regions (bool)** – whether regions were used in the calculation.
            - **charge (int)** - the charge of the system.
            - **spin_polarization (int)** - the spin-polarization of the system.
            - **multiplicity (int)** - the multiplicity of the system. This is equal to 2|S|+1 for spin-polarization S.
    """
    assert info.engine == "adf", f"This function reads ADF data, not {info.engine} data"

    ret = Result()

    # set the calculation task at a higher level
    ret.task = info.input.task

    # the VibrationalAnalysis task does not produce adf.rkf files
    # in that case we end the reading here, since the following
    # variables do not apply
    if ret.task.lower() == "vibrationalanalysis":
        return ret

    reader_adf = cache.get(info.files["adf.rkf"])

    relativistic_type_map = {
        0: "None",
        1: "scalar Pauli",
        3: "scalar ZORA",  # scalar ZORA + MAPA
        4: "scalar ZORA + full pot.",
        5: "scalar ZORA + APA",
        6: "scalar X2C + MAPA",
        7: "scalar X2C ZORA + MAPA",
        11: "spin-orbit Pauli",
        13: "spin-orbit ZORA",  # spin-orbit ZORA + MAPA
        14: "spin-orbit ZORA + full pot.",
        15: "spin-orbit ZORA + APA",
        16: "spin-orbit X2C + MAPA",
        17: "spin-orbit X2C ZORA + MAPA",
    }
    # determine if calculation used relativistic corrections
    # if it did, variable 'escale' will be present in 'SFOs'
    # if it didnt, only variable 'energy' will be present
    ret.relativistic = ("SFOs", "escale") in reader_adf
    ret.relativistic_type = relativistic_type_map[reader_adf.read("General", "ioprel")]

    # determine if MOs are unrestricted or not
    # general, nspin is 1 for restricted and 2 for unrestricted calculations
    ret.unrestricted_mos = reader_adf.read("General", "nspin") == 2

    # determine if SFOs are unrestricted or not
    ret.unrestricted_sfos = reader_adf.read("General", "nspinf") == 2

    # get the symmetry group
    ret.symmetry.group = reader_adf.read("Geometry", "grouplabel").strip()

    # get the symmetry labels
    ret.symmetry.labels = reader_adf.read("Symmetry", "symlab").strip().split()

    # determine if the calculation used regions or not
    frag_order = reader_adf.read("Geometry", "fragment and atomtype index")
    frag_order = frag_order[: len(frag_order) // 2]
    ret.used_regions = max(frag_order) != len(frag_order)

    ret.charge = reader_adf.read("Molecule", "Charge")

    ret.spin_polarization = 0
    if ret.unrestricted_mos:
        nalpha = 0
        nbeta = 0
        for label in ret.symmetry.labels:
            nalpha += sum(ensure_list(reader_adf.read(label, "froc_A")))
            nbeta += sum(ensure_list(reader_adf.read(label, "froc_B")))
        ret.spin_polarization = nalpha - nbeta
    ret.multiplicity = 2 * ret.spin_polarization + 1

    return ret


# ------------------------------------------------------------- #
# ------------------------ Properties ------------------------- #
# ------------------------------------------------------------- #


# ----------------------- VDD charges ------------------------- #


def _read_vdd_charges(kf_reader: KFReader) -> arrays.Array1D[np.float64]:
    """Returns the VDD charges from the KFReader object."""
    vdd_scf: List[float] = ensure_list(kf_reader.read("Properties", "AtomCharge_SCF Voronoi"))  # type: ignore since plams does not include typing for KFReader. List[float] is returned
    vdd_ini: List[float] = ensure_list(kf_reader.read("Properties", "AtomCharge_initial Voronoi"))  # type: ignore since plams does not include typing for KFReader. List[float] is returned

    # VDD charges are scf - initial charges. Note, these are in units of electrons while most often these are denoted in mili-electrons
    return np.array([float((scf - ini)) for scf, ini in zip(vdd_scf, vdd_ini)])


def _read_vdd_charges_initial(kf_reader: KFReader) -> arrays.Array1D[np.float64]:
    """Returns the initial VDD charges from the KFReader object."""
    vdd_ini: List[float] = ensure_list(kf_reader.read("Properties", "AtomCharge_initial Voronoi"))  # type: ignore since plams does not include typing for KFReader. List[float] is returned
    return np.array(vdd_ini)


def _read_vdd_charges_SCF(kf_reader: KFReader) -> arrays.Array1D[np.float64]:
    """Returns the SCF VDD charges from the KFReader object."""
    vdd_scf: List[float] = ensure_list(kf_reader.read("Properties", "AtomCharge_SCF Voronoi"))  # type: ignore since plams does not include typing for KFReader. List[float] is returned
    return np.array(vdd_scf)


def _get_vdd_charges_per_irrep(results_type: KFReader) -> Dict[str, arrays.Array1D[np.float64]]:
    """Extracts the Voronoi Deformation Density charges from the fragment calculation sorted per irrep."""
    symlabels = str(results_type.read("Symmetry", "symlab")).split()  # split on whitespace

    # If there is only one irrep, there is no irrep decomposition
    if len(symlabels) == 1:
        return {}

    vdd_irrep = np.array(results_type.read("Properties", "Voronoi chrg per irrep"))
    n_atoms = int(results_type.read("Molecule", "nAtoms"))  # type: ignore since no static typing. Returns an int

    # NOTE: apparently, the irrep charges are minus the total VDD charges. That's why the minus sign in the second line below
    vdd_irrep = vdd_irrep[-len(symlabels) * n_atoms :]  # vdd_irrep = vdd_irrep.reshape((n_headers, len(symlabels), n_atoms)) # NOQA E203
    vdd_per_irrep = {irrep: -vdd_irrep[i * n_atoms : (i + 1) * n_atoms] for i, irrep in enumerate(symlabels)}  # NOQA E203
    return vdd_per_irrep


# ----------------------- Vibrations ------------------------- #


def _read_vibrations(reader: cache.TrackKFReader) -> Result:
    ret = Result()
    ret.number_of_modes = reader.read("Vibrations", "nNormalModes")
    ret.frequencies = ensure_list(reader.read("Vibrations", "Frequencies[cm-1]"))
    if ("Vibrations", "Intensities[km/mol]") in reader:
        ret.intensities = ensure_list(reader.read("Vibrations", "Intensities[km/mol]"))
    ret.number_of_imag_modes = len([freq for freq in ret.frequencies if freq < 0])
    ret.character = "minimum" if ret.number_of_imag_modes == 0 else "transitionstate"
    ret.modes = []
    for i in range(ret.number_of_modes):
        ret.modes.append(reader.read("Vibrations", f"NoWeightNormalMode({i+1})"))
    return ret


# def _read_excitations(info: Result):
    
def _read_excitations(reader: cache.TrackKFReader) -> Result:
    ret = Result()
    excitation_types = []
    symlab_exc = reader.read('Symmetry', 'symlab excitations').split()
    for section, variable in reader:
        if not section.startswith('Excitations'):
            continue

        _, exctyp, irrep = section.split()
        if (exctyp, irrep) in excitation_types:
            continue

        excitation_types.append((exctyp, irrep))

        ret[irrep][exctyp].number_of_excitations = reader.read(section, 'nr of excenergies')
        ret[irrep][exctyp].energies = np.array(reader.read(section, 'excenergies'))  # in Ha

        # values used to convert excitation photon energies to wavelengths
        c = 299_792_458e9  # nm/s
        h = 0.0367502 * 4.135_667_696e-15  # Ha s
        ret[irrep][exctyp].wavelengths = (h * c) / ret[irrep][exctyp].energies # in nm
        ret[irrep][exctyp].oscillator_strengths = np.array(reader.read(section, 'oscillator strengths'))  # in km mol
        ret[irrep][exctyp].transition_dipole_moments = np.array(reader.read(section, 'transition dipole moments')).reshape(ret[irrep][exctyp].number_of_excitations, 3)

        ret[irrep][exctyp].contributions = []
        ret[irrep][exctyp].from_MO = []
        ret[irrep][exctyp].to_MO = []
        ret[irrep][exctyp].from_MO_idx = []
        ret[irrep][exctyp].to_MO_idx = []
        ret[irrep][exctyp].from_MO_spin = []
        ret[irrep][exctyp].to_MO_spin = []
        ret[irrep][exctyp].from_MO_irrep = []
        ret[irrep][exctyp].to_MO_irrep = []

        for exc_index in range(1, ret[irrep][exctyp].number_of_excitations + 1):
            contr = ensure_list(reader.read(section, f'contr {exc_index}'))
            contr_idx = ensure_list(reader.read(section, f'contr index {exc_index}'))
            contr_spin = ensure_list(reader.read(section, f'contr spin {exc_index}'))
            is_unrestricted = 2 in contr_spin
            contr_irrep = ensure_list(reader.read(section, f'contr irep index {exc_index}'))
            ncontr = len(contr_idx) // 2 

            MO_names = []
            for idx, spin, irrep_idx in zip(contr_idx, contr_spin, contr_irrep):
                spin = {
                    1: 'A',
                    2: 'B'
                }[spin]
                if is_unrestricted:
                    MO_names.append(f'{idx}{symlab_exc[irrep_idx-1]}_{spin}')
                else:
                    MO_names.append(f'{idx}{symlab_exc[irrep_idx-1]}')

            ret[irrep][exctyp].contributions.append(contr)
            ret[irrep][exctyp].from_MO.append(MO_names[:ncontr])
            ret[irrep][exctyp].to_MO.append(MO_names[ncontr:])
            ret[irrep][exctyp].from_MO_idx.append(contr_idx[:ncontr])
            ret[irrep][exctyp].to_MO_idx.append(contr_idx[ncontr:])
            ret[irrep][exctyp].from_MO_spin.append(contr_spin[:ncontr])
            ret[irrep][exctyp].to_MO_spin.append(contr_spin[ncontr:])
            ret[irrep][exctyp].from_MO_irrep.append(contr_irrep[:ncontr])
            ret[irrep][exctyp].to_MO_irrep.append(contr_irrep[ncontr:])

    return ret


def get_properties(info: Result) -> Result:
    """Function to get properties from an ADF calculation.

    Args:
        info: Result object containing ADF properties.

    Returns:
        :Result object containing properties from the ADF calculation:

            - **energy.bond (float)** – bonding energy (|kcal/mol|).
            - **energy.elstat.total (float)** – total electrostatic potential (|kcal/mol|).
            - **energy.elstat.Vee (float)** – electron-electron repulsive term of the electrostatic potential (|kcal/mol|).
            - **energy.elstat.Ven (float)** – electron-nucleus attractive term of the electrostatic potential (|kcal/mol|).
            - **energy.elstat.Vnn (float)** – nucleus-nucleus repulsive term of the electrostatic potential (|kcal/mol|).
            - **energy.orbint.total (float)** – total orbital interaction energy containing contributions from each symmetry label and correction energy(|kcal/mol|).
            - **energy.orbint.{symmetry label} (float)** – orbital interaction energy from a specific symmetry label (|kcal/mol|).
            - **energy.orbint.correction (float)** - orbital interaction correction energy, the difference between the total and the sum of the symmetrized interaction energies (|kcal/mol|)
            - **energy.pauli.total (float)** – total Pauli repulsion energy (|kcal/mol|).
            - **energy.dispersion (float)** – total dispersion energy (|kcal/mol|).
            - **energy.gibbs (float)** – Gibb's free energy (|kcal/mol|). Only populated if vibrational modes were calculated.
            - **energy.enthalpy (float)** – enthalpy (|kcal/mol|). Only populated if vibrational modes were calculated.
            - **energy.nuclear_internal (float)** – nuclear internal energy (|kcal/mol|). Only populated if vibrational modes were calculated.
            - **vibrations.number_of_modes (int)** – number of vibrational modes for this molecule, 3N-5 for non-linear molecules and 3N-6 for linear molecules, where N is the number of atoms.
            - **vibrations.number_of_imag_modes (int)** – number of imaginary vibrational modes for this molecule.
            - **vibrations.frequencies (float)** – vibrational frequencies associated with the vibrational modes, sorted from low to high (|cm-1|).
            - **vibrations.intensities (float)** – vibrational intensities associated with the vibrational modes (|km/mol|).
            - **vibrations.modes (list[float])** – list of vibrational modes sorted from low frequency to high frequency.
            - **vibrations.character (str)** – Character of the molecule based on the number of imaginary vibrational modes. Can be "minimum" or "transition state".
            - **vdd.charges (nparray[float] (1D))** - 1D array of Voronoi Deformation Denisty (VDD) charges in [electrons], being the difference between the final (SCF) and initial VDD charges.
            - **vdd.charges.{symmetry label} (nparray[float] (1D))** - 1D array of Voronoi Deformation Denisty (VDD) charges in [electrons] per irrep.
            - **s2** - expectation value of the :math:`S^2` operator.
            - **s2_expected** - ideal expectation value of the :math:`S^2` operator. For restricted calculations this should always equal ``s2``.
            - **spin_contamination** - the amount of spin-contamination observed in this calculation. It is equal to (s2 - s2_expected) / (s2_expected). Ideally this value should be below 0.1.
            - **dipole_vector** - the dipole moment vector.
            - **dipole_moment** - the magnitude of the dipole moment vector.
            - **quadrupole_moment** - the quadrupole moment vector.
            - **dens_at_atom** - the electron density at each atom.
    """

    assert info.engine == "adf", f"This function reads ADF data, not {info.engine} data"

    ret = Result()

    if info.adf.task.lower() == "vibrationalanalysis":
        reader_ams = cache.get(info.files["ams.rkf"])
        ret.vibrations = _read_vibrations(reader_ams)
        return ret

    reader_adf = cache.get(info.files["adf.rkf"])

    # electronic excitation information
    if ("All excitations", "nr excitations") in reader_adf:
        ret.excitations = _read_excitations(reader_adf)

    # read energies (given in Ha in rkf files)
    ret.energy.bond = reader_adf.read("Energy", "Bond Energy") * constants.HA2KCALMOL

    # total electrostatic potential
    ret.energy.elstat.total = reader_adf.read("Energy", "elstat") * constants.HA2KCALMOL

    # we can further decompose elstat if it was enabled
    if info.files.out:
        with open(info.files.out) as output:
            lines = output.readlines()

        skip_next = -1
        for line in lines:
            if "Electrostatic Interaction Energies" in line:
                skip_next = 4
                continue
            if skip_next == 0:
                f1, f2, Vee, Ven, Vnn, total = line.strip().split()
                ret.energy.elstat.Vee = float(Vee) * constants.HA2KCALMOL
                ret.energy.elstat.Ven = float(Ven) * constants.HA2KCALMOL
                ret.energy.elstat.Vnn = float(Vnn) * constants.HA2KCALMOL
            skip_next -= 1


    # print(info.files)

    # read the total orbital interaction energy
    ret.energy.orbint.total = reader_adf.read("Energy", "Orb.Int. Total") * constants.HA2KCALMOL

    # to calculate the orbital interaction term:
    # the difference between the total and the sum of the symmetrized interaction energies should be calculated
    # therefore the correction is first set equal to the total orbital interaction.
    ret.energy.orbint.correction = ret.energy.orbint.total

    # looping over every symlabel, to get the energy per symmetry label
    for symlabel in info.adf.symmetry.labels:
        symlabel = symlabel.split(":")[0]
        ret.energy.orbint[symlabel] = reader_adf.read("Energy", f"Orb.Int. {symlabel}") * constants.HA2KCALMOL

        # the energy per symmetry label is abstracted from the "total orbital interaction"
        # obtaining the correction to the orbital interaction term
        ret.energy.orbint.correction -= ret.energy.orbint[symlabel]

    ret.energy.pauli.total = reader_adf.read("Energy", "Pauli Total") * constants.HA2KCALMOL
    ret.energy.dispersion = reader_adf.read("Energy", "Dispersion Energy") * constants.HA2KCALMOL

    if ("Thermodynamics", "Gibbs free Energy") in reader_adf:
        ret.energy.gibbs = reader_adf.read("Thermodynamics", "Gibbs free Energy") * constants.HA2KCALMOL
        ret.energy.enthalpy = reader_adf.read("Thermodynamics", "Enthalpy") * constants.HA2KCALMOL
        ret.energy.nuclear_internal = reader_adf.read("Thermodynamics", "Internal Energy total") * constants.HA2KCALMOL

    # vibrational information
    if ("Vibrations", "nNormalModes") in reader_adf:
        ret.vibrations = _read_vibrations(reader_adf)

    # read the Voronoi Deformation Charges Deformation (VDD) before and after SCF convergence (being "inital" and "SCF")
    try:
        ret.vdd.charges = _read_vdd_charges(reader_adf)
        ret.vdd.charges_initial = _read_vdd_charges_initial(reader_adf)
        ret.vdd.charges_SCF = _read_vdd_charges_SCF(reader_adf)
        ret.vdd.update(_get_vdd_charges_per_irrep(reader_adf))
    except KeyError:
        pass

    # read spin-squared operator info
    # the total spin
    S = info.adf.spin_polarization * 1 / 2
    ret.s2_expected = S * (S + 1)
    # this is the real expectation value
    if ("Properties", "S2calc") in reader_adf:
        ret.s2 = reader_adf.read("Properties", "S2calc")
    else:
        ret.s2 = 0

    # calculate the contamination
    # if S is 0 then we will get a divide by zero error, but spin-contamination should be 0
    if S != 0:
        ret.spin_contamination = (ret.s2 - ret.s2_expected) / (ret.s2_expected)
    else:
        ret.spin_contamination = 0

    ret.dipole_vector = reader_adf.read("Properties", "Dipole")
    ret.dipole_moment = np.linalg.norm(ret.dipole_vector)
    ret.quadrupole_moment = reader_adf.read("Properties", "Quadrupole")
    ret.dens_at_atom = ensure_list(reader_adf.read("Properties", "Electron Density at Nuclei"))

    return ret


def get_level_of_theory(info: Result) -> Result:
    """Function to get the level-of-theory from an input-file.

    Args:
        inp_path: Path to the input file. Can be a .run or .in file create for AMS

    Returns:
        :Dictionary containing information about the level-of-theory:

            - **summary (str)** - a summary string that gives the level-of-theory in a human-readable format.
            - **xc.functional (str)** - XC-functional used in the calculation.
            - **xc.category (str)** - category the XC-functional belongs to. E.g. GGA, MetaHybrid, etc ...
            - **xc.dispersion (str)** - the dispersion correction method used during the calculation.
            - **xc.summary (str)** - a summary string that gives the XC-functional information in a human-readable format.
            - **xc.empiricalScaling (str)** - which empirical scaling parameter was used. Useful for MP2 calculations.
            - **basis.type (str)** - the size/type of the basis-set.
            - **basis.core (str)** - the size of the frozen-core approximation.
            - **quality (str)** - the numerical quality setting.
    """
    sett = info.input
    ret = Result()
    # print(json.dumps(sett, indent=4))
    xc_categories = ["GGA", "LDA", "MetaGGA", "MetaHybrid", "Model", "LibXC", "DoubleHybrid", "Hybrid", "MP2", "HartreeFock"]
    ret.xc.functional = "VWN"
    ret.xc.category = "LDA"
    for cat in xc_categories:
        if cat.lower() in [key.lower() for key in sett.adf.xc]:
            ret.xc.functional = sett.adf.xc[cat]
            ret.xc.category = cat

    ret.basis.type = sett.adf.basis.type
    ret.basis.core = sett.adf.basis.core
    ret.quality = sett.adf.NumericalQuality or "Normal"

    ret.xc.dispersion = None
    if "dispersion" in [key.lower() for key in sett.adf.xc]:
        ret.xc.dispersion = " ".join(sett.adf.xc.dispersion.split())

    # the empirical scaling value is used for MP2 calculations
    ret.xc.empirical_scaling = None
    if "empiricalscaling" in [key.lower() for key in sett.adf.xc]:
        ret.xc.empiricalscaling = sett.adf.xc.empiricalscaling

    # MP2 and HF are a little bit different from the usual xc categories. They are not key-value pairs but only the key
    # we start building the ret.xc.summary string here already. This will contain the human-readable functional name
    if ret.xc.category == "MP2":
        ret.xc.summary = "MP2"
        if ret.xc.empiricalscaling:
            ret.xc.summary += f"-{ret.xc.empiricalscaling}"
    elif ret.xc.category == "HartreeFock":
        ret.xc.summary = "HF"
    else:
        ret.xc.summary = ret.xc.functional

    # If dispersion was used, we want to add it to the ret.xc.summary
    if ret.xc.dispersion:
        if ret.xc.dispersion.lower() == "grimme3":
            ret.xc.summary += "-D3"
        if ret.xc.dispersion.lower() == "grimme3 bjdamp":
            ret.xc.summary += "-D3(BJ)"
        if ret.xc.dispersion.lower() == "grimme4":
            ret.xc.summary += "-D4"
        if ret.xc.dispersion.lower() == "ddsc":
            ret.xc.summary += "-dDsC"
        if ret.xc.dispersion.lower() == "uff":
            ret.xc.summary += "-dUFF"
        if ret.xc.dispersion.lower() == "mbd":
            ret.xc.summary += "-MBD@rsSC"
        if ret.xc.dispersion.lower() == "default":
            ret.xc.summary += "-D"

    # ret.summary is simply the ret.xc.summary plus the basis set type
    ret.summary = f"{ret.xc.summary}/{ret.basis.type}"
    return ret

