import numpy as np
import TCutility.results
from TCutility.results import Result

def active_atom_vibrations(calc_dir: str) -> Result:
    '''
    Function to get 

    Args:
        calc_dir: path pointing to the desired calculation.

    Returns:
        : :

            - **number_of_atoms (int)** – number of atoms in the molecule.

    '''
    #assert data.transitionstate.reaction_coordinate, "transitionstate only"

    data = TCutility.results.read(calc_dir)
    #data.update(ams.get_molecules(calc_dir))
    rcatoms = data.TransitionStateSearch.ReactionCoordinate

    previbmol = data.output
    postvibmol = previbmol.copy()
    vibrationslist = np.array(data.vibrations.modes).reshape(-1,3)

    pairs = []
    reaction_coordinate = 0.00



if __name__ == '__main__':
	active_atom_vibrations('../test/fixtures/2')

''' 

def find_bonds_from_transitionstate(rkf: plams.KFFile, previbmol=None, num_bonds_formed=1, bond_order=1, max_rc=2, granularity=0.05, conv_AngAu=False):
    angtoau = 1.8897259886 if conv_AngAu else 1
    if previbmol == None:
        previbmol = Molecule()._mol_from_rkf_section(rkf.read_section('Molecule'))
    
    coordslist = np.array(previbmol).reshape(-1,3)/angtoau

    try:
        vibrationslist = np.array(rkf.read_section('Vibrations')['NoWeightNormalMode(1)']).reshape(-1,3)/angtoau
    except KeyError:
        #print(f'Warning: No transition state vibrations found', end='')
        return [(0,0)]

    previbmol.guess_bonds()
    bond_tolerance = 1.28
    while len(previbmol.separate()) < 2:
        bond_tolerance -= 0.01
        previbmol.guess_bonds(dmax=bond_tolerance)

    postvibmol = previbmol.copy()
    broke_loop = False
    pairs = []
    reaction_coordinate = 0.00
    while len(pairs)/2 < num_bonds_formed:
        if reaction_coordinate > max_rc:
            broke_loop = True
            break
        reaction_coordinate += granularity
        postvib = (coordslist + reaction_coordinate * vibrationslist)
        postvibmol.from_array(postvib)
        postvibmol.guess_bonds(dmax=bond_tolerance)
        bonded_atoms = np.where(postvibmol.bond_matrix() - previbmol.bond_matrix() == bond_order)
        pairs = [[a,b] for a,b in np.c_[bonded_atoms[0], bonded_atoms[1]] if postvibmol.bond_matrix()[a][b] == bond_order]

    if broke_loop:
        reaction_coordinate = 0.00
        while len(pairs)/2 < num_bonds_formed:
            if reaction_coordinate < -max_rc:
                return [(0,0)]
            reaction_coordinate -= granularity
            postvib = (coordslist + reaction_coordinate * vibrationslist)
            postvibmol.from_array(postvib)
            postvibmol.guess_bonds(dmax=bond_tolerance)
            bonded_atoms = np.where(postvibmol.bond_matrix() - previbmol.bond_matrix() == bond_order)
            pairs = [[a,b] for a,b in np.c_[bonded_atoms[0], bonded_atoms[1]] if postvibmol.bond_matrix()[a][b] == bond_order]

    return [(a1+1,a2+1) for (a1,a2) in pairs if a1 < a2]

def check_correct_transition(path_to_ts):
    inputfile = path_to_ts + '/input_mol.xyz'
    
    try:
        mol = Molecule(inputfile)
        rkf = plams.KFFile(j(path_to_ts, 'geometry', 'adf.rkf'))
        atom_order = rkf.read('Geometry', 'atom order index')
    except FileNotFoundError:
        return 1

    with open(inputfile, 'r') as f:
        aa_intended = [x-1 for x,l in enumerate(f) if 'active_atoms_0' in l]
        for idx, entry in enumerate(aa_intended):
            aa_intended[idx] = atom_order[len(atom_order)//2:].index(entry) + 1
        
        aa_actual = []
        for pair in find_bonds_from_transitionstate(rkf, mol):
            fixed = []
            for atom in pair:
                try:
                    fixed.append(atom_order[len(atom_order)//2:].index(atom) + 1)
                except ValueError:
                    pass
            aa_actual = fixed
    predicted_outlier = int(aa_intended == aa_actual)
    return predicted_outlier

'''
