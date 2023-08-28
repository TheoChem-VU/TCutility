"""This module provides basic and general information about calculations done using AMS given a calculation directory. 
This includes information about the engine used (ADF, DFTB, BAND, ...), general information such as timings, files, status of the calculation, ... 
This information is used in further analysis programs.
"""

import numpy as np
from scm import plams
from TCutility.results import cache, Result
import os
from datetime import datetime

j = os.path.join


def get_calc_files(calc_dir: str) -> dict:
    '''Function that returns files relevant to AMS calculations stored in calc_dir.

    Args:
        calc_dir: path pointing to the desired calculation

    Returns:
        Dictionary containing filenames and paths
    '''
    # collect all files in the current directory and subdirectories
    files = []
    for root, _, files_ in os.walk(calc_dir):
        # some results are stored in dirs called {name}.results, if the calculations uses fragments there will be additional dirs called
        # {name}.{fragname}.results, which do not contain new information as the required info is copied over to {name}.results. Therefore
        # we should skip the fragment directories 
        if os.path.split(root)[1].endswith('.results') and len(os.path.split(root)[1].split('.')) > 2:
            continue

        # we only need the rkf files in the .results directories
        if root.endswith('.rkf') and '.results' not in root:
            continue

        # opened files end in ~ and should be ignored
        if root.endswith('~'):
            continue

        # t21 files for specific atoms are not usefull and should be ignored
        if 't21.' in root:
            continue

        # if a calculation is running or did not finish correctly there might be tmp. dirs, which should be ignored
        if os.path.split(root)[1].startswith('tmp.'):
            continue

        # the rest can all be stored
        files.extend([j(root, file) for file in files_])

    # parse the filenames
    ret = {}
    ret['root'] = os.path.abspath(calc_dir)
    for file in files:
        # rkf files are either called /{program}.rkf, or /{name}.{program}.rkf, so we must parse them in a special way
        if file.endswith('.rkf'):
            f = os.path.split(file)[1]
            parts = f.split('.')
            f = f'{parts[-2]}.rkf'
            ret[f] = os.path.abspath(file)

        # logfiles are generally called either {name}.log or {name}.logfile
        if file.endswith('.logfile') or file.endswith('.log') or file.endswith('.err'):
            f = os.path.split(file)[1]
            parts = f.split('.')
            f = '.'.join(parts[1:]).replace('logfile', 'log')
            ret[f] = os.path.abspath(file)

    return ret


def get_ams_version(calc_dir: str) -> Result:
    '''Function to get the AMS version used in the calculation.

    Args:
        calc_dir: path pointing to the desired calculation.

    Returns:
        dict: Dictionary containing results about the AMS version:

            - **string (str)** – the full version string as written by SCM.
            - **major (str)** – major AMS version, should correspond to the year of release.
            - **minor (str)** – minor AMS version.
            - **micro (str)** – micro AMS version, should correspond to the internal revision number.
            - **date (datetime.datetime)** – date the AMS version was released.
    '''
    ret = Result()
    files = get_calc_files(calc_dir)
    reader_ams = cache.get(files['ams.rkf'])

    # store information about the version of AMS
    ret.string = reader_ams.read('General', 'release')
    # decompose the version string
    ret.major = ret.string.split('.')[0]
    ret.minor = ret.string.split()[0].split('.')[1]
    ret.micro = ret.string.split()[1]
    ret.date = datetime.strptime(ret.string.split()[-1][1:-1], '%Y-%m-%d')

    return ret


def get_timing(calc_dir: str) -> Result:
    '''Function to get the timings from the calculation.

    Args:
        calc_dir: path pointing to the desired calculation.

    Returns:
        dict: Dictionary containing results about the timings:

            - **cpu (float)** – time spent performing calculations on the cpu.
            - **sys (float)** – time spent by the system (file IO, process creation/destruction, etc ...).
            - **total (float)** – total time spent by AMS on the calculation, can be larger than the sum of cpu and sys.
    '''
    ret = Result()
    files = get_calc_files(calc_dir)
    reader_ams = cache.get(files['ams.rkf'])

    ret.cpu = reader_ams.read('General', 'CPUTime') if ('General', 'CPUTime') in reader_ams else None
    ret.sys = reader_ams.read('General', 'SysTime') if ('General', 'SysTime') in reader_ams else None
    ret.total = reader_ams.read('General', 'ElapsedTime') if ('General', 'ElapsedTime') in reader_ams else None

    return ret


def get_ams_info(calc_dir: str) -> Result:
    '''Function to read useful info about the calculation in calc_dir. Returned information will depend on the type of file that is provided.

    Args:
        calc_dir: path pointing to the desired calculation.

    Returns:
        dict: Dictionary containing results about the calculation and AMS:

            - **ret.ams_version (dict)** – information about the AMS version used, includes ``string`` the full version string and ``major``, ``minor``, ``micro``, and ``date`` 
                which is the decomposed version.
            - **ret.engine (str)** – the engine that was used to perform the calculation.
            - **ret.job_id (str)** - the ID of the job, can be used to check if two calculations are the same. Might also be used as a unique identifier for the calculation.
    '''
    ret = Result()
    ret.files = get_calc_files(calc_dir)
    reader_ams = cache.get(ret.files['ams.rkf'])

    # check what the program is first. The program can be either AMS or one of the engines (ADF, DFTB, ...)
    if ('General', 'engine') in reader_ams:
        ret.engine = reader_ams.read('General', 'engine').strip().lower()
    # if program cannot be read from reader it is probably an old version of ADF, so we should default to ADF
    else:
        ret.engine = 'adf'

    # store the job id, which should be unique for the job
    ret.job_id = reader_ams.read('General', 'jobid') if ('General', 'jobid') in reader_ams else None

    # store information about the version of AMS
    ret.ams_version = get_ams_version(calc_dir)

    # store the computation timings, only available in ams.rkf
    ret.timing = get_timing(calc_dir)

    # store the calculation status
    ret.status = calculation_status(calc_dir)

    # check if this was a multijob
    ret.is_multijob = False
    if len([file for file in ret.files if file.endswith('.rkf')]) > 2:
        ret.is_multijob = True

    # read molecules
    ret.molecule = get_molecules(calc_dir)

    # and history variables
    ret.history = get_history(calc_dir)

    cache.unload(ret.files['ams.rkf'])
    return ret


def calculation_status(calc_dir: str) -> Result:
    '''Function that returns the status of the calculation described in reader. 
    In case of non-succes it will also give possible reasons for the errors/warnings.

    Args:
        reader: ``plams.KFReader`` or ``plams.KFFile`` object pointing to the desired calculation

    Returns:
        dict: Dictionary containing information about the calculation status:

            - **fatal (bool)** – True if calculation cannot be analysed correctly, False otherwise
            - **reasons (list[str])** – list of reasons to explain the status, they can be errors, warnings, etc.
            - **name (str)** – calculation status written as a string, one of ("SUCCESS", "RUNNING", "UNKNOWN", "SUCCESS(W)", "FAILED")
            - **code (str)** – calculation status written as a single character, one of ("S", "R", "U", "W" "F")
    '''
    files = get_calc_files(calc_dir)
    reader_ams = cache.get(files['ams.rkf'])

    ret = Result()
    ret.fatal = True
    ret.name = None
    ret.code = None
    ret.reasons = []

    termination_status = reader_ams.read('General', 'termination status').strip()

    # parse the logfile to find errors and warnings
    if 'log' in files:
        with open(files['log']) as logfile:
            for line in logfile.readlines():
                # the first 25 characters include the timestamp and two spaces
                line_ = line.strip()[25:]
                # errors and warnings have a predictable format
                if line_.lower().startswith('error:') or line_.lower().startswith('warning: '):
                    ret.reasons.append(line_)

    if termination_status == 'NORMAL TERMINATION':
        ret.fatal = False
        ret.name = 'SUCCESS'
        ret.code = 'S'
        return ret

    if termination_status == 'IN PROGRESS':
        ret.reasons.append('Calculation in progress')
        ret.name = 'RUNNING'
        ret.code = 'R'
        return ret

    if termination_status == 'UNKNOWN':
        ret.reasons.append('Calculation status unknown')
        ret.name = 'UNKNOWN'
        ret.code = 'U'
        return ret

    if termination_status == 'NORMAL TERMINATION with warnings':
        ret.fatal = False
        ret.name = 'SUCCESS(W)'
        ret.code = 'W'
        return ret

    if termination_status == 'NORMAL TERMINATION with errors':
        ret.name = 'FAILED'
        ret.code = 'F'
        return ret

    # if we have not excited the function yet we do not know what the status is
    # probably means that there was a parsing error in ams, which will be placed in termination status
    ret.reasons.append(termination_status)
    ret.name = 'UNKNOWN'
    ret.code = 'U'
    return ret


def get_molecules(calc_dir: str) -> Result:
    '''
    Function to get molecules from the calculation, including input, output and history molecules.
    It will also add bonds to the molecule if they are given in the rkf file, else it will guess them.

    Args:
        calc_dir: path pointing to the desired calculation.

    Returns:
        dict: Dictionary containing information about the molecular systems:

            - **number_of_atoms (int)** – number of atoms in the molecule.
            - **atom_numbers (list[int])** – list of atomic numbers for each atom in the molecule.
            - **atom_symbols (list[str])** – list of elements for each atom in the molecule.
            - **atom_masses (list[float])** – list of atomic masses for each atom in the molecule.
            - **input (plams.Molecule)** – molecule that was given in the input for the calculation.
            - **output (plams.Molecule)** – final molecule that was given as the output for the calculation. 
                If the calculation was a singlepoint calculation output and input molecules will be the same.
    '''
    files = get_calc_files(calc_dir)
    # all info is stored in reader_ams
    reader_ams = cache.get(files['ams.rkf'])

    ret = Result()

    # read general
    atnums = reader_ams.read('InputMolecule', 'AtomicNumbers')
    natoms = len(atnums)
    ret.number_of_atoms = natoms
    ret.atom_numbers = atnums
    ret.atom_symbols = reader_ams.read('InputMolecule', 'AtomSymbols').split()
    ret.atom_masses = reader_ams.read('InputMolecule', 'AtomMasses')

    # read input molecule
    ret.input = plams.Molecule()
    # read in the coordinates, they are given in Bohr, so convert them to Angstrom
    coords = np.array(reader_ams.read('InputMolecule', 'Coords')).reshape(natoms, 3) * 0.529177
    # add the atoms to the molecule
    for atnum, coord in zip(atnums, coords):
        ret.input.add_atom(plams.Atom(atnum=atnum, coords=coord))
    # try to add the bonds if they were given in the rkf file
    if ('Molecule', 'fromAtoms') in reader_ams and ('Molecule', 'toAtoms') in reader_ams and ('Molecule', 'bondOrders'):
        for at1, at2, order in zip(reader_ams.read('InputMolecule', 'fromAtoms'), reader_ams.read('InputMolecule', 'toAtoms'), reader_ams.read('InputMolecule', 'bondOrders')):
            ret.input.add_bond(plams.Bond(ret.input[at1], ret.input[at2], order=order))
    # if the bonds were not given, guess them
    else:
        ret.input.guess_bonds()

    # read output molecule
    ret.output = plams.Molecule()
    coords = np.array(reader_ams.read('Molecule', 'Coords')).reshape(natoms, 3) * 0.529177
    for atnum, coord in zip(atnums, coords):
        ret.output.add_atom(plams.Atom(atnum=atnum, coords=coord))
    if ('Molecule', 'fromAtoms') in reader_ams and ('Molecule', 'toAtoms') in reader_ams and ('Molecule', 'bondOrders'):
        for at1, at2, order in zip(reader_ams.read('Molecule', 'fromAtoms'), reader_ams.read('Molecule', 'toAtoms'), reader_ams.read('Molecule', 'bondOrders')):
            ret.output.add_bond(plams.Bond(ret.output[at1], ret.output[at2], order=order))
    else:
        ret.output.guess_bonds()

    return ret


def get_history(calc_dir: str) -> Result:
    '''
    Function to get history variables. The type of variables read depends on the type of calculation.

    Args:
        calc_dir: path pointing to the desired calculation.

    Returns:
        dict: Dictionary containing information about the calculation status:

            - **number_of_entries (int)** – number of steps in the history.
            - **{variable} (list[Any])** – variable read from the history section. The number of variables and type of variables depend on the nature of the calculation.
              
              Common variables:
            - **coords (list[plams.Molecule])** – list of molecules from the history, for example from a geometry optimization or PES scan.
            - **energy (list[float])** – list of energies associated with each geometry step.
            - **gradient (list[list[float]])** – array of gradients for each geometry step and each atom.
    '''
    # read history mols
    files = get_calc_files(calc_dir)
    # all info is stored in reader_ams
    reader_ams = cache.get(files['ams.rkf'])

    ret = Result()

    # read general
    atnums = reader_ams.read('InputMolecule', 'AtomicNumbers')
    natoms = len(atnums)

    if ('History', 'nEntries') in reader_ams:
        ret.number_of_entries = reader_ams.read('History', 'nEntries')
        # for history we read the other items in the rkf file
        index = 1
        items = []
        while index:
            try:
                item_name = reader_ams.read('History', f'ItemName({index})')
                items.append(item_name)
                index += 1
            except KeyError:
                index = False
        for item in items:
            ret[item.lower()] = []

        for i in range(ret.number_of_entries):
            for item in items:
                val = reader_ams.read('History', f'{item}({i+1})')
                if item == 'Coords':
                    mol = plams.Molecule()
                    coords = np.array(val).reshape(natoms, 3) * 0.529177
                    for atnum, coord in zip(atnums, coords):
                        mol.add_atom(plams.Atom(atnum=atnum, coords=coord))
                    mol.guess_bonds()
                    ret.coords.append(mol)
                else:
                    ret[item.lower()].append(val)

    return ret
