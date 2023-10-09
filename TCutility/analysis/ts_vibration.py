import numpy as np
import TCutility.results as tcr
from TCutility.results import Result
from scm import plams
from scm.plams import *


from yutility import molecule
def extract_rc_from_xyz(calc_dir):
    inputmol = molecule.load(calc_dir + '/input_mol.xyz')
    return np.array([[idx+1 for idx in molecule.get_labeled_atoms(inputmol['molecule'], 'active_atoms_0', return_idx=True)] + [1]])

def atom_distance(molecule, atom1, atom2):
    res = 0.0
    for i,j in zip(molecule[atom1],molecule[atom2]):
        res += (i - j)**2
    return np.sqrt(res)

def determine_ts_reactioncoordinate(calc_dir, min_delta_dist=0.1):
    data = tcr.read(calc_dir)
    assert 'modes' in data.properties.vibrations, f'Vibrational data is required, but was not present in .rkf file'

    outputmol = data.molecule.output

    basepos = np.array(outputmol).reshape(-1,3)
    tsimode = np.array(data.properties.vibrations.modes[0]).reshape(-1,3)

    posvibmol = outputmol.copy()
    posvibmol.from_array(basepos + tsimode)
    posvibmol.guess_bonds()
    negvibmol = outputmol.copy()
    negvibmol.from_array(basepos - tsimode)
    negvibmol.guess_bonds()

    pairs = np.where(posvibmol.bond_matrix() - negvibmol.bond_matrix())
    rc = np.array(
                [   [int(a) + 1, int(b) + 1, int(np.sign(posvibmol.bond_matrix()[a][b] - negvibmol.bond_matrix()[a][b]))] 
                    for a, b in np.c_[pairs[0], pairs[1]] 
                    if a < b and abs(atom_distance(posvibmol, a+1, b+1) - atom_distance(negvibmol, a+1, b+1)) > min_delta_dist
                ])
    return rc


def validate_transitionstate(calc_dir, rcatoms = None):
    data = tcr.read(calc_dir)
    result = determine_ts_reactioncoordinate(calc_dir)

    if isinstance(rcatoms, list):
        rcatoms = np.array(rcatoms)

    if not isinstance(rcatoms, np.ndarray):
        assert 'reactioncoordinate' in data.input.transitionstatesearch, f'Reaction coordinate is a required input, but was neither provided nor present in the .rkf file'
        rcatoms = np.array([[int(float(y)) for y in x.split()[1:]] for x in data.input.transitionstatesearch.reactioncoordinate])
    
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
    print(validate_transitionstate(file, extract_rc_from_xyz(file)))

    print('\n')

    file = '/Users/yumanhordijk/Koen/temporary_going_to_delete/ts sn2.results'
    print(determine_ts_reactioncoordinate(file))

    print('\n')

    file = '../../test/fixtures/2'
    print(determine_ts_reactioncoordinate(file))
