from TCutility.results import Result
import os
from scm import plams

j = os.path.join


def get_calc_files(calc_dir: str) -> Result:
    '''Function that returns files relevant to AMS calculations stored in ``calc_dir``.

    Args:
        calc_dir: path pointing to the desired calculation

    Returns:
        Dictionary containing filenames and paths
    '''
    # collect all files in the current directory and subdirectories
    files = []
    for root, _, files_ in os.walk(calc_dir):
        files.extend([j(root, file) for file in files_])

    # parse the filenames
    ret = Result()
    ret.root = os.path.abspath(calc_dir)
    for file in files:
        with open(file) as f:
            lines = f.readlines()

        if any(['* O   R   C   A *' in line for line in lines]):
            ret.out = os.path.abspath(file)

    return ret


def get_version(info: Result) -> Result:
    ret = Result()
    with open(info.files.out) as out:
        for line in out.readlines():
            line = line.strip()
            if 'Program Version' not in line:
                continue
            version = line.split()[2]
            ret.full = version
            ret.major = version.split('.')[0]
            ret.minor = version.split('.')[1]
            ret.micro = version.split('.')[2]
            return ret


def get_input(info: Result) -> Result:
    ret = Result()
    with open(info.files.out) as out:
        start_reading = False
        lines = []
        for line in out.readlines():
            line = line.strip()
            if start_reading:
                lines.append(line)

            if 'INPUT FILE' in line:
                start_reading = True
                continue

            if '****END OF INPUT****' in line:
                break

    lines = [line.split('>')[1] for line in lines[2:-1] if line.split('>')[1].strip()]

    ret.main = []
    curr_section = None
    read_system = False
    system_lines = []
    for line in lines:
        line = line.strip()

        if line.startswith('!'):
            ret.main.extend(line.removeprefix('!').split())

        if curr_section:
            if line.lower() == 'end':
                curr_section = None
                continue

            var, val = line.split()
            ret.sections[curr_section][var] = val

        if line.startswith('%'):
            curr_section = line.split()[0][1:]
            if len(line.split()) == 2:
                ret.sections[curr_section] = line.split()[1]
                curr_section = None

        if read_system:
            if line == '*':
                read_system = False
                continue

            system_lines.append(line)

        if line.startswith('*'):
            read_system = True
            _, coordinates, charge, multiplicity = line.split()
            if coordinates == 'xyz':
                ret.system.coordinate_system = 'cartesian'
            elif coordinates == 'int':
                ret.system.coordinate_system = 'internal'
            ret.system.charge = charge
            ret.system.multiplicity = multiplicity
            continue

    ret.system.molecule = plams.Molecule()
    for line in system_lines:
        ret.system.molecule.add_atom(plams.Atom(symbol=line.split()[0], coords=[float(x) for x in line.split()[1:4]]))
    return ret


def get_calculation_status(info: Result) -> Result:
    ret = Result()
    ret.fatal = True
    ret.name = None
    ret.code = None
    ret.reasons = []

    if 'out' not in info.files.out:
        ret.reasons.append('Calculation status unknown')
        ret.name = 'UNKNOWN'
        ret.code = 'U'
        return ret

    with open(info.files.out) as out:
        lines = out.readlines()
        if any(['ORCA TERMINATED NORMALLY' in line for line in lines]):
            ret.fatal = False
            ret.name = 'SUCCESS'
            ret.code = 'S'
            return ret

    ret.name = 'FAILED'
    ret.code = 'F'
    return ret


def get_molecules(info: Result) -> Result:
    ret = Result()
    ret.input = info.input.system.molecule
    ret.number_of_atoms = len(ret.input.atoms)

    ret.output = None

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

        if 'THE OPTIMIZATION HAS CONVERGED' in line:
            look_for_coords = True

        if look_for_coords and 'CARTESIAN COORDINATES (ANGSTROEM)' in line:
            look_for_coords = False
            start_reading = True

    ret.output = plams.Molecule()
    for coord in coords[1:]:
        sym, x, y, z = coord.split()
        ret.output.add_atom(plams.Atom(symbol=sym, coords=[float(x), float(y), float(z)]))

    return ret


def get_info(calc_dir: str) -> Result:
    '''Function to read useful info about the calculation in ``calc_dir``. Returned information will depend on the type of file that is provided.

    Args:
        calc_dir: path pointing to the desired calculation.

    Returns:
        :Dictionary containing results about the calculation and AMS:

            - **version (Result)** – information about the AMS version used, see :func:`get_version`.
            - **engine (str)** – the engine that was used to perform the calculation, for example 'adf', 'dftb', ...
            - **status (Result)** – information about calculation status, see :func:`get_calculation_status`.
            - **molecule (Result)** – information about the input and output molecules and the molecular system in general, see :func:`get_molecules`.
    '''
    ret = Result()
    ret.files = get_calc_files(calc_dir)

    # store the input of the calculation
    ret.input = get_input(ret)

    # store the job id, which should be unique for the job

    # store information about the version of AMS
    ret.version = get_version(ret)

    # store the computation timings, only available in ams.rkf
    # ret.timing = get_timing(ret)

    # store the calculation status
    ret.status = get_calculation_status(ret)

    # check if this was a multijob
    # ret.is_multijob = False
    # if len([file for file in ret.files if file.endswith('.rkf')]) > 2:
    #     ret.is_multijob = True

    # # read molecules
    ret.molecule = get_molecules(ret)

    # # and history variables
    # ret.history = get_history(calc_dir)

    # cache.unload(ret.files['ams.rkf'])
    return ret


if __name__ == '__main__':
    ret = get_info('/Users/yumanhordijk/Library/CloudStorage/OneDrive-VrijeUniversiteitAmsterdam/RadicalAdditionBenchmark/data/abinitio/P_C2H2_NH2/OPT_pVTZ')
    print(ret.molecule)
