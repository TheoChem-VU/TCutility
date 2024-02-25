from scm import plams
from tcutility.results import result
from tcutility import ensure_list
from typing import Dict

def parse_str(s: str):
    # checks if string should be an int, float, bool or string

    # sanitization first
    # empty s returns None
    # if s is not a str return it
    if s == "":
        return None
    if not isinstance(s, str):
        return s

    if "," in s:
        return [parse_str(part.strip()) for part in s.split(",")]

    # to parse the string we use try/except method
    try:
        return int(s)
    except ValueError:
        pass

    try:
        return float(s)
    except ValueError:
        pass

    # bool type casting always works, so we have to specifically check for correct strings
    if s in ["True", "False"]:
        return bool(s)

    return s


def save(mol: plams.Molecule, path: str, comment: str = None):
    """Save a molecule in a custom xyz file format.
    Molecule and atom flags can be provided as the "flags" parameter of the object (mol.flags and atom.flags).
    """
    comment = comment or mol.comment
    with open(path, "w+") as f:
        f.write(f"{len(mol.atoms)}\n{comment}\n")
        for atom in mol.atoms:
            flags_str = ""
            flags = atom.flags if hasattr(atom, "flags") else {}
            for key, value in flags.items():
                if key == "tags":
                    if len(value) > 0:
                        flags_str += " ".join([str(x) for x in value]) + " "
                    else:
                        continue
                else:
                    flags_str += f"{key}={value} "

            f.write(f"{atom.symbol}\t{atom.coords[0]: .10f}\t{atom.coords[1]: .10f}\t{atom.coords[2]: .10f}\t{flags_str}\n")

        f.write("\n")

        flags = mol.flags if hasattr(mol, "flags") else {}
        for key, value in flags.items():
            if key == "tags":
                f.write("\n".join([str(x) for x in value]) + "\n")
            else:
                f.write(f"{key} = {value}\n")


def load(path) -> plams.Molecule:
    """
    Load a molecule from a given xyz file path.
    The xyz file is structured as follows:

    .. code-block::

        [int]
        Comment line
        [str] [float] [float] [float] atom_tag1 atom_tag2 atom_key1=...
        [str] [float] [float] [float] atom_tag1 atom_tag2 atom_key1=...
        [str] [float] [float] [float]

        mol_tag1
        mol_tag2
        mol_key1=...
        mol_key2 = ...


    The xyz file is parsed and returned as a :class:`plams.Molecule <plams.mol.molecule.Molecule>` object.
    Flags and tags are given as ``mol.flags`` and ``mol.flags.tags`` respectively.
    Similarly for the atoms, the flags and tags are given as ``mol.atoms[i].flags`` and ``mol.atoms[i].flags.tags``
    """

    def parse_flags(args):
        ret = result.Result()
        ret.tags = set()
        for arg in args:
            # flags are given as key=value pairs
            # tags are given as loose keys
            if "=" in arg:
                key, value = arg.split("=")
                ret[key.strip()] = parse_str(value.strip())
            else:
                ret.tags.add(parse_str(arg.strip()))
        return ret

    with open(path) as f:
        lines = [line.strip() for line in f.readlines()]

    mol = plams.Molecule()

    natoms = int(lines[0])
    mol.comment = lines[1]
    # not all lines in the file will define atoms. Lines after line natoms+2 will be used for flags
    atom_lines = lines[2 : natoms + 2]
    for line in atom_lines:
        # parse every atom first
        symbol, x, y, z, *args = line.split()
        atom = plams.Atom(symbol=symbol, coords=(float(x), float(y), float(z)))
        atom.flags = parse_flags(args)
        mol.add_atom(atom)

    # after the atoms we parse the flags for the molecule
    flag_lines = lines[natoms + 2 :]
    flag_lines = [line.strip() for line in flag_lines if line.strip()]
    mol.flags = parse_flags(flag_lines)

    return mol


def guess_fragments(mol: plams.Molecule) -> Dict[str, plams.Molecule]:
    '''
    Guess fragments based on data from the xyz file. Two methods are currently supported, see the tabs below. 
    We also support reading of charges and spin-polarizations for the fragments. 
    They should be given as ``charge_{fragment_name}`` and ``spinpol_{fragment_name}`` respectively.
    
    
    .. tabs::
        
        .. group-tab:: First method

            .. code-block::

                8

                N       0.00000000       0.00000000      -0.81474153 
                B      -0.00000000      -0.00000000       0.83567034 
                H       0.47608351      -0.82460084      -1.14410295 
                H       0.47608351       0.82460084      -1.14410295 
                H      -0.95216703       0.00000000      -1.14410295 
                H      -0.58149793       1.00718395       1.13712667 
                H      -0.58149793      -1.00718395       1.13712667 
                H       1.16299585      -0.00000000       1.13712667 

                frag_Donor = 1, 3-5
                frag_Acceptor = 2, 6-8
                charge_Donor = -1
                spinpol_Acceptor = 2
            
            In this case, fragment atom indices must be provided below the coordinates. 
            The fragment name must be prefixed with ``frag_``. Indices can be given as integers or as ranges using ``-``.
        
        .. group-tab:: Second method

            .. code-block::

                8

                N       0.00000000       0.00000000      -0.81474153 frag=Donor
                B      -0.00000000      -0.00000000       0.83567034 frag=Acceptor
                H       0.47608351      -0.82460084      -1.14410295 frag=Donor
                H       0.47608351       0.82460084      -1.14410295 frag=Donor
                H      -0.95216703       0.00000000      -1.14410295 frag=Donor
                H      -0.58149793       1.00718395       1.13712667 frag=Acceptor
                H      -0.58149793      -1.00718395       1.13712667 frag=Acceptor
                H       1.16299585      -0.00000000       1.13712667 frag=Acceptor

                charge_Donor = -1
                spinpol_Acceptor = 2
            
            In this case, fragment atoms are marked with the `frag` flag which gives the name of the fragment the atom belongs to.

    Args:
        mol: the molecule that is to be split into fragments. It should have defined either method shown above. 
             If it does not define these methods this function returns ``None``.

    Returns:
        A dictionary containing fragment names as keys and :class:`plams.Molecule <scm.plams.mol.molecule.Molecule>` objects as values. 
        Atoms that were not included by either method will be placed in the molecule object with key ``None``.

    '''

    # first method, check if the fragments are defined as molecule flags
    fragment_flags = [flag for flag in mol.flags if flag.startswith('frag_')]
    if len(fragment_flags) > 0:
        # we split here to get of the frag_ prefix
        fragment_mols = {frag.split('_', 1)[1]: plams.Molecule() for frag in fragment_flags}
        for frag in fragment_flags:
            frag_name = frag.split('_', 1)[1]
            indices = []
            index_line = ensure_list(mol.flags[frag])
            for indx in index_line:
                if isinstance(indx, int):
                    indices.append(indx)
                elif isinstance(indx, str) and '-' in indx:
                    indices.extend(range(int(indx.split('-')[0]), int(indx.split('-')[1]) + 1))
                else:
                    raise ValueError(f'Fragment index {indx} could not be parsed.')

            [fragment_mols[frag_name].add_atom(mol[i]) for i in indices]
            fragment_mols[frag_name].flags = {'tags': set()}
            if f'charge_{frag_name}' in mol.flags:
                fragment_mols[frag_name].flags['charge'] = mol.flags[f'charge_{frag_name}']
            if f'spinpol_{frag_name}' in mol.flags:
                fragment_mols[frag_name].flags['spinpol'] = mol.flags[f'spinpol_{frag_name}']

        return fragment_mols

    # second method, check if the atoms have a frag= flag defined
    fragment_names = set(atom.flags.get('frag') for atom in mol)
    if len(fragment_names) > 0:
        fragment_mols = {name: plams.Molecule() for name in fragment_names}
        for atom in mol:
            # get the fragment the atom belongs to and add it to the list
            fragment_mols[atom.flags.get('frag')].add_atom(atom)

        for frag in fragment_names:
            fragment_mols[frag].flags = {'tags': set()}
            if f'charge_{frag}' in mol.flags:
                fragment_mols[frag].flags['charge'] = mol.flags[f'charge_{frag}']
            if f'spinpol_{frag}' in mol.flags:
                fragment_mols[frag].flags['spinpol'] = mol.flags[f'spinpol_{frag}']

        return fragment_mols



if __name__ == "__main__":
    # mol = load(r"D:\Users\Yuman\Desktop\PhD\ychem\calculations2\5ef3a511141a993d83552515df6bf882a7560dd806f88df4e2c2887b4d2a9595\transitionstate\input_mol.xyz")
    mol = load('../../examples/job/NH3BH3.xyz')
    frags = guess_fragments(mol)
    print(frags)