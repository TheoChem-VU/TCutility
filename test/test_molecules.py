import os
from tcutility import molecule
from scm import plams

j = os.path.join


def test_atom_flags() -> None:
    xyzfile = j(os.path.split(__file__)[0], "fixtures", "xyz", "transitionstate_radical_addition.xyz")
    mol = molecule.load(xyzfile)
    atom = mol[2]
    assert atom.flags.origin == "substrate"


def test_atom_tags() -> None:
    xyzfile = j(os.path.split(__file__)[0], "fixtures", "xyz", "transitionstate_radical_addition.xyz")
    mol = molecule.load(xyzfile)
    atom = mol[3]
    assert "R1" in atom.flags.tags


def test_mol_reading() -> None:
    xyzfile = j(os.path.split(__file__)[0], "fixtures", "xyz", "transitionstate_radical_addition.xyz")
    tcmol = molecule.load(xyzfile)
    plamsmol = plams.Molecule(xyzfile)
    assert all(tcatom.symbol == plamsatom.symbol and tcatom.coords == plamsatom.coords for tcatom, plamsatom in zip(tcmol.atoms, plamsmol.atoms))


def test_mol_flags() -> None:
    xyzfile = j(os.path.split(__file__)[0], "fixtures", "xyz", "transitionstate_radical_addition.xyz")
    mol = molecule.load(xyzfile)
    assert mol.flags.task == "TransitionStateSearch"


def test_mol_tags() -> None:
    xyzfile = j(os.path.split(__file__)[0], "fixtures", "xyz", "transitionstate_radical_addition.xyz")
    mol = molecule.load(xyzfile)
    assert "vibrations" in mol.flags.tags


def test_comment() -> None:
    xyzfile = j(os.path.split(__file__)[0], "fixtures", "xyz", "transitionstate_radical_addition.xyz")
    mol = molecule.load(xyzfile)
    assert mol.comment == "molecule used for testing the molecule module"


def test_list_value() -> None:
    xyzfile = j(os.path.split(__file__)[0], "fixtures", "xyz", "pyr.xyz")
    mol = molecule.load(xyzfile)
    assert mol.flags.conn == [6, 12]


def test_list_value2() -> None:
    xyzfile = j(os.path.split(__file__)[0], "fixtures", "xyz", "pyr.xyz")
    mol = molecule.load(xyzfile)
    assert mol.flags.test_list == [3.14, "pi"]


def test_mol_copy() -> None:
    xyzfile = j(os.path.split(__file__)[0], "fixtures", "xyz", "pyr.xyz")
    mol = molecule.load(xyzfile)
    mol.copy()


def test_guess_fragments() -> None:
    xyzfile = j(os.path.split(__file__)[0], "fixtures", "xyz", "NaCl.xyz")
    mol = molecule.load(xyzfile)
    frags = molecule.guess_fragments(mol)
    assert frags['Na'][1].symbol == 'Na'


def test_guess_fragments2() -> None:
    xyzfile = j(os.path.split(__file__)[0], "fixtures", "xyz", "NaCl.xyz")
    mol = molecule.load(xyzfile)
    frags = molecule.guess_fragments(mol)
    assert frags['Na'].flags['charge'] == 1


def test_guess_fragments3() -> None:
    xyzfile = j(os.path.split(__file__)[0], "fixtures", "xyz", "NaCl_homolytic.xyz")
    mol = molecule.load(xyzfile)
    frags = molecule.guess_fragments(mol)
    assert frags['Cl'].flags['spinpol'] == 1


if __name__ == "__main__":
    import pytest

    pytest.main()
