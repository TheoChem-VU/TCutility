import numpy as np
from TCutility.results import read
from scm import plams

def atom_distance(molecule: plams.Molecule, atom1: int, atom2: int) -> float:
    res = 0.0
    for i,j in zip(molecule[atom1],molecule[atom2]):
        res += (i - j)**2
    return np.sqrt(res)

def avg_relative_bond_length_delta(base: plams.Molecule, pos: plams.Molecule,neg: plams.Molecule, a1: int, a2: int) -> float:
    basedist = atom_distance(base, a1+1, a2+1)
    x = abs((atom_distance(pos, a1+1, a2+1)/basedist)-1)
    y = abs((atom_distance(neg, a1+1, a2+1)/basedist)-1)
    return (x+y)/2

def determine_ts_reactioncoordinate(calc_dir: str, bond_tolerance: float = 1.28, min_delta_dist: float = 0.1) -> np.ndarray:
    '''Function to retrieve reaction coordinate from a given transitionstate, using the first imaginary frequency.

    Args:
        calc_dir: path pointing to the desired calculation.
        bond_tolerance: parameter for plams.molecule.guess_bonds() function
        min_delta_dist: minimum relative bond length change before qualifying as active atom

    Returns:
        Array containing all the obtained reaction coordinates. Reaction coordinate format is [active_atom1, active_atom2, sign]
        Symmetry elements are ignored, by convention the atom labels are increasing (atom1 < atom2)
    '''

    data = read(calc_dir)
    assert 'modes' in data.properties.vibrations, 'Vibrational data is required, but was not present in .rkf file'

    outputmol = data.molecule.output

    base = np.array(outputmol).reshape(-1,3)
    tsimode = np.array(data.properties.vibrations.modes[0]).reshape(-1,3)

    posvib = outputmol.copy()
    posvib.from_array(base + tsimode)
    posvib.guess_bonds(dmax=bond_tolerance)
    negvib = outputmol.copy()
    negvib.from_array(base - tsimode)
    negvib.guess_bonds(dmax=bond_tolerance)

    pairs = np.where(posvib.bond_matrix() - negvib.bond_matrix())
    rc = np.array(
                [   [a+1, b+1, np.sign(posvib.bond_matrix()[a][b] - negvib.bond_matrix()[a][b])]
                    for a, b in np.c_[pairs[0], pairs[1]] 
                    if a < b and avg_relative_bond_length_delta(outputmol, posvib, negvib, a, b) > min_delta_dist
                ],  dtype=int)
    return rc


def validate_transitionstate(calc_dir: str, rcatoms = None, bond_tolerance: float = 1.28, min_delta_dist: float = 0.1) -> bool:
    '''Function to determine whether a transition state calculation yielded the expected transition state.

    Args:
        calc_dir: path pointing to the desired calculation.
        rcatoms: list or array containing expected reaction coordinates, to check against the transition state. If not defined, it is obtained from the ams.rkf user input
        bond_tolerance: parameter for plams.molecule.guess_bonds() function, used in determine_ts_reactioncoordinate
        min_delta_dist: minimum relative bond length change before qualifying as active atom, used in determine_ts_reactioncoordinate

    Returns:
        Boolean value, True if the found transition state reaction coordinates match the expected reaction coordinates, False otherwise
    '''

    result = determine_ts_reactioncoordinate(calc_dir, bond_tolerance, min_delta_dist)

    if isinstance(rcatoms, list):
        rcatoms = np.array(rcatoms)

    if not isinstance(rcatoms, np.ndarray):
        data = read(calc_dir)
        assert 'reactioncoordinate' in data.input.transitionstatesearch, 'Reaction coordinate is a required input, but was neither provided nor present in the .rkf file'
        rcatoms = np.array([[int(float(y)) for y in x.split()[1:]] for x in data.input.transitionstatesearch.reactioncoordinate])

    if not isinstance(rcatoms[0], np.ndarray):
        rcatoms = np.array([rcatoms])

    assert np.all([len(x)==3 for x in rcatoms]), 'Invalid format of reaction coordinate'

    # sort for consistency
    for index, [a,b,c] in enumerate(rcatoms):
        if a > b:
            rcatoms[index] = [b,a,c]
    rcatoms = rcatoms[rcatoms[:,1].argsort()]
    rcatoms = rcatoms[rcatoms[:,0].argsort()]
    result = result[result[:,1].argsort()]
    result = result[result[:,0].argsort()]

    # only the first reaction coordinate sign is arbitrary, check remaining coordinates for consistency
    result[:, 2] = result[:, 2] if np.sign(result[0][2]) == rcatoms[0][2] else -result[:, 2]
    ret = np.all(result == rcatoms)    

    return ret

if __name__ == '__main__':
    file = '../../test/fixtures/radical_addition_ts'
    print(determine_ts_reactioncoordinate(file))
    print(validate_transitionstate(file))
    print(validate_transitionstate(file, [1,16,1]))
    print(validate_transitionstate(file, [[1,16,1]]))

    print('\n')

    file = '../../test/fixtures/chloromethane_sn2_ts'
    print(determine_ts_reactioncoordinate(file))
