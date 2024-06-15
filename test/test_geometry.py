from tcutility import geometry
from scm import plams
import numpy as np


def test_rotation_matrix():
    test_rot = np.array([[-0.3587314, -0.0511359, 0.9320391], [-0.2293407, -0.9630634, -0.1411088], [0.9048285, -0.2643747, 0.3337536]]).round(5)
    assert (geometry.get_rotmat(0.4, 1.2, 3).round(5) == test_rot).all()


def test_apply_rotmat():
    R = geometry.get_rotmat(y=np.pi)
    a = np.array([1, 0, 0])
    assert (geometry.apply_rotmat(a, R).round(5) == np.array([-1, 0, 0])).all()


def test_apply_rotmat2():
    R = geometry.get_rotmat()
    a = np.array([1, 0, 0])
    assert (geometry.apply_rotmat(a, R).round(5) == a).all()


def test_apply_rotmat3():
    R = geometry.get_rotmat(y=np.pi)
    a = np.array([[1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0]])
    b = np.array([[-1, 0, 0], [-1, 0, 0], [-1, 0, 0], [-1, 0, 0]])
    assert (geometry.apply_rotmat(a, R).round(5) == b).all()


def test_apply_rotate():
    a = np.array([1, 0, 0])
    assert (geometry.rotate(a, y=np.pi).round(5) == np.array([-1, 0, 0])).all()


def test_apply_rotate2():
    a = np.array([1, 0, 0])
    assert (geometry.rotate(a).round(5) == a).all()


def test_apply_rotate3():
    a = np.array([[1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0]])
    b = np.array([[-1, 0, 0], [-1, 0, 0], [-1, 0, 0], [-1, 0, 0]])
    assert (geometry.rotate(a, y=np.pi).round(5) == b).all()


def test_vector_align_rotmat():
    a = np.random.rand(3) * 20 - 10
    b = np.random.rand(3) * 20 - 10

    R = geometry.vector_align_rotmat(a, b)

    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)

    assert (geometry.apply_rotmat(a, R).round(5) == b.round(5)).all()


def test_vector_align_rotmat2():
    a = np.array([1, 0, 0])
    b = np.array([1, 0, 0])

    R = geometry.vector_align_rotmat(a, b)
    assert (R.round(5) == np.eye(3)).all()


def test_vector_align_rotmat3():
    a = np.array([-1, 0, 0])
    b = np.array([1, 0, 0])

    R = geometry.vector_align_rotmat(a, b)
    assert (geometry.apply_rotmat(a, R).round(5) == b.round(5)).all()


def test_transform():
    # create two arrays that are the same
    X, Y = np.arange(5 * 3).reshape(5, 3), np.arange(5 * 3).reshape(5, 3)  

    # create a transformation matrix to change X
    Tx = geometry.Transform()
    Tx.rotate(x=1, y=1, z=1)
    Tx.translate(x=1, y=1, z=1)

    X = Tx(X)
    
    # get the Kabsch transformation matrix
    Tkabsch = geometry.KabschTransform(X, Y)

    # check if applying the transformation matrix to X yields Y
    assert np.isclose(Tkabsch(X), Y).all()


def test_transform2():
    # create two arrays that are the same
    X, Y = np.arange(5 * 3).reshape(5, 3), np.arange(5 * 3).reshape(5, 3)  

    # get the Kabsch transformation matrix
    Tkabsch = geometry.KabschTransform(X, Y)

    # check if applying the transformation matrix to X yields Y
    assert np.isclose(Tkabsch(X), Y).all()


def test_transform_mol():
    inp = """H       0.00000000       0.00000000       0.38278869
             H       0.00000000       0.00000000      -0.38278869"""

    mol = plams.Molecule()
    for line in inp.splitlines():
        symbol, x, y, z = line.strip().split()
        mol.add_atom(plams.Atom(symbol=symbol, coords=[x, y, z]))

    # translate the molecule
    T = geometry.Transform()
    T.translate([0, 0, 0.38278869])

    # check if the second atom is centered on the origin
    assert T(mol).atoms[1].coords == (0.0, 0.0, 0.0)


def test_transform_mol2():
    inp = """H       0.00000000       0.00000000       0.38278869
             H       0.00000000       0.00000000      -0.38278869"""

    mol = plams.Molecule()
    for line in inp.splitlines():
        symbol, x, y, z = line.strip().split()
        mol.add_atom(plams.Atom(symbol=symbol, coords=[x, y, z]))

    # reflect the molecule on the yz-plane
    T = geometry.Transform()
    T.reflect([0, 0, 1])
    # check if the second atom is not in the first atoms position
    assert T(mol).atoms[1].coords == (0.0, 0.0, 0.38278869)


if __name__ == "__main__":
    import pytest

    pytest.main()
