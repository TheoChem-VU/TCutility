import numpy as np
import warnings
from tcutility import results
from scm import plams


def avg_relative_bond_length_delta(base: plams.Molecule, pos: plams.Molecule, neg: plams.Molecule, atom1: int, atom2: int) -> float:
    """Function to calculate relative atom distance change in vibrational mode

    Args:
        base: plams.Molecule object containing the coordinates before applying vibration
        pos: plams.Molecule object with the vibrational mode added
        neg: plams.Molecule object with the vibrational mode subtracted
        atom1: label for the first atom
        atom2: label for the second atom

    Returns:
        Average relative difference from the baseline distance between selected atoms in this vibrational mode (as percentage).
    """
    basedist = base[atom1].distance_to(base[atom2])
    x = abs((pos[atom1].distance_to(pos[atom2]) / basedist) - 1)  # distances between positive and negative vibration are normalized with base distance
    y = abs((neg[atom1].distance_to(neg[atom2]) / basedist) - 1)  # variances are obtained and averaged
    return (x + y) / 2


def determine_ts_reactioncoordinate(data: results.Result, mode_index: int = 0, bond_tolerance: float = 1.28, min_delta_dist: float = 0.0) -> np.ndarray:
    """Function to retrieve reaction coordinate from a given transitionstate, using the first imaginary frequency.

    Args:
        data: TCutility.results.Result object containing calculation data
        mode_index: vibrational mode index to analyze
        bond_tolerance: parameter for plams.Molecule.guess_bonds() function
        min_delta_dist: minimum relative bond length change before qualifying as active atom. If 0, all bond changes are counted

    Returns:
        Array containing all the obtained reaction coordinates. Reaction coordinate format is [active_atom1, active_atom2, sign], using Distance reactioncoordinate
        Symmetry elements are ignored, by convention the atom labels are increasing (atom1 < atom2)
    """

    assert "modes" in data.properties.vibrations, "Vibrational data is required, but was not present in .rkf file"

    outputmol = data.molecule.output

    base = np.array(outputmol).reshape(-1, 3)
    tsimode = np.array(data.properties.vibrations.modes[mode_index]).reshape(-1, 3)

    posvib = outputmol.copy()
    posvib.from_array(base + tsimode)
    posvib.guess_bonds(dmax=bond_tolerance)
    negvib = outputmol.copy()
    negvib.from_array(base - tsimode)
    negvib.guess_bonds(dmax=bond_tolerance)

    pairs = np.where(posvib.bond_matrix() - negvib.bond_matrix())
    rc = np.array(
        [
            [a + 1, b + 1, np.sign(posvib.bond_matrix()[a][b] - negvib.bond_matrix()[a][b])]
            for a, b in np.c_[pairs[0], pairs[1]]  # bond matrices and pairs matrix are 0-indexed unlike the plams.Molecule labels, hence a+1 and b+1 are needed
            if a < b and avg_relative_bond_length_delta(outputmol, posvib, negvib, a + 1, b + 1) > min_delta_dist
        ],
        dtype=int,
    )
    return rc


def validate_transitionstate(calc_dir: str, rcatoms: list = None, analyze_modes: int = 1, **kwargs) -> bool:
    """Function to determine whether a transition state calculation yielded the expected transition state. Checks the reaction coordinates provided by the user (or in the .rkf file User Input section) and compares
        this against the reaction coordinates found in the imaginary modes of the transitionstate. If the transitionstate has multiple imaginary frequencies, it is possible to check multiple modes for the expected
        reaction coordinate.

    Args:
        calc_dir: path pointing to the desired calculation.
        rcatoms: list or array containing expected reaction coordinates, to check against the transition state. If not defined, it is obtained from the ams.rkf user input.
                  Only uses 'Distance' reaction coordinate. Format should be [atomlabel1, atomlabel2, (optional) sign]
        analyze_modes: Number of imaginary modes to analyze, default only the first mode. Modes are ordered lowest frequency first. If 0 or negative value is provided, analyze all modes with imaginary frequency.
        **kwargs: keyword arguments for use in :func:`determine_ts_reactioncoordinate`.

    Returns:
        Boolean value, True if the found transition state reaction coordinates contain the expected reaction coordinates, False otherwise.
        If multiple modes are analyzed, returns True if at least one mode contains the expected reaction coordinates.
    """

    data = results.read(calc_dir)
    assert "modes" in data.properties.vibrations, "Vibrational data is required, but was not present in .rkf file"

    nimag = sum(1 for x in data.properties.vibrations.frequencies if x < 0)
    if nimag == 0:
        return False  # no imaginary modes found in transitionstate

    if analyze_modes > 0:  # if positive value is provided, check that many imaginary vibrational modes. Otherwise all imaginary ones are analyzed
        nimag = min(nimag, analyze_modes)  # limit to the actual number of vibrational modes

    if isinstance(rcatoms, type(None)):
        assert "reactioncoordinate" in data.input.transitionstatesearch, "Reaction coordinate is a required input, but was neither provided nor present in the .rkf file"
        rcatoms = np.array([[int(float(y)) for y in x.split()[1:]] for x in data.input.transitionstatesearch.reactioncoordinate if x.split()[0] == "Distance"])
        assert len(rcatoms) > 0, "Reaction coordinate data was present in .rkf file, but no reaction coordinate using Distance was provided"

    # cast the reaction coordinate as 2d array. If reaction coordinate sign is provided, it must be provided for all reaction coordinates.
    # the np.atleast_2d() function will cause a deprecation warning if the dimensions mismatch, this is raised as a value error instead
    with warnings.catch_warnings(record=True) as w:
        rcatoms = np.atleast_2d(rcatoms)
        if len(w) > 0:
            raise ValueError(w[-1].message)

    assert np.all([len(x) == 2 or len(x) == 3 for x in rcatoms]), "Invalid format of reaction coordinate. Reaction coordinate format must be [label1, label2, (optional) sign]"

    ret = []

    for idx in range(nimag):
        result = determine_ts_reactioncoordinate(data, mode_index=idx, **kwargs)
        if len(result) == 0:
            ret.append(False)
            continue

        # sort for consistency
        for index, [a, b, *c] in enumerate(rcatoms):
            if c:
                c = np.sign(c)
            if a > b:
                a, b = b, a
            rcatoms[index] = [a, b, *c]
        rcatoms = rcatoms[rcatoms[:, 1].argsort()]
        rcatoms = rcatoms[rcatoms[:, 0].argsort()]
        result = result[result[:, 1].argsort()]
        result = result[result[:, 0].argsort()]

        # (optional) check for internal consistency if the reaction coordinate sign is provided
        # only the first reaction coordinate sign is arbitrary, check remaining coordinates for consistency
        if len(rcatoms[0]) > 2:
            foundmatch = False
            for idx, rc in enumerate(result):
                if rc[0] == rcatoms[0][0] and rc[1] == rcatoms[0][1]:
                    result[:, 2] = result[:, 2] if np.sign(result[idx][2]) == rcatoms[0][2] else -result[:, 2]
                    foundmatch = True
                    break
            if not foundmatch:  # at least one element of rcatoms is not present in result
                ret.append(False)
                continue
        else:
            result = result[:, :-1]

        ret.append(set(str(x) for x in rcatoms).issubset(set(str(y) for y in result)))

    return any(ret)
