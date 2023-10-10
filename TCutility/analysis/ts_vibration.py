import numpy as np
from TCutility.results import read

# temp
from yutility import molecule
def extract_rc_from_xyz(calc_dir):
    inputmol = molecule.load(calc_dir + '/input_mol.xyz')
    return np.array([[idx+1 for idx in molecule.get_labeled_atoms(inputmol['molecule'], 'active_atoms_0', return_idx=True)] + [1]])

def atom_distance(molecule, atom1, atom2):
    res = 0.0
    for i,j in zip(molecule[atom1],molecule[atom2]):
        res += (i - j)**2
    return np.sqrt(res)

def relative_bond_length_delta(base,pos,neg,a1,a2):
    basedist = atom_distance(base, a1+1, a2+1)
    x = abs((atom_distance(pos, a1+1, a2+1)/basedist)-1)
    y = abs((atom_distance(neg, a1+1, a2+1)/basedist)-1)
    return (x+y)/2

def determine_ts_reactioncoordinate(calc_dir, bond_tolerance=1.28, min_delta_dist=0.1):
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
                    if a < b and relative_bond_length_delta(outputmol, posvib, negvib, a, b) > min_delta_dist
                ], dtype=int)
    return rc


def validate_transitionstate(calc_dir, rcatoms = None):
    data = read(calc_dir)
    result = determine_ts_reactioncoordinate(calc_dir)

    if isinstance(rcatoms, list):
        rcatoms = np.array(rcatoms)

    if not isinstance(rcatoms, np.ndarray):
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

    # match arbitrary sign with reaction coordinate
    result[:, 2] = result[:, 2] if np.sign(result[0][2]) == rcatoms[0][2] else -result[:, 2]
    ret = np.all(result == rcatoms)    

    return ret

if __name__ == '__main__':
    file = '/Users/yumanhordijk/Koen/tcml2022/yuman/ychem/calculations2/cb564ea7b7ec6e28a09bbc474787fe71d8c0406b07a3444ae9e4e0196f3d7a1e/transitionstate'
    print(determine_ts_reactioncoordinate(file))
    print(extract_rc_from_xyz(file))
    print(validate_transitionstate(file))
    print(validate_transitionstate(file, extract_rc_from_xyz(file)))
    print(validate_transitionstate(file, [1,16,1]))
    print(validate_transitionstate(file, [[1,16,1]]))

    print('\n')

    file = '/Users/yumanhordijk/Koen/temporary_going_to_delete/ts sn2.results'
    print(determine_ts_reactioncoordinate(file))

    print('\n')

    file = '../../test/fixtures/2'
    print(determine_ts_reactioncoordinate(file))
