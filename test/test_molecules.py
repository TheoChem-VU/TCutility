import os
from TCutility import molecule
from scm import plams

j = os.path.join


def test_atom_flags() -> None:
    xyzfile = j('test', 'fixtures', 'xyz', 'transitionstate_radical_addition.xyz')
    mol = molecule.load(xyzfile)
    atom = mol[2]
    assert atom.flags.origin == 'substrate'


def test_atom_tags() -> None:
    xyzfile = j('test', 'fixtures', 'xyz', 'transitionstate_radical_addition.xyz')
    mol = molecule.load(xyzfile)
    atom = mol[3]
    assert 'R1' in atom.flags.tags


def test_mol_reading() -> None:
    xyzfile = j('test', 'fixtures', 'xyz', 'transitionstate_radical_addition.xyz')
    tcmol = molecule.load(xyzfile)
    plamsmol = plams.Molecule(xyzfile)
    assert all(tcatom.symbol == plamsatom.symbol and tcatom.coords == plamsatom.coords for tcatom, plamsatom in zip(tcmol.atoms, plamsmol.atoms))


def test_mol_flags() -> None:
    xyzfile = j('test', 'fixtures', 'xyz', 'transitionstate_radical_addition.xyz')
    mol = molecule.load(xyzfile)
    assert mol.flags.task == 'TransitionStateSearch'


def test_mol_tags() -> None:
    xyzfile = j('test', 'fixtures', 'xyz', 'transitionstate_radical_addition.xyz')
    mol = molecule.load(xyzfile)
    assert 'vibrations' in mol.flags.tags
