from TCutility.results import Result
from TCutility import constants
import os
from scm import plams
import numpy as np


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
        try:
            with open(file) as f:
                lines = f.readlines()

            if any(['* O   R   C   A *' in line for line in lines]):
                ret.out = os.path.abspath(file)
        except:  # noqa
            pass

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
            _, coordinates, charge, multiplicity = line.split()[:4]
            if coordinates == 'xyz':
                ret.system.coordinate_system = 'cartesian'
            elif coordinates == 'int':
                ret.system.coordinate_system = 'internal'
            elif coordinates == 'xyzfile':
                ret.system.coordinate_system = 'cartesian'
                # ret.system.coordinate_file = 
                read_system = False
            ret.system.charge = charge
            ret.system.multiplicity = multiplicity
            continue

    if coordinates in ['xyz', 'int']:
        ret.system.molecule = plams.Molecule()
        for line in system_lines:
            ret.system.molecule.add_atom(plams.Atom(symbol=line.split()[0], coords=[float(x) for x in line.split()[1:4]]))

    info.task = 'SinglePoint'
    if 'optts' in [x.lower() for x in ret.main]:
        info.task = 'TransitionStateSearch'
    elif 'opt' in [x.lower() for x in ret.main]:
        info.task = 'GeometryOptimization'

    return ret



def get_level_of_theory(info: Result) -> Result:
    '''Function to get the level-of-theory from an input-file.

    Args:
        inp_path: Path to the input file. Can be a .run or .in file create for AMS

    Returns:
        :Dictionary containing information about the level-of-theory:
            
            - **summary (str)** - a summary string that gives the level-of-theory in a human-readable format.
            - **basis.type (str)** - the size/type of the basis-set.
            - **UsedQROs (bool)** - whether QROs were used.
    '''
    sett = info.input
    ret = Result()
    main = [x.lower() for x in sett.main]
    for method in ['MP2', 'CCSD', 'CCSD(T)', 'CCSDT']:
        if method.lower() in main:
            ret.method = method
            break

    for method in ['MP2', 'CCSD', 'CCSD(T)', 'CCSDT']:
        if method.lower() in main:
            ret.method = method
            break
    
    for bs in ['cc-pVSZ', 'cc-pVDZ', 'cc-pVTZ', 'cc-pVQZ', 'aug-cc-pVSZ', 'aug-cc-pVDZ', 'aug-cc-pVTZ', 'aug-cc-pVQZ']:
        if bs.lower() in main:
            ret.basis.type = bs

    if sett.sections.mdci.UseQROs and sett.sections.mdci.UseQROs.lower() == 'true':
        ret.UseQROs = True
    else:
        ret.UseQROs = False

    ret.summary = f'{"QRO-" if ret.UseQROs else ""}{method}/{ret.basis.type}'

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

    ret.engine = 'orca'
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
    ret = Result()
    start_reading = False
    start_reading_idx = 0
    freq_lines = []
    for i, line in enumerate(lines):
        if start_reading:
            if len(line) == 0 and (i - start_reading_idx) > 4:
                break
            if ':' in line:
                freq_lines.append(line)

        if 'VIBRATIONAL FREQUENCIES' in line:
            start_reading = True
            start_reading_idx = i

    nmodes = len(freq_lines)
    frequencies = [float(line.split()[1]) for line in freq_lines]
    nrotranslational = sum([freq == 0 for freq in frequencies])
    ret.frequencies = frequencies[nrotranslational:]
    ret.number_of_imag_modes = len([freq for freq in ret.frequencies if freq < 0])
    ret.character = 'minimum' if ret.number_of_imag_modes == 0 else 'transitionstate' if ret.number_of_imag_modes == 1 else f'saddlepoint({ret.number_of_imag_modes})'

    start_reading = False
    mode_lines = []
    for i, line in enumerate(lines):
        if 'NORMAL MODES' in line:
            start_reading = True
            continue

        if 'IR SPECTRUM' in line:
            start_reading = False
            break

        if start_reading:
            mode_lines.append(line)

    mode_lines = mode_lines[6:-3]
    mode_lines = [[float(x) for x in line.split()[1:]] for i, line in enumerate(mode_lines) if i % (nmodes + 1) != 0]

    nblocks = len(mode_lines)//nmodes
    blocks = []
    for block in range(nblocks):
        blocks.append(np.array(mode_lines[block * nmodes: (block + 1) * nmodes]))
    ret.modes = np.hstack(blocks).T.tolist()[nrotranslational:]

    start_reading = False
    int_lines = []
    for i, line in enumerate(lines):
        if 'IR SPECTRUM' in line:
            start_reading = True
            continue

        if 'The epsilon (eps) is given for a Dirac delta lineshape.' in line:
            start_reading = False
            break

        if start_reading:
            int_lines.append(line)

    ints = [float(line.split()[3]) for line in int_lines[5:-1]]
    ret.intensities = [0] * ret.number_of_imag_modes + ints
    return ret


def get_properties(info: Result) -> Result:
    ret = Result()

    with open(info.files.out) as out:
        lines = [line.strip() for line in out.readlines()]

    ret.vibrations = get_vibrations(lines)

    for line in lines:
        if 'FINAL SINGLE POINT ENERGY' in line:
            ret.energy.bond = float(line.split()[4]) * constants.HA2KCALMOL
            continue

        if 'E(0)' in line:
            ret.energy.HF = float(line.split()[-1]) * constants.HA2KCALMOL
            continue

        if 'Final correlation energy' in line:
            ret.energy.corr = float(line.split()[-1]) * constants.HA2KCALMOL
            continue

        if 'E(MP2)' in line:
            ret.energy.MP2 = float(line.split()[-1]) * constants.HA2KCALMOL + ret.energy.HF
            continue

        if 'E(CCSD) ' in line:
            ret.energy.CCSD = float(line.split()[-1]) * constants.HA2KCALMOL
            continue

        if 'E(CCSD(T))' in line:
            ret.energy.CCSD_T = float(line.split()[-1]) * constants.HA2KCALMOL
            continue

        if 'Final Gibbs free energy' in line:
            ret.energy.gibbs = float(line.split()[-2]) * constants.HA2KCALMOL
            continue

        if 'Total enthalpy' in line:
            ret.energy.enthalpy = float(line.split()[-2]) * constants.HA2KCALMOL
            continue

        if 'Final entropy term' in line:
            ret.energy.entropy = float(line.split()[-2])
            continue

        if 'T1 diagnostic' in line:
            ret.t1 = float(line.split()[3])
            continue

        if 'Expectation value of <S**2>' in line:
            ret.s2 = float(line.split()[-1])
            continue

        if 'Ideal value' in line:
            ret.s2_expected = float(line.split()[-1])
            continue

    return ret


if __name__ == '__main__':
    ret = get_info('/Users/yumanhordijk/Library/CloudStorage/OneDrive-VrijeUniversiteitAmsterdam/RadicalAdditionBenchmark/data/abinitio/P_C2H2_NH2/OPT_pVTZ')
    print(ret.molecule)
