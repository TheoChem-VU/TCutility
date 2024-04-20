from tcutility.results import Result
from tcutility import constants, slurm
import os
from scm import plams
import numpy as np


j = os.path.join


def get_calc_files(calc_dir: str) -> Result:
    """Function that returns files relevant to AMS calculations stored in ``calc_dir``.

    Args:
        calc_dir: path pointing to the desired calculation

    Returns:
        Result object containing filenames and paths
    """
    # collect all files in the current directory and subdirectories
    files = []
    for root, _, files_ in os.walk(calc_dir):
        files.extend([j(root, file) for file in files_])

    # parse the filenames
    ret = Result()
    ret.root = os.path.abspath(calc_dir)
    for file in files:
        try:
            with open(file) as f:
                lines = f.readlines()

            if any(["* O   R   C   A *" in line for line in lines]):
                ret.out = os.path.abspath(file)
        except:  # noqa
            pass

    return ret


def get_version(info: Result) -> Result:
    """Function to get the ORCA version used in the calculation.

    Args:
        info: Result object containing ORCA calculation settings.

    Returns:
        :Result object containing results about the ORCA version:

            - **full (str)** – the full version string as written by ORCA.
            - **major (str)** – major ORCA version.
            - **minor (str)** – minor ORCA version.
            - **micro (str)** – micro ORCA version.
    """
    ret = Result()
    with open(info.files.out) as out:
        for line in out.readlines():
            line = line.strip()
            if "Program Version" not in line:
                continue
            version = line.split()[2]
            ret.full = version
            ret.major = version.split(".")[0]
            ret.minor = version.split(".")[1]
            ret.micro = version.split(".")[2]
            return ret


def get_input(info: Result) -> Result:
    """Function that parses the input file for this ORCA calculation.

    Args:
        info: Result object containing ORCA calculation settings.

    Returns:
        :Result object containing information about the calculation input:

            - **main (list[str])** - the main inputs for the calculation. These are the lines that start with a "!".
            - **sections (Result)** - extra settings added to the calculation. These are the lines that start with a "%" and optionally end with "END" clause.
            - **system (Result)** - settings related to the molecular system. This includes charge, multiplicity and the coordinates.
            - **task (str)** - the task that was performed by the calculation, e.g. "SinglePoint", "TransitionStateSearch".
    """
    ret = Result()
    with open(info.files.out) as out:
        start_reading = False
        lines = []
        for line in out.readlines():
            line = line.strip()
            if start_reading:
                lines.append(line)

            if "INPUT FILE" in line:
                start_reading = True
                continue

            if "****END OF INPUT****" in line:
                break

    lines = [line.split(">")[1] for line in lines[2:-1] if line.split(">")[1].strip()]

    ret.main = []
    curr_section = None
    read_system = False
    system_lines = []
    coordinates = None
    for line in lines:
        line = line.strip()

        if line.startswith("!"):
            ret.main.extend(line.strip("!").split())

        if curr_section:
            if line.lower() == "end":
                curr_section = None
                continue

            var, val = line.split()
            ret.sections[curr_section][var] = val

        if line.startswith("%"):
            curr_section = line.split()[0][1:]
            if len(line.split()) == 2:
                ret.sections[curr_section] = line.split()[1]
                curr_section = None

        if read_system:
            if line == "*":
                read_system = False
                continue

            system_lines.append(line)

        if line.startswith("*"):
            read_system = True
            _, coordinates, charge, multiplicity = line.split()[:4]
            if coordinates == "xyz":
                ret.system.coordinate_system = "cartesian"
            elif coordinates == "int":
                ret.system.coordinate_system = "internal"
            elif coordinates == "xyzfile":
                ret.system.coordinate_system = "cartesian"
                read_system = False
            ret.system.charge = charge
            ret.system.multiplicity = multiplicity
            continue

    if coordinates in ["xyz", "int"]:
        ret.system.molecule = plams.Molecule()
        for line in system_lines:
            line = line.replace(':', '')
            ret.system.molecule.add_atom(plams.Atom(symbol=line.split()[0], coords=[float(x) for x in line.split()[1:4]]))

    info.task = "SinglePoint"
    if "optts" in [x.lower() for x in ret.main]:
        info.task = "TransitionStateSearch"
    elif "opt" in [x.lower() for x in ret.main]:
        info.task = "GeometryOptimization"

    return ret


def get_level_of_theory(info: Result) -> Result:
    """Function to get the level-of-theory from an input-file.

    Args:
        info: Result object containing ORCA calculation settings.

    Returns:
        :Result object containing information about the level-of-theory:

            - **summary (str)** - a summary string that gives the level-of-theory in a human-readable format.
            - **basis.type (str)** - the size/type of the basis-set.
            - **UsedQROs (bool)** - whether QROs were used.
    """
    sett = info.input
    ret = Result()
    main = [x.lower() for x in sett.main]
    ret.method = 'HF'
    for method in ["MP2", "CCSD", "CCSD(T)", "CCSDT"]:
        if method.lower() in main:
            ret.method = method
            break

    ret.basis.type = 'def2-SVP'
    for bs in ["cc-pVDZ", "cc-pVTZ", "cc-pVQZ", "cc-pV5Z", "aug-cc-pVDZ", "aug-cc-pVTZ", "aug-cc-pVQZ", "aug-cc-pV5Z"]:
        if bs.lower() in main:
            ret.basis.type = bs

    used_qros = sett.sections.mdci.UseQROs and sett.sections.mdci.UseQROs.lower() == "true"
    ret.summary = f'{"QRO-" if used_qros else ""}{method}/{ret.basis.type}'

    return ret


def get_calc_settings(info: Result) -> Result:
    """Function to read calculation settings for an ORCA calculation.

    Args:
        info: Result object containing ORCA calculation settings.

    Returns:
        :Result object containing properties from the ORCA calculation:

            - **task (str)** – the task that was set for the calculation.
            - **unrestricted (bool)** – whether or not the wavefunction is treated in an unrestricted manner.
            - **used_qros (bool)** - whether the reference wavefunction is transformed to a QRO wavefunction.
            - **frequencies (bool)** - whether vibrational frequencies were calculated.
            - **charge (int)** - the charge of the molecular system.
            - **spin_polarization (int)** - the spin-polarization of the molecular system.
            - **multiplicity (int)** - the multiplicity of the molecular system.
    """

    assert info.engine == "orca", f"This function reads ORCA data, not {info.engine} data"

    ret = Result()

    # set the calculation task at a higher level
    ret.task = info.input.task

    main = [x.lower() for x in info.input.main]
    # determine if the wavefunction are unrestricted or not
    ret.unrestricted = any(tag in main for tag in ["uhf", "uno"])
    ret.used_qros = info.input.sections.mdci.UseQROs and info.input.sections.mdci.UseQROs.lower() == "true"
    ret.frequencies = "freq" in main
    ret.charge = int(info.input.system.charge)
    ret.spin_polarization = int(info.input.system.multiplicity) - 1
    ret.multiplicity = int(info.input.system.multiplicity)
    return ret


def get_calculation_status(info: Result) -> Result:
    """Function that returns the status of the ORCA calculation described in reader. In case of non-succes it will also give possible reasons for the errors/warnings.

    Args:
        info: Result object containing ORCA calculation information.

    Returns:
        :Result object containing information about the calculation status:

            - **fatal (bool)** – True if calculation cannot be analysed correctly, False otherwise
            - **reasons (list[str])** – list of reasons to explain the status, they can be errors, warnings, etc.
            - **name (str)** – calculation status written as a string, one of ("SUCCESS", "RUNNING", "UNKNOWN", "SUCCESS(W)", "FAILED")
            - **code (str)** – calculation status written as a single character, one of ("S", "R", "U", "W" "F")
    """
    ret = Result()
    ret.fatal = True
    ret.name = None
    ret.code = None
    ret.reasons = []

    # if we do not have an output file the calculation failed
    if "out" not in info.files.out:
        ret.reasons.append("Calculation status unknown")
        ret.name = "UNKNOWN"
        ret.code = "U"
        return ret

    # try to read if the calculation succeeded
    with open(info.files.out) as out:
        lines = out.readlines()
        if any(["ORCA TERMINATED NORMALLY" in line for line in lines]):
            ret.fatal = False
            ret.name = "SUCCESS"
            ret.code = "S"
            return ret

    # if it didnt we default to failed
    ret.name = "FAILED"
    ret.code = "F"

    # otherwise we check if the job is being managed by slurm
    if not slurm.workdir_info(os.path.abspath(info.files.root)):
        return ret

    # get the statuscode from the workdir
    state = slurm.workdir_info(os.path.abspath(info.files.root)).statuscode
    state_name = {
        'CG': 'COMPLETING',
        'CF': 'CONFIGURING',
        'PD': 'PENDING',
        'R': 'RUNNING'
    }.get(state, 'UNKNOWN')

    ret.fatal = False
    ret.name = state_name
    ret.code = state
    ret.reasons = []

    return ret


def get_molecules(info: Result) -> Result:
    """Function that returns information about the molecules for this calculation.

    Args:
        info: Result object containing ORCA calculation information.

    Returns:
        :Result object containing properties from the ORCA calculation:

            - **input (plams.Molecule)** - the input molecule for this calculation.
            - **output (plams.Molecule)** - the output molecule for this calculation, for example the optimized structure after a geometry optimization.
            - **number_of_atoms (int)** - the number of atoms in the molecular system.
    """
    ret = Result()
    ret.input = info.input.system.molecule
    ret.number_of_atoms = len(ret.input.atoms)

    with open(info.files.out) as out:
        lines = out.readlines()
        lines = [line.strip() for line in lines]

    start_reading = False
    look_for_coords = False
    coords = []
    for line in lines:
        if start_reading:
            if len(line) == 0:
                start_reading = False
                break

            coords.append(line)

        if "THE OPTIMIZATION HAS CONVERGED" in line:
            look_for_coords = True

        if look_for_coords and "CARTESIAN COORDINATES (ANGSTROEM)" in line:
            look_for_coords = False
            start_reading = True

    ret.output = plams.Molecule()
    for coord in coords[1:]:
        sym, x, y, z = coord.split()
        ret.output.add_atom(plams.Atom(symbol=sym, coords=[float(x), float(y), float(z)]))

    if len(ret.output.atoms) == 0:
        ret.output = ret.input.copy()
    return ret


def get_info(calc_dir: str) -> Result:
    """Function to read useful info about the calculation in ``calc_dir``. Returned information will depend on the type of file that is provided.

    Args:
        calc_dir: path pointing to the desired calculation.

    Returns:
        :Result object containing results about the calculation and AMS:

            - **version (Result)** – information about the AMS version used, see :func:`get_version`.
            - **files (Result)** - paths to files that are important for this calculation.
            - **input (Result)** - information about the input of this calculation, see :func:`get_input`.
            - **level (Result)** - information about the level of theory used for this calculation, see :func:`get_level_of_theory`.
            - **engine (str)** – the engine that was used to perform the calculation, for example 'adf', 'dftb', ...
            - **status (Result)** – information about calculation status, see :func:`get_calculation_status`.
            - **molecule (Result)** – information about the input and output molecules and the molecular system in general, see :func:`get_molecules`.
    """
    ret = Result()

    ret.engine = "orca"
    ret.files = get_calc_files(calc_dir)

    # store the input of the calculation
    ret.input = get_input(ret)

    ret.level = get_level_of_theory(ret)

    # store information about the version of AMS
    ret.version = get_version(ret)

    # store the calculation status
    ret.status = get_calculation_status(ret)

    # read molecules
    ret.molecule = get_molecules(ret)

    return ret


def get_vibrations(lines):
    """Function to read vibrational data of an ORCA calculation.

    Args:
        lines: Lines in the output file of the ORCA calculation.

    Returns:
        :Result object containing vibrational properties from the ORCA calculation:

            - **number_of_modes (int)** – number of vibrational modes for this molecule, 3N-5 for non-linear molecules and 3N-6 for linear molecules, where N is the number of atoms.
            - **number_of_imaginary_modes (int)** – number of imaginary vibrational modes for this molecule.
            - **frequencies (list[float])** – vibrational frequencies associated with the vibrational modes, sorted from low to high (|cm-1|).
            - **intensities (list[float])** – vibrational intensities associated with the vibrational modes (|km/mol|). In ORCA, intensities of imaginary modes are set to 0.
            - **modes (list[float])** – list of vibrational modes sorted from low frequency to high frequency.
            - **character (str)** – the PES character of the molecular system. Either "minimum", "transitionstate" or "saddlepoint(n_imag)", for 0, 1, n_imag number of imaginary frequencies.
    """
    ret = Result()
    start_reading = False
    start_reading_idx = 0
    freq_lines = []
    for i, line in enumerate(lines):
        if start_reading:
            if len(line) == 0 and (i - start_reading_idx) > 4:
                break
            if ":" in line:
                freq_lines.append(line)

        if "VIBRATIONAL FREQUENCIES" in line:
            start_reading = True
            start_reading_idx = i

    ret.number_of_modes = len(freq_lines)
    frequencies = [float(line.split()[1]) for line in freq_lines]
    nrotranslational = sum([freq == 0 for freq in frequencies])
    ret.frequencies = frequencies[nrotranslational:]
    ret.number_of_imaginary_modes = len([freq for freq in ret.frequencies if freq < 0])
    ret.character = "minimum" if ret.number_of_imaginary_modes == 0 else "transitionstate" if ret.number_of_imaginary_modes == 1 else f"saddlepoint({ret.number_of_imaginary_modes})"

    start_reading = False
    mode_lines = []
    for i, line in enumerate(lines):
        if "NORMAL MODES" in line:
            start_reading = True
            continue

        if "IR SPECTRUM" in line:
            start_reading = False
            break

        if start_reading:
            mode_lines.append(line)

    mode_lines = mode_lines[6:-3]
    mode_lines = [[float(x) for x in line.split()[1:]] for i, line in enumerate(mode_lines) if i % (ret.number_of_modes + 1) != 0]

    nblocks = len(mode_lines) // ret.number_of_modes
    blocks = []
    for block in range(nblocks):
        blocks.append(np.array(mode_lines[block * ret.number_of_modes : (block + 1) * ret.number_of_modes]))
    ret.modes = np.hstack(blocks).T.tolist()[nrotranslational:]

    start_reading = False
    int_lines = []
    for i, line in enumerate(lines):
        if "IR SPECTRUM" in line:
            start_reading = True
            continue

        if "The epsilon (eps) is given for a Dirac delta lineshape." in line:
            start_reading = False
            break

        if start_reading:
            int_lines.append(line)

    ints = [float(line.split()[3]) for line in int_lines[5:-1]]
    ret.intensities = [0] * ret.number_of_imaginary_modes + ints
    return ret


def get_properties(info: Result) -> Result:
    """Function to get properties from an ORCA calculation.

    Args:
        info: Result object containing ORCA properties.

    Returns:
        :Result object containing properties from the ORCA calculation:

            - **energy.bond (float)** – total bonding energy (|kcal/mol|).
            - **energy.enthalpy (float)** – enthalpy (|kcal/mol|). Only obtained if vibrational modes were calculated.
            - **energy.entropy (float)** – entropy (|kcal/mol|). Only obtained if vibrational modes were calculated.
            - **energy.gibbs (float)** – Gibb's free energy (|kcal/mol|). Only obtained if vibrational modes were calculated.
            - **energy.[method] (float)** - total energy (|kcal/mol|) at a certain level (HF, MP2, CCSD, ...). This is the sum of energy.HF and energy.[method]_corr.
            - **energy.[method]_corr (float)** - electron correlation energy (|kcal/mol|) at a certain level (HF, MP2, CCSD, ...).
            - **vibrations.number_of_modes (int)** – number of vibrational modes for this molecule, 3N-5 for non-linear molecules and 3N-6 for linear molecules, where N is the number of atoms.
            - **vibrations.number_of_imaginary_modes (int)** – number of imaginary vibrational modes for this molecule.
            - **vibrations.frequencies (list[float])** – vibrational frequencies associated with the vibrational modes, sorted from low to high (|cm-1|).
            - **vibrations.intensities (list[float])** – vibrational intensities associated with the vibrational modes (|km/mol|). In ORCA, intensities of imaginary modes are set to 0.
            - **vibrations.modes (list[float])** – list of vibrational modes sorted from low frequency to high frequency.
            - **vibrations.character (str)** – the PES character of the molecular system. Either "minimum", "transitionstate" or "saddlepoint(n_imag)", for 0, 1, n_imag number of imaginary frequencies.
            - **t1** - T1 diagnostic for the highest level of correlation chosen. Used to check the validity of the reference wavefunction.
            - **s2** - expectation value of the :math:`S^2` operator.
            - **s2_expected** - ideal expectation value of the :math:`S^2` operator.
            - **spin_contamination** - the amount of spin-contamination observed in this calculation. It is equal to (s2 - s2_expected) / (s2_expected). Ideally this value should be below 0.1.
    """
    ret = Result()

    with open(info.files.out) as out:
        lines = [line.strip() for line in out.readlines()]

    if info.orca.frequencies:
        ret.vibrations = get_vibrations(lines)

    # read some important info about the calculation
    for line in lines:
        if "FINAL SINGLE POINT ENERGY" in line:
            ret.energy.bond = float(line.split()[4]) * constants.HA2KCALMOL
            continue

        if "E(0)" in line:
            ret.energy.HF = float(line.split()[-1]) * constants.HA2KCALMOL
            continue

        if "Final correlation energy" in line:
            ret.energy.corr = float(line.split()[-1]) * constants.HA2KCALMOL
            continue

        if "E(MP2)" in line:
            ret.energy.MP2 = float(line.split()[-1]) * constants.HA2KCALMOL + ret.energy.HF
            ret.energy.MP2_corr = float(line.split()[-1]) * constants.HA2KCALMOL
            continue

        if "E(CCSD) " in line:
            ret.energy.CCSD = float(line.split()[-1]) * constants.HA2KCALMOL
            ret.energy.CCSD_corr = float(line.split()[-1]) * constants.HA2KCALMOL - ret.energy.HF
            continue

        if "E(CCSD(T))" in line:
            ret.energy.CCSD_T = float(line.split()[-1]) * constants.HA2KCALMOL
            ret.energy.CCSD_T_corr = float(line.split()[-1]) * constants.HA2KCALMOL - ret.energy.HF
            continue

        if "Final Gibbs free energy" in line:
            ret.energy.gibbs = float(line.split()[-2]) * constants.HA2KCALMOL
            continue

        if "Total enthalpy" in line:
            ret.energy.enthalpy = float(line.split()[-2]) * constants.HA2KCALMOL
            continue

        if "Final entropy term" in line:
            ret.energy.entropy = float(line.split()[-2])
            continue

        if "T1 diagnostic" in line:
            ret.t1 = float(line.split()[3])
            continue

        if "Expectation value of <S**2>" in line:
            ret.s2 = float(line.split()[-1])
            continue

        if "Ideal value" in line:
            ret.s2_expected = float(line.split()[-1])
            continue

    if ret.s2 and ret.s2_expected:
        ret.spin_contamination = (ret.s2 - ret.s2_expected) / ret.s2_expected

    return ret


if __name__ == "__main__":
    # ret = get_info("/Users/yumanhordijk/Library/CloudStorage/OneDrive-VrijeUniversiteitAmsterdam/RadicalAdditionBenchmark/data/abinitio/P_C2H2_NH2/OPT_pVTZ")
    # print(ret.molecule)

    ret = get_info('/Users/yumanhordijk/Library/CloudStorage/OneDrive-VrijeUniversiteitAmsterdam/RadicalAdditionBenchmark2/data/SP_CCSDpT_augCCpVQZ')
    print(ret.input)
    prop = get_properties(ret)
    # print(ret)
