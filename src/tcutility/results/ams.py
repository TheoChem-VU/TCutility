import os
import re
from datetime import datetime
from typing import List

import numpy as np
from scm import plams
import scipy.interpolate

from tcutility import constants, ensure_list
from tcutility.results import Result, cache
from tcutility.tc_typing import arrays

j = os.path.join


def get_calc_files(calc_dir: str) -> dict:
    """Function that returns files relevant to AMS calculations stored in ``calc_dir``.

    Args:
        calc_dir: path pointing to the desired calculation

    Returns:
        Dictionary containing filenames and paths
    """
    # collect all files in the current directory and subdirectories
    files = []
    for root, _, files_ in os.walk(os.path.abspath(calc_dir)):
        if os.path.split(root)[1].startswith("."):
            continue

        # some results are stored in dirs called {name}.results, if the calculations uses fragments there will be additional dirs called
        # {name}.{fragname}.results, which do not contain new information as the required info is copied over to {name}.results. Therefore
        # we should skip the fragment directories
        if os.path.split(root)[1].endswith(".results") and len(os.path.split(root)[1].split(".")) > 2:
            continue

        # we only need the rkf files in the .results directories
        if root.endswith(".rkf") and ".results" not in root:
            continue

        # opened files end in ~ and should be ignored
        if root.endswith("~"):
            continue

        # t21 files for specific atoms are not usefull and should be ignored
        if "t21." in root:
            continue

        # if a calculation is running or did not finish correctly there might be tmp. dirs, which should be ignored
        if os.path.split(root)[1].startswith("tmp."):
            continue

        # the rest can all be stored
        files.extend([j(root, file) for file in files_])

    # parse the filenames
    ret = {}
    ret["root"] = os.path.abspath(calc_dir)
    for file in files:
        # rkf files are either called /{program}.rkf, or /{name}.{program}.rkf, so we must parse them in a special way
        if file.endswith(".rkf"):
            f = os.path.split(file)[1]
            parts = f.split(".")
            f = f"{parts[-2]}.rkf"
            ret[f] = os.path.abspath(file)

        # logfiles are generally called either {name}.log or {name}.logfile
        if file.endswith(".logfile") or file.endswith(".log") or file.endswith(".err"):
            f = os.path.split(file)[1]
            parts = f.split(".")
            f = ".".join(parts[1:]).replace("logfile", "log")
            ret[f] = os.path.abspath(file)

        if file.endswith(".out") and "CreateAtoms" not in file:
            ret["out"] = os.path.abspath(file)

    return ret


def get_ams_version(calc_dir: str) -> Result:
    """Function to get the AMS version used in the calculation.

    Args:
        calc_dir: path pointing to the desired calculation.

    Returns:
        :Dictionary containing results about the AMS version:

            - **full (str)** – the full version string as written by SCM.
            - **major (str)** – major AMS version, should correspond to the year of release.
            - **minor (str)** – minor AMS version.
            - **micro (str)** – micro AMS version, should correspond to the internal revision number.
            - **date (datetime.datetime)** – date the AMS version was released.
    """
    ret = Result()
    files = get_calc_files(calc_dir)
    reader_ams = cache.get(files["ams.rkf"])

    # store information about the version of AMS
    ret.full = str(reader_ams.read("General", "release"))
    # decompose the full version string
    ret.major = ret.full.split(".")[0]
    ret.minor = ret.full.split()[0].split(".")[1]
    ret.micro = ret.full.split()[1]
    ret.date = datetime.strptime(ret.full.split('(')[-1].split(')')[0], "%Y-%m-%d")

    return ret


def get_ams_info(calc_dir: str) -> Result:
    """Function to read useful info about the calculation in ``calc_dir``. Returned information will depend on the type of file that is provided.

    Args:
        calc_dir: path pointing to the desired calculation.

    Returns:
        :Dictionary containing results about the calculation and AMS:

            - **ams_version (Result)** – information about the AMS version used, see :func:`get_ams_version`.
            - **engine (str)** – the engine that was used to perform the calculation, for example 'adf', 'dftb', ...
            - **job_id (str)** – the ID of the job, can be used to check if two calculations are the same. Might also be used as a unique identifier for the calculation.
            - **status (Result)** – information about calculation status, see :func:`get_calculation_status`.
            - **is_multijob (bool)** – whether the job was a multijob, for example a fragment analysis.
            - **molecule (Result)** – information about the input and output molecules and the molecular system in general, see :func:`get_molecules`.
            - **history (Result)** – information about history variables, see :func:`get_history`.
    """
    ret = Result()
    ret.files = get_calc_files(calc_dir)
    reader_ams = cache.get(ret.files["ams.rkf"])

    # check what the program is first. The program can be either AMS or one of the engines (ADF, DFTB, ...)
    if ("General", "engine") in reader_ams:
        ret.engine = str(reader_ams.read("General", "engine")).strip().lower()
    # if program cannot be read from reader it is probably an old version of ADF, so we should default to ADF
    else:
        ret.engine = "adf"

    # store the input of the calculation
    ret.input = get_ams_input(reader_ams.read("General", "user input"))

    # store the job id, which should be unique for the job
    ret.job_id = reader_ams.read("General", "jobid") if ("General", "jobid") in reader_ams else None

    # store information about the version of AMS
    ret.ams_version = get_ams_version(calc_dir)

    # store the computation timings, only available in ams.rkf
    ret.timing = get_timing(calc_dir)

    # store the calculation status
    ret.status = get_calculation_status(calc_dir)

    # check if this was a multijob
    ret.is_multijob = False
    if len([file for file in ret.files if file.endswith(".rkf")]) > 2:
        ret.is_multijob = True

    # read molecules
    ret.molecule = get_molecules(calc_dir)

    # and history variables
    ret.history = get_history(calc_dir)

    ret.pes = get_pes(calc_dir)

    cache.unload(ret.files["ams.rkf"])
    return ret


def get_timing(calc_dir: str) -> Result:
    """Function to get the timings from the calculation.

    Args:
        calc_dir: path pointing to the desired calculation.

    Returns:
        :Dictionary containing results about the timings:

            - **cpu (float)** – time spent performing calculations on the cpu.
            - **sys (float)** – time spent by the system (file IO, process creation/destruction, etc ...).
            - **total (float)** – total time spent by AMS on the calculation, can be larger than the sum of cpu and sys.
    """
    ret = Result()
    files = get_calc_files(calc_dir)
    reader_ams = cache.get(files["ams.rkf"])

    ret.cpu = reader_ams.read("General", "CPUTime") if ("General", "CPUTime") in reader_ams else None
    ret.sys = reader_ams.read("General", "SysTime") if ("General", "SysTime") in reader_ams else None
    ret.total = reader_ams.read("General", "ElapsedTime") if ("General", "ElapsedTime") in reader_ams else None

    return ret


def get_calculation_status(calc_dir: str) -> Result:
    """Function that returns the status of the calculation described in reader.
    In case of non-succes it will also give possible reasons for the errors/warnings.

    Args:
        reader: ``plams.KFReader`` or ``plams.KFFile`` object pointing to the desired calculation

    Returns:
        :Dictionary containing information about the calculation status:

            - **fatal (bool)** – True if calculation cannot be analysed correctly, False otherwise
            - **reasons (list[str])** – list of reasons to explain the status, they can be errors, warnings, etc.
            - **name (str)** – calculation status written as a string, one of ("SUCCESS", "RUNNING", "UNKNOWN", "SUCCESS(W)", "FAILED")
            - **code (str)** – calculation status written as a single character, one of ("S", "R", "U", "W" "F")
    """
    files = get_calc_files(calc_dir)

    ret = Result()
    ret.fatal = True
    ret.name = None
    ret.code = None
    ret.reasons = []

    # parse the logfile to find errors and warnings
    if "log" in files:
        with open(files["log"]) as logfile:
            lines = logfile.readlines()
            # the termination status is at the end of the file, so we start reading from the end
            for line in lines[::-1]:
                # the first 25 characters include the timestamp and two spaces
                line_ = line.strip()[25:].lower()
                # errors and warnings have a predictable format
                if line_.lower().startswith("error:") or line_.lower().startswith("warning: "):
                    ret.reasons.append(line_)

                if "normal termination" in line_:
                    ret.fatal = False
                    ret.name = "SUCCESS"
                    ret.code = "S"
                    return ret


    reader_ams = cache.get(files["ams.rkf"])
    termination_status = str(reader_ams.read("General", "termination status")).strip()

    if termination_status == "NORMAL TERMINATION":
        ret.fatal = False
        ret.name = "SUCCESS"
        ret.code = "S"
        return ret

    if termination_status == "IN PROGRESS":
        ret.fatal = False
        ret.reasons.append("Calculation in progress")
        ret.name = "RUNNING"
        ret.code = "R"
        return ret

    if termination_status == "UNKNOWN":
        ret.reasons.append("Calculation status unknown")
        ret.name = "UNKNOWN"
        ret.code = "U"
        return ret

    if termination_status == "NORMAL TERMINATION with warnings":
        ret.fatal = False
        ret.name = "SUCCESS(W)"
        ret.code = "W"
        return ret

    if termination_status == "NORMAL TERMINATION with errors":
        ret.name = "FAILED"
        ret.code = "F"
        return ret

    # if we have not excited the function yet we do not know what the status is
    # probably means that there was a parsing error in ams, which will be placed in termination status
    ret.reasons.append(termination_status)
    ret.name = "UNKNOWN"
    ret.code = "U"
    return ret


# ------------------------------------------------------------- #
# ------------------------- Geometry -------------------------- #
# ------------------------------------------------------------- #


# -------------------- Fragment indices ----------------------- #


def _get_fragment_indices_from_input_order(results_type) -> arrays.Array1D:
    """Function to get the fragment indices from the input order. This is needed because the fragment indices are stored in internal order in the rkf file."""
    frag_indices = np.array(results_type.read("Geometry", "fragment and atomtype index")).reshape(2, -1)  # 1st row: Fragment index; 2nd row atomtype index
    atom_order = np.array(results_type.read("Geometry", "atom order index")).reshape(2, -1)  # 1st row: input order; 2nd row: internal order
    return frag_indices[0][atom_order[0] - 1]


# ------------------------ Molecule -------------------------- #


def _make_molecule(kf_variable: str, reader_ams: plams.KFReader, natoms: int, atnums: List[int]) -> plams.Molecule:
    """Makes a plams.Molecule object from the given kf_variable ("InputMolecule" or "Molecule") and reader."""
    # read output molecule
    ret_mol = plams.Molecule()
    coords = np.array(reader_ams.read(kf_variable, "Coords")).reshape(natoms, 3) * constants.BOHR2ANG
    for atnum, coord in zip(atnums, coords):
        ret_mol.add_atom(plams.Atom(atnum=atnum, coords=coord))
    if ("Molecule", "fromAtoms") in reader_ams and ("Molecule", "toAtoms") in reader_ams and ("Molecule", "bondOrders") in reader_ams:
        at_from = ensure_list(reader_ams.read("InputMolecule", "fromAtoms"))
        at_to = ensure_list(reader_ams.read("InputMolecule", "toAtoms"))
        bos = ensure_list(reader_ams.read("InputMolecule", "bondOrders"))
        for at1, at2, order in zip(at_from, at_to, bos):
            ret_mol.add_bond(plams.Bond(ret_mol[at1], ret_mol[at2], order=order))
    else:
        ret_mol.guess_bonds()
    return ret_mol


def get_molecules(calc_dir: str) -> Result:
    """
    Function to get molecules from the calculation, including input, output and history molecules.
    It will also add bonds to the molecule if they are given in the rkf file, else it will guess them.

    Args:
        calc_dir: path pointing to the desired calculation.

    Returns:
        :Dictionary containing information about the molecular systems:

            - **number_of_atoms (int)** – number of atoms in the molecule.
            - **atom_numbers (list[int])** – list of atomic numbers for each atom in the molecule.
            - **atom_symbols (list[str])** – list of elements for each atom in the molecule.
            - **atom_masses (list[float])** – list of atomic masses for each atom in the molecule.
            - **input (plams.Molecule)** – molecule that was given in the input for the calculation.
            - **output (plams.Molecule)** – final molecule that was given as the output for the calculation. If the calculation was a singlepoint calculation output and input molecules will be the same.
            - **frag_indices (numpy array[int] (1D))** – list of fragment indices for each atom in the molecule. The indices are given in the order of the atoms in the molecule.
    """
    files = get_calc_files(calc_dir)
    # all info is stored in reader_ams
    reader_ams = cache.get(files["ams.rkf"])

    ret = Result()

    # read general
    atnums = ensure_list(reader_ams.read("InputMolecule", "AtomicNumbers"))  # type: ignore plams does not include type hints. Returns list[int]
    natoms = len(atnums)
    ret.number_of_atoms = natoms
    ret.atom_numbers = atnums
    ret.atom_symbols = str(reader_ams.read("InputMolecule", "AtomSymbols")).split()
    ret.atom_masses = reader_ams.read("InputMolecule", "AtomMasses")

    # read input molecule
    ret.input = _make_molecule("InputMolecule", reader_ams, natoms, atnums)

    # read output molecule
    ret.output = _make_molecule("Molecule", reader_ams, natoms, atnums)

    # add fragment indices to the molecule using adf file
    try:
        reader_adf = cache.get(files["adf.rkf"])
        ret.frag_indices = _get_fragment_indices_from_input_order(reader_adf)
    except KeyError:
        ret.frag_indices = np.ones(natoms)

    # add the charges to the molecule
    try:
        ret.mol_charge = reader_ams.read("Molecule", "Charge")
    except KeyError:
        ret.mol_charge = 0.0

    return ret


def get_pes(calc_dir: str) -> Result:
    """
    Function to get PES scan variables.

    Args:
        calc_dir: path pointing to the desired calculation.

    Returns:
        :Dictionary containing information about the PES scan:

            - ``nscan_coords`` **int** – the number of scan-coordinates for this PES scan.
            - ``scan_coord_name`` **list[str] | str** – the names of the scan-coordinates.
                If there is more than one scan-coordinates it will be a list of strings, otherwise it will be a single string.
            - ``scan_coord`` **list[np.ndarray] | np.ndarray** – arrays of values for the scan-coordinates.
                If there is more than one scan-coordinates it will be a list of arrays, otherwise it will be a single array.
            - ``npoints`` **list[int] | int** – number of scan points for the scan-coordinates.
                If there is more than one scan-coordinates it will be a list of integers, otherwise it will be a single integer.
            - ``energies`` **np.ndarray** - array containing energies with shape ``npoints``.
            - ``energy_interpolator`` **scipy.interpolate.RegularGridInterpolator** - interpolator 
                object used for obtaining energies at any point on the PES. Cannot be used for extrapolation.
            - ``molecule_interpolator`` **fuction** - interpolator used to obtain molecular coordinates at
                any point on the PES. Cannot be used for extrapolation.
    """
    # read history mols
    files = get_calc_files(calc_dir)
    # all info is stored in reader_ams
    reader_ams = cache.get(files["ams.rkf"])

    # check if we have done a PESScan
    if ("PESScan", "nPoints") not in reader_ams:
        return

    ret = Result()

    history_indices = reader_ams.read('PESScan', 'HistoryIndices')
    atnums = ensure_list(reader_ams.read("InputMolecule", "AtomicNumbers"))  # type: ignore plams does not include type hints. Returns list[int]
    ret.molecules = []
    for i in history_indices:
        mol = plams.Molecule()
        coords = np.array(reader_ams.read("History", f"Coords({i})")).reshape(-1, 3) * constants.BOHR2ANG
        for atnum, coord in zip(atnums, coords):
            mol.add_atom(plams.Atom(atnum=atnum, coords=coord))
        mol.guess_bonds()
        ret.molecules.append(mol)

    # read general info
    ret.nscan_coords = reader_ams.read("PESScan", "nScanCoord")
    ret.scan_coord_name = [reader_ams.read("PESScan", f"ScanCoord({i+1})").strip() for i in range(ret.nscan_coords)]
    ret.npoints = [reader_ams.read("PESScan", f"nPoints({i+1})") for i in range(ret.nscan_coords)]
    
    conversion_factors = [constants.BOHR2ANG if name.startswith('Distance') else 180/np.pi for name in ret.scan_coord_name]

    ret.scan_coord = [np.linspace(reader_ams.read("PESScan", f"RangeStart({i+1})"), reader_ams.read("PESScan", f"RangeEnd({i+1})"), ret.npoints[i]) * f for i, f in zip(range(ret.nscan_coords), conversion_factors)]
    if ("PESScan", "PES") in reader_ams:
        # if we have the PES we can get the energies and coordinates
        ret.energies = np.array(reader_ams.read("PESScan", "PES")).reshape(*ret.npoints) * constants.HA2KCALMOL
        # return an interpolator for the energies
        ret.energy_interpolator = scipy.interpolate.RegularGridInterpolator(ret.scan_coord, ret.energies)

        # generate the coordinate arrays to be able to interpolate
        _coords = np.array([np.array(mol) for mol in ret.molecules]).reshape(*ret.npoints, len(ret.molecules[0]), 3)
        # this interpolator is a temporary one, it will be used to get the coordinates only, not the 
        # whole molecule including atomic number, data, etc.
        _coordinate_interpolator = scipy.interpolate.RegularGridInterpolator(ret.scan_coord, _coords)

        # this function replaces the interpolator and uses the interpolator to generate molecules 
        # at specific PES coordinates
        def molecule_interpolator(xi: np.ndarray) -> np.ndarray:
            xi = np.atleast_2d(xi)
            yi = _coordinate_interpolator(xi)
            mols = []
            for y in yi:
                mol = plams.Molecule()
                for atnum, coord in zip(atnums, y):
                    mol.add_atom(plams.Atom(atnum=atnum, coords=coord))
                mols.append(mol)
                
            return mols

        ret.molecule_interpolator = molecule_interpolator

    # if only one coord is given, flatten some parameters
    if ret.nscan_coords == 1:
        ret.scan_coord_name = ret.scan_coord_name[0]
        ret.scan_coord = ret.scan_coord[0]
        ret.npoints = ret.npoints[0]

    return ret


def get_history(calc_dir: str) -> Result:
    """
    Function to get history variables. The type of variables read depends on the type of calculation.

    Args:
        calc_dir: path pointing to the desired calculation.

    Returns:
        :Dictionary containing information about the calculation status:

            - ``number_of_entries`` **(int)** – number of steps in the history.
            - ``{variable}`` **(list[Any])** – variable read from the history section. The number of variables and type of variables depend on the nature of the calculation.

              Common variables:
                | ``Molecule`` **(list[plams.Molecule])** – list of molecules from the history, for example from a geometry optimization or PES scan.
                | ``energy`` **(list[float])** – list of energies associated with each geometry step.
                | ``gradient`` **(list[list[float]])** – array of gradients for each geometry step and each atom.
    """
    # read history mols
    files = get_calc_files(calc_dir)
    # all info is stored in reader_ams
    reader_ams = cache.get(files["ams.rkf"])

    ret = Result()

    # read general info
    atnums = ensure_list(reader_ams.read("InputMolecule", "AtomicNumbers"))  # type: ignore plams does not include type hints. Returns list[int]
    natoms = len(atnums)

    if ("History", "nEntries") in reader_ams:
        # the number of elements per history variable (e.g. number of steps in a geometry optimization)
        ret.number_of_entries = reader_ams.read("History", "nEntries")
        # for history we read the other variables in the rkf file
        # the variables are given in ('History', f'ItemName({index})') so we have to find all of those
        index = 1  # tracks the current index of the variable. Will be set to False to stop the search
        items = []
        while index:
            # try to access ItemName, if it cannot find it stop iteration
            try:
                item_name = reader_ams.read("History", f"ItemName({index})")
                items.append(item_name)
                index += 1
            except KeyError:
                index = False

        if "Coords" in items:
            items.append("Molecule")

        # create variable in result for each variable found
        for item in items:
            ret[item.lower()] = []

        # collect the elements for each history variable
        for i in range(ret.number_of_entries):
            for item in items:
                # Molecule are special, because we will convert them to plams.Molecule objects first
                if item == "Molecule":
                    mol = plams.Molecule()
                    coords = np.array(reader_ams.read("History", f"Coords({i+1})")).reshape(natoms, 3) * constants.BOHR2ANG
                    for atnum, coord in zip(atnums, coords):
                        mol.add_atom(plams.Atom(atnum=atnum, coords=coord))
                    mol.guess_bonds()
                    ret.molecule.append(mol)
                # other variables are just added as-is
                else:
                    val = reader_ams.read("History", f"{item}({i+1})")
                    ret[item.lower()].append(val)

        if "converged" not in ret.keys() and ("PESScan", "HistoryIndices") in reader_ams:
            ret["converged"] = [False] * ret.number_of_entries
            for idx in ensure_list(reader_ams.read("PESScan", "HistoryIndices")):
                ret["converged"][idx - 1] = True

    return ret


def get_input_blocks():
    """
    This function reads input_blocks and decomposes its content into a list of blocks and a list of non-standard blocks
    The general format is as follows:

    parentblock
    - subblock
    - - subsubblock
    - subblock !nonstandard
    parentblock
    - subblock
    - - subsubblock
    - - - subsubsubblock
    - - - subsubsubblock !nonstandard

    Each subblock has to be defined within its parent block. !nonstandard indicates that the block is a non-standard block
    These blocks are special in that they can contain multiple of the same entry
    """
    blocks = []
    nonstandard_blocks = []
    parent_blocks = []  # this list tracks the parent blocks of the current block
    with open(j(os.path.split(__file__)[0], "input_blocks")) as inpblx:
        lines = inpblx.readlines()

    for line in lines:
        line = line.strip().lower()
        # we can ignore some lines
        if line == "" or line.startswith("#"):
            continue

        # block_depth indicates how many parents the block has
        block_depth = line.count("- ")
        # we reduce the amount of parent_blocks using block_depth
        # if we move from a subsubblock to a subblock we remove the last-added block
        parent_blocks = parent_blocks[:block_depth]

        # remove the "- " substrings
        block = line.split("- ")[-1].strip().lower()
        # check if the block is non-standard. If it is, remove the !nonstandard substring
        # and add it to the nonstandard_blocks list
        if block.endswith("!nonstandard"):
            block = block.split()[0]
            nonstandard_blocks.append(parent_blocks.copy() + [block])
        # in both standard and nonstandard cases add the block to blocks list
        blocks.append(parent_blocks.copy() + [block])
        # add the current block to parent_blocks for the next line
        parent_blocks.append(block.lower())

    return blocks, nonstandard_blocks


def get_ams_input(inp: str) -> Result:
    def get_possible_blocks():
        # check which blocks are openable given the current open blocks
        # we start by considering all blocks
        possible_blocks = blocks
        # we iterate through the open blocks and check if the first element in the possible_blocks is the same.
        # this way we move down through the blocks
        for open_block in open_blocks:
            possible_blocks = [block[1:] for block in possible_blocks if len(block) > 0 and block[0].lower() == open_block.lower()]
        # we want only the first element in the possible blocks, not the tails
        possible_blocks = set([block[0] for block in possible_blocks if len(block) > 0])
        return possible_blocks

    sett = Result()

    blocks, nonstandard_blocks = get_input_blocks()

    open_blocks = ["ams"]
    for line in inp.splitlines():
        line = line.strip()

        # we remove comments from the line
        # comments can be either at the start of a line or after a real statement
        # so we have to search the line for comment starters and remove the part after it
        for comment_start in ["#", "!", "::"]:
            if comment_start in line:
                idx = line.index(comment_start)
                line = line[:idx]

        # skip empty lines
        if not line:
            continue

        # if we encounter an end statement we can close the last openblock
        if line.lower().startswith("end"):
            open_blocks.pop(-1)
            continue

        # check if we are opening a block
        # We have to store the parts of a compact block (if it is compact)
        # it will be a list of tuples of key-value pairs
        compact_parts = None
        skip = False
        # check if the current line corresponds to a possible block
        for possible_block in get_possible_blocks():
            if line.lower().startswith(possible_block.lower()):
                # a block opening can either span multiple lines or can be use with compact notation
                # compact notation will always have = signs
                if "=" in line:
                    # split the key-values using some regex magic
                    compact = line[len(possible_block) :].strip()  # remove the block name
                    compact_parts = re.findall(r"""(\S+)=['"]{0,1}([^'"\n]*)['"]{0,1}""", compact)
                else:
                    skip = True
                # add the new block to the open_blocks
                open_blocks.append(possible_block)

        # if we are not in a compact block we can just skip
        if skip:
            continue

        # get the sett to the correct level
        # first check if the block is nonstandard
        is_nonstandard = [block.lower() for block in open_blocks] in nonstandard_blocks
        sett_ = sett
        # go to the layer one above the lowest
        for open_block in open_blocks[:-1]:
            sett_ = sett_[open_block]
        # at the lowest level we have to check if the block is nonstandard. If it is, we add the whole line to the settings object
        if is_nonstandard and not sett_[open_blocks[-1]]:
            sett_[open_blocks[-1]] = []
        # then finally go to the lowest sett layer
        sett_ = sett_[open_blocks[-1]]

        # if we are in a compact block we just add all the key-value pairs
        if compact_parts:
            for key, val in compact_parts:
                sett_[key] = val
            # compact blocks do not have end statements, so we can remove it again from the open_blocks
            open_blocks.pop(-1)
        # in a normal block we split the line and add them to the settings
        else:
            # for nonstandard blocks we add the line to the list
            if is_nonstandard:
                sett_.append(line.strip())
            # for normal blocks we split the line and set it as a key, the rest of the line is the value
            else:
                sett_[line.split()[0]] = line[len(line.split()[0]) :].strip()

    for engine_block in ["engine adf", "engine dftb", "engine band"]:
        if engine_block not in sett["ams"]:
            continue
        sett["ams"][engine_block.split()[1]] = sett["ams"][engine_block]
        del sett["ams"][engine_block]

    return sett["ams"]
