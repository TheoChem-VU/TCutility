from tcutility.results import Result
from tcutility import constants, molecule
import os
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
    ret.extra = []
    ret.root = os.path.abspath(calc_dir)
    for file in files:
        if file.endswith('.out') and not file.endswith('g98.out'):
            ret.out = os.path.abspath(file)
            continue
        if file.endswith('xtbopt.xyz'):
            ret.opt_out = os.path.abspath(file)
            continue
        if file.endswith('xtbopt.log'):
            ret.opt_history = os.path.abspath(file)
            continue
        if file.endswith('xtbscan.log'):
            ret.scan_out = os.path.abspath(file)
            continue
        if file.endswith('vibspectrum'):
            ret.vibspectrum = os.path.abspath(file)
            continue
        if file.endswith('hessian'):
            ret.hessian = os.path.abspath(file)
            continue

        ret.extra.append(os.path.abspath(file))

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
            if "* xtb version" not in line:
                continue
            version = line.split()[3]
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
        for line in out.readlines():
            line = line.strip()
            if line.startswith('program call'):
                call = line.split(':')[1].strip().split()
            if line.startswith('coordinate file'):
                ret.coord_file = line.split(':')[1].strip()

    ret.call = " ".join(call)

    ### TASK
    ret.task = 'SinglePoint'
    for option in ['--opt', '--ohess']:
        # check if we used the option in our call
        if option not in call:
            continue

        # if we used it we did a geo-opt
        ret.task = 'GeometrOptimization'
        # check if we did a PESScan, it also requires using the --opt option
        if 'scan_out' in info.files:
            ret.task = 'PESScan'

        # check if we gave convergence criteria
        ret.geometry_convergence = 'Normal'
        option_idx = call.index(option)
        if not call[option_idx + 1].startswith('-'):
            ret.geometry_convergence = call[option_idx + 1]

    ### CHARGE
    ret.charge = 0
    for option in ['--charge', '-c']:
        # check if we used the option in our call
        if option not in call:
            continue
        # read the next position in the call
        option_idx = call.index(option)
        ret.charge = int(call[option_idx + 1])

    ### SPIN-POLARIZATION
    ret.spin_polarization = 0
    for option in ['--uhf', '-u']:
        # check if we used the option in our call
        if option not in call:
            continue
        # read the next position in the call
        option_idx = call.index(option)
        ret.spin_polarization = int(call[option_idx + 1])

    ### SOLVATION
    ret.solvent = None
    ret.solvation_model = None

    if '--alpb' in call:
        option_idx = call.index('--alpb')
        ret.solvent = call[option_idx + 1]
        ret.solvation_model = 'ALPB'

    for option in ['-g', '--gbsa']:
        if option not in call:
            continue
        option_idx = call.index(option)
        ret.solvent = call[option_idx + 1]
        ret.solvation_model = 'GBSA'

    ### DETAILED INPUT
    ret.detailed = None
    if '--input' in call:
        ret.detailed = Result()
        option_idx = call.index('--input')
        inp_file = call[option_idx + 1]
        for file in info.files.extra:
            if file.endswith(inp_file):
                ret.detailed.file = file
                break

        with open(ret.detailed.file) as infile:
            content = infile.readlines()

        for line in content:
            line = line.strip()
            if line.startswith('$'):
                curr_section = line[1:]
                continue

            if ':' in line:
                key, val = line.split(':')
                ret.detailed[curr_section].setdefault(key, [])
                ret.detailed[curr_section][key].append(val.strip())

            elif '=' in line:
                key, val = line.split('=')
                ret.detailed[curr_section][key] = val.strip()

    ### MODEL HAMILTONIAN
    ret.model = 'GFN2-xTB'
    if '--gfn' in call:
        option_idx = call.index('--gfn')
        version = call[option_idx + 1]
        ret.model = f'GFN{version}-xTB'

    if '--gfnff' in call:
        ret.model = 'GFNFF'

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

    if "out" not in info.files:
        ret.reasons.append("Calculation status unknown")
        ret.name = "UNKNOWN"
        ret.code = "U"
        return ret

    with open(info.files.out) as out:
        lines = out.readlines()
        if any(['[WARNING] Runtime exception occurred' in line for line in lines]):
            ret.fatal = True
            ret.name = "FAILED"
            ret.code = "F"

            line_index = [i for i, line in enumerate(lines) if '[WARNING] Runtime exception occurred' in line][0]
            for line in lines[line_index + 1:]:
                if '##########' in line:
                    break
                ret.reasons.append(line.strip())
            return ret

        if any(["* finished run" in line for line in lines]):
            ret.fatal = False
            ret.name = "SUCCESS"
            ret.code = "S"
            return ret

    ret.name = "FAILED"
    ret.code = "F"
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
    for file in info.files.extra:
        if file.endswith(info.input.coord_file):
            coord_file = file
            break

    ret.input = molecule.load(coord_file)
    ret.output = ret.input.copy()

    if 'opt_out' in info.files:
        ret.output = molecule.load(info.files.opt_out)

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

    ret.engine = "xtb"
    ret.files = get_calc_files(calc_dir)

    # store the input of the calculation
    ret.input = get_input(ret)

    # store information about the version of AMS
    ret.version = get_version(ret)

    # # store the calculation status
    ret.status = get_calculation_status(ret)

    # # read molecules
    ret.molecule = get_molecules(ret)

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

    # read some important info about the calculation
    for line in lines:
        if "TOTAL ENERGY" in line:
            ret.energy.bond = float(line.split()[3]) * constants.HA2KCALMOL
            continue

        if "TOTAL FREE ENERGY" in line:
            ret.energy.gibbs = float(line.split()[4]) * constants.HA2KCALMOL
            continue

        if "TOTAL ENTHALPY" in line:
            ret.energy.enthalpy = float(line.split()[3]) * constants.HA2KCALMOL
            continue

        if "# frequencies" in line:
            ret.vibrations.number_of_modes = int(line.split()[3])
            continue

        if "# imaginary freq." in line:
            ret.vibrations.number_of_imaginary_modes = int(line.split()[4])
            continue

        if 'vibrational frequencies' in line:
            ret.vibrations.frequencies = []
            continue

        if 'eigval :' in line:
            ret.vibrations.frequencies.extend([float(freq) for freq in line.split()[2:]])

    if ret.vibrations.frequencies:
        # get the number of the first vibrational mode, so without the translations and rotations
        first_mode = len(ret.vibrations.frequencies) - ret.vibrations.number_of_modes + 1
        # we have to remove the first 5 or 6 frequencies, because they are translation+rotation
        ret.vibrations.frequencies = ret.vibrations.frequencies[first_mode - 1:]

        # read in the vibspectrum file to get the vibrational intensities:
        ret.vibrations.intensities = []
        if info.files.vibspectrum:
            with open(info.files.vibspectrum) as spec:
                for line in spec.readlines()[3:-1]:
                    if line.startswith('$'):
                        continue

                    if int(line.split()[0]) < first_mode:
                        continue

                    ret.vibrations.intensities.append(float(line.split()[3]))

        # read in the hessian file to get the normal modes:
        if info.files.hessian:
            hessian = []
            with open(info.files.hessian) as hess:
                for line in hess.readlines()[1:]:
                    hessian.extend([float(x) for x in line.split()])

            # number of modes:
            N = int(np.sqrt(len(hessian)))
            # square hessian:
            H = np.reshape(hessian, (N, N))

            # get the atomic masses
            mol = molecule.load(info.files.opt_out)
            masses = np.atleast_2d([atom.mass for atom in mol.atoms for _ in range(3)])

            # make the reduced mass matrix
            mu = np.sqrt(masses * masses.T)
            # and reduced mass Hessian
            F = H / mu

            # diagonalize it to get frequencies and modes
            freqs, modes = np.linalg.eigh(F)
            # print(modes)

            # from yviewer import viewer
            # mol.guess_bonds()
            # viewer.show(mol, molinfo=[{'normalmode': modes[0].reshape(-1, 3)}])

    return ret


if __name__ == "__main__":
    from tcutility import log

    ret = get_info("/Users/yumanhordijk/PhD/ganesh_project/calculations/AlCl3_xtb/opt_1")
    log.log(ret.files)
    props = get_properties(ret)
    print(props)

    # ret = get_info("/Users/yumanhordijk/PhD/ganesh_project/calculations/AlCl3_xtb/scan_1")
    # print(ret)
