import os

from tcutility import molecule, pathfunc
from tcutility.results import Result

j = os.path.join

def convert(st):
    try:
        return int(st)
    except ValueError: #If you get a ValueError
        return float(st)

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
    files = sorted(files, key=pathfunc.path_depth, reverse=True)

    # parse the filenames
    ret = Result()
    ret.extra = []
    ret.root = os.path.abspath(calc_dir)
    for file in files:
        if file.endswith(".out") and not file.endswith("g98.out"):
            ret.out = os.path.abspath(file)
            continue
        if file.endswith("xtbopt.xyz"):
            ret.opt_out = os.path.abspath(file)
            continue
        if file.endswith("xtbopt.log"):
            ret.opt_history = os.path.abspath(file)
            continue
        if file.endswith("xtbscan.log"):
            ret.scan_out = os.path.abspath(file)
            continue
        if file.endswith("vibspectrum"):
            ret.vibspectrum = os.path.abspath(file)
            continue
        if file.endswith("hessian"):
            ret.hessian = os.path.abspath(file)
            continue
        if file.endswith('crest_conformers.xyz'):
            ret.conformers = os.path.abspath(file)
            continue
        if file.endswith('crest_rotamers.xyz'):
            ret.rotamers = os.path.abspath(file)
            continue
        if file.endswith('crest_best.xyz'):
            ret.best = os.path.abspath(file)
            continue
        ret.extra.append(os.path.abspath(file))

    return ret


def get_version(info: Result) -> Result:
    """Function to get the CREST version used in the calculation.

    Args:
        info: Result object containing CREST calculation settings.

    Returns:
        :Result object containing results about the CREST version:

            - **full (str)** – the full version string as written by CREST.
            - **major (str)** – major CREST version.
            - **minor (str)** – minor CREST version.
    """
    ret = Result()
    with open(info.files.out) as out:
        for line in out.readlines():
            line = line.strip()
            if "Version" not in line:
                continue
            version = line.split()[1][:-1]
            ret.full = version
            ret.major = version.split(".")[0]
            ret.minor = version.split(".")[1]
            ret.micro = ''
            return ret


def get_input(info: Result) -> Result:
    """Function that parses the input file for this CREST calculation.

    Args:
        info: Result object containing CREST calculation settings.

    Returns:
        :Result object containing information about the calculation input:

            - **main (list[str])** - the main inputs for the calculation. These are the lines that start with a "!".
            - **sections (Result)** - extra settings added to the calculation. These are the lines that start with a "%" and optionally end with "END" clause.
            - **system (Result)** - settings related to the molecular system. This includes charge, multiplicity and the coordinates.
            - **task (str)** - the task that was performed by the calculation, e.g. "SinglePoint", "TransitionStateSearch".
    """
    ret = Result()
    with open(info.files.out) as out:
        lines = out.readlines()
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith("Command line input:"):
                # next line contains the call
                call = lines[i+1].strip('$> ').split()
    ret.call = " ".join(call)
    ### TASK
    ret.coord_file = call[1]
    ### CHARGE
    ret.charge = 0
    for option in ["--charge", "-c"]:
        # check if we used the option in our call
        if option not in call:
            continue
        # read the next position in the call
        option_idx = call.index(option)
        ret.charge = convert(call[option_idx + 1])

    ### SPIN-POLARIZATION
    ret.spin_polarization = 0
    for option in ["--uhf", "-u"]:
        # check if we used the option in our call
        if option not in call:
            continue
        # read the next position in the call
        option_idx = call.index(option)
        ret.spin_polarization = convert(call[option_idx + 1])

    ### SOLVATION
    ret.solvent = None
    ret.solvation_model = None

    if "--alpb" in call:
        option_idx = call.index("--alpb")
        ret.solvent = call[option_idx + 1]
        ret.solvation_model = "ALPB"

    for option in ["-g", "--gbsa"]:
        if option not in call:
            continue
        option_idx = call.index(option)
        ret.solvent = call[option_idx + 1]
        ret.solvation_model = "GBSA"
    
    ### DETAILED INPUT
    ret.detailed = None
    if "--input" in call:
        ret.detailed = Result()
        option_idx = call.index("--input")
        inp_file = call[option_idx + 1]
        for file in info.files.extra:
            if file.endswith(inp_file):
                ret.detailed.file = file
                break

        with open(ret.detailed.file) as infile:
            content = infile.readlines()

        for line in content:
            line = line.strip()
            if line.startswith("$"):
                curr_section = line[1:]
                continue

            if ":" in line:
                key, val = line.split(":")
                ret.detailed[curr_section].setdefault(key, [])
                ret.detailed[curr_section][key].append(val.strip())

            elif "=" in line:
                key, val = line.split("=")
                ret.detailed[curr_section][key] = val.strip()

    ### MODEL HAMILTONIAN
    ret.model = "GFN2-xTB"
    if "--gfn" in call:
        option_idx = call.index("--gfn")
        version = call[option_idx + 1]
        ret.model = f"GFN{version}-xTB"

    if "--gfnff" in call:
        ret.model = "GFNFF"

    return ret


def get_calculation_status(calc_dir: str) -> Result:
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

    info = get_info(calc_dir)

    if "out" not in info.files:
        ret.reasons.append("Calculation status unknown")
        ret.name = "UNKNOWN"
        ret.code = "U"
        return ret

    with open(info.files.out) as out:
        lines = out.readlines()
        if any(["[WARNING] Runtime exception occurred" in line for line in lines]):
            ret.fatal = True
            ret.name = "FAILED"
            ret.code = "F"

            line_index = [i for i, line in enumerate(lines) if "[WARNING] Runtime exception occurred" in line][0]
            for line in lines[line_index + 1 :]:
                if "##########" in line:
                    break
                ret.reasons.append(line.strip())
            return ret

        if any(["CREST terminated normally." in line for line in lines]):
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
    ret.number_of_atoms = len(ret.input)
    ret.output = ret.input.copy()

    if "best" in info.files:
        ret.output = molecule.load(info.files.best)

    if "conformers" in info.files:
        with open(info.files.conformers) as ensemble:
            lines = ensemble.readlines()
            number_of_mols = len(lines)//(ret.number_of_atoms + 2)
            mol_lines = [lines[i*(ret.number_of_atoms + 2):(i+1)*(ret.number_of_atoms + 2)] for i in range(number_of_mols)]
            ret.conformers = [molecule.from_string("".join(mol_lines_)) for mol_lines_ in mol_lines]

    if "rotamers" in info.files:
        with open(info.files.rotamers) as ensemble:
            lines = ensemble.readlines()
            number_of_mols = len(lines)//(ret.number_of_atoms + 2)
            mol_lines = [lines[i*(ret.number_of_atoms + 2):(i+1)*(ret.number_of_atoms + 2)] for i in range(number_of_mols)]
            ret.rotamers = [molecule.from_string("".join(mol_lines_)) for mol_lines_ in mol_lines]

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

    ret.engine = "crest"
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


if __name__ == "__main__":
    from tcutility import log

    ret = get_info("/Users/yumanhordijk/PhD/Projects/RadicalAdditionWorkflow/calculations/preparation/radicals/NMe2")
    log.log(ret.files)
    print(ret.status)

    # ret = get_info("/Users/yumanhordijk/PhD/ganesh_project/calculations/AlCl3_xtb/scan_1")
    # print(ret)
