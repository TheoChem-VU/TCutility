from TCutility import geometry
import numpy as np


def test_rotation_matrix():
	test_rot = np.array([[-0.3587314, -0.0511359,  0.9320391],
  						 [-0.2293407, -0.9630634, -0.1411088],
  						 [ 0.9048285, -0.2643747,  0.3337536]]).round(5)
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
	a = np.random.rand(3)*20-10
	b = np.random.rand(3)*20-10

	R = geometry.vector_align_rotmat(a, b)

	a = a/np.linalg.norm(a)
	b = b/np.linalg.norm(b)

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



if __name__ == '__main__':
	import pytest
	pytest.main()
