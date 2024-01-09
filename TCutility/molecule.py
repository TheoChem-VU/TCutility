from scm import plams
from TCutility.results import result


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

        ```
        [int] number of atoms
        Comment line
        Xx X1 Y1 Z1 atom_tag1 atom_tag2 atom_key1=...
        Xx X2 Y2 Z2 atom_tag1 atom_tag2 atom_key1=...
        Xx X3 Y3 Z3

        mol_tag1
        mol_tag2
        mol_key1=...
        mol_key2 = ...
        ```

    The xyz file is parsed and returned as a plams.Molecule object.
    Flags and tags are given as mol.flags and mol.flags.tags respectively
    Similarly for the atoms, the flags and tags are given as mol.atoms[i].flags and mol.atoms[i].flags.tags
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


if __name__ == "__main__":
    mol = load(r"D:\Users\Yuman\Desktop\PhD\ychem\calculations2\5ef3a511141a993d83552515df6bf882a7560dd806f88df4e2c2887b4d2a9595\transitionstate\input_mol.xyz")
    print(mol)
    print(mol.flags)
    print(mol[1].flags)
