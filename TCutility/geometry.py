import numpy as np
from math import sin, cos
import scipy
from typing import Tuple



def get_rotation_matrix(x: float = None, y: float = None, z: float = None) -> np.ndarray:
    ''' 
    Create a rotation matrix based on the Tait-Bryant sytem.
    In this system, x, y, and z are angles of rotation around
    the corresponding axes. This function uses the right-handed 
    convention

    Args:
        x, y, z: Totation around the axes in radians.

    Returns:
        3x3 rotation matrix
    '''
    # start with identity matrix
    R = np.eye(3)

    # apply rotation around each axis separately
    if x is not None:
        c = cos(x)
        s = sin(x)
        R = R @ np.array(([1, 0, 0],
                          [0, c, -s],
                          [0, s, c]))

    if y is not None:
        c = cos(y)
        s = sin(y)
        R = R @ np.array(([c, 0, s],
                          [0, 1, 0],
                          [-s, 0, c]))

    if z is not None:
        c = cos(z)
        s = sin(z)
        R = R @ np.array(([c, -s, 0],
                          [s, c, 0],
                          [0, 0, 1]))

    return R


def apply_rotation_matrix(coords: np.ndarray, R: np.ndarray) -> np.ndarray:
    '''
    Apply a rotation matrix to a set of coordinates
    '''
    coords = np.atleast_2d(coords)
    return (R @ coords.T).T.squeeze()


def rotate(coords: np.ndarray, x: float = None, y: float = None, z: float = None) -> np.ndarray:
    '''
    Shorthand function that builds and applies a rotation matrix to a set of coordinates.
    '''
    return apply_rotation_matrix(coords, get_rotation_matrix(x, y, z))


def vector_align_rotmat(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    '''
    Calculate a rotation matrix that aligns vector a onto vector b.
    '''
    # normalize the vectors first
    a = np.array(a) / np.linalg.norm(a)
    b = np.array(b) / np.linalg.norm(b)
    
    c = a @ b
    # check if they are not already aligned
    if c == 1:
        return np.eye(3)
    if c == -1:
        raise ValueError('Inner product of a and b is 1, no rotation possible.')

    v = np.cross(a, b)
    skew = np.array([
        [0, -v[2], v[1]],
        [v[2], 0, -v[0]],
        [-v[1], v[0], 0]
    ])
    R = np.eye(3) + skew + skew @ skew / (1 + c)
    return R


class Transform:
    def __init__(self, 
                 R: np.ndarray = None, 
                 T: np.ndarray = None, 
                 S: np.ndarray = None):
        self.M = self.build_matrix(R, T, S)

    def __str__(self):
        return str(self.M)

    def translate(self, 
                  T: np.ndarray = None, 
                  x: float = None, 
                  y: float = None, 
                  z: float = None):
        '''
        Add a translation component to the transformation matrix.
        Arguments can be given as a container of x, y, z values. They can also be given separately.
        You can also specify x, y and z components separately

        Example usage:
            Transform.translate([2, 3, 0])
            Transform.translate(x=2, y=3)
        '''

        if T is None:
            T = [x or 0, y or 0, z or 0]

        self.M = self.M @ self.build_matrix(T=T)

    def rotate(self, 
               R: np.ndarray = None, 
               x: float = None, 
               y: float = None, 
               z: float = None):
        r'''
        Add a rotational component to transformation matrix.
        Arguments can be given as a rotation matrix R \in R^3x3 or by specifying the angle to rotate along the x, y or z axes
        
        Example usage:
            Transform.rotate(get_rotation_matrix(x=1, y=-1))
            Transform.rotate(x=1, y=-1)
        '''
        if R is None:
            R = get_rotation_matrix(x=x, y=y, z=z)

        self.M = self.M @ self.build_matrix(R=R)

    def scale(self, 
              S: np.ndarray = None, 
              x: float = None, 
              y: float = None, 
              z: float = None):
        '''
        Add a scaling component to the transformation matrix.
        Arguments can be given as a container of x, y, z values.
        You can also specify x, y and z components separately

        Example usage:
            Transform.scale([0, 0, 3])
            Transform.scale(z=3)
        '''

        if S is None:
            S = [x or 1, y or 1, z or 1]
        elif isinstance(S, (float, int)):
            S = [S, S, S]

        self.M = self.M @ self.build_matrix(S=S)

    def build_matrix(self, 
                     R: np.ndarray = None, 
                     T: np.ndarray = None, 
                     S: np.ndarray = None) -> np.ndarray:
        r'''
        Build and return a transformation matrix. 
        This 4x4 matrix encodes rotations, translations and scaling.

            M = | R@diag(S)   T |
                | 0_3         1 |

        where R \in R^3x3, T \in R^3x1, 0_3 = [0, 0, 0] \in R^1x3 and 1 \in R

        When applied to a positional vector [x, y, z, 1] it will apply these 
        transformations simultaneously. 

        Note: This matrix is an element of the special SE(3) Lie group.
        '''

        # set the default matrix and vectors
        R = R if R is not None else get_rotation_matrix()
        T = T if T is not None else np.array([0, 0, 0])
        S = S if S is not None else np.array([1, 1, 1])

        return np.array([
            [R[0, 0]*S[0], R[0, 1],      R[0, 2],      T[0]],
            [R[1, 0],      R[1, 1]*S[1], R[1, 2],      T[1]],
            [R[2, 0],      R[2, 1],      R[2, 2]*S[2], T[2]],
            [0,            0,            0,            1]])
        
    def __call__(self, *args, **kwargs):
        return self.apply(*args, **kwargs)

    def apply(self, v: np.ndarray) -> np.ndarray:
        r'''
        Applies the transformation matrix to vector(s) v \in R^Nx3
        v should be a series of column vectors.

        Application is a three-step process.
         1) Append row vector of ones to the bottom of v
         2) Apply the transformation matrix M \dot v
         3) Remove the bottom row vector of ones and return the result
        '''
        v = np.atleast_2d(v)
        v = np.asarray(v).T
        N = v.shape[1]
        v = np.vstack([v, np.ones(N)])
        vprime = self.M @ v
        return vprime[:3, :].T

    def __matmul__(self, other):
        if isinstance(other, Transform):
            return self.combine_transforms(other)

    def combine_transforms(self, other: 'Transform') -> 'Transform':
        '''
        Combine two different transform objects. This involves creating 
        a new Transform object and multiplying the two transform matrices
        and assigning it to the new object.
        '''

        new = Transform()
        new.M = self.M @ other.M
        return new

    def get_rotation_matrix(self):
        return self.M[:3, :3]


class KabschTransform(Transform):
    def __init__(self, 
                 X: np.ndarray, 
                 Y: np.ndarray):
        '''
        Use Kabsch-Umeyama algorithm to calculate the optimal rotation matrix and translation
        to superimpose X onto Y. 

        It is numerically stable and works when the covariance matrix is singular.
        Both sets of points must be the same size for this algorithm to work.
        The coordinates are first centered onto their centroids before determining the 
        optimal rotation matrix.

        References
            https://en.wikipedia.org/wiki/Orthogonal_Procrustes_problem
            https://en.wikipedia.org/wiki/Kabsch_algorithm
        '''

        # make sure arrays are 2d and the same size
        X, Y = np.atleast_2d(X), np.atleast_2d(Y)
        assert X.shape == Y.shape, f"Matrices X with shape {X.shape} and Y with shape {Y.shape} are not the same size"

        # center the coordinates
        centroid_x = np.mean(X, axis=0)
        centroid_y = np.mean(Y, axis=0)
        Xc = X - centroid_x
        Yc = Y - centroid_y

        # calculate covariance matrix H
        H = Xc.T @ Yc

        # first do single value decomposition on covariance matrix
        # this step ensures that the algorithm is numerically stable
        # and removes problems with singular covariance matrices
        U, _, V = scipy.linalg.svd(H)

        # get the sign of the determinant of V.T @ U.T
        sign = np.sign(np.linalg.det(V.T@U.T))
        # then build the optimal rotation matrix
        d = np.diag([1, 1, sign])
        R = V.T @ d @ U.T

        # build the transformation:
        # for a sequence of transformation operations we have to invert their order
        # We have that Y ~= (R @ (X - centroid_x).T).T + centroid_y
        # the normal order is to first translate X by -centroid_x
        # then rotate with R
        # finally translate by +centroid_y
        self.M = self.build_matrix()
        self.translate(centroid_y)
        self.rotate(R)
        self.translate(-centroid_x)


def RMSD(X: np.ndarray, 
         Y: np.ndarray,
         axis: int = None,
         use_kabsch: bool = True) -> float:
    r'''
    Calculate Root Mean Squared Deviations between two sets of points X and Y.
    By default Kabsch' algorithm is used to align the sets of points prior to calculating the RMSD.
    Optionally the axis can be given to calculate the RMSD along different axes.

    RMSD is given as

        $$ \frac{1}{N}\sqrt{\sum_i^N (X_i - Y_i)^2} $$
    
    Args:
        X, Y: Arrays to compare. They should have the same shape.
        axis: Axis to compare. Defaults to None.
        use_kabsch: Whether to use Kabsch' algorithm to align X and Y before calculating the RMSD. Defaults to True.
    
    Returns:
        RMSD in the units of X and Y.
    '''
    assert X.shape == Y.shape

    # apply Kabsch transform
    if use_kabsch:
        Tkabsch = KabschTransform(X, Y)
        X = Tkabsch(X)

    return np.sqrt(np.sum((X - Y)**2, axis=axis)/X.shape[0])


def random_points_on_sphere(shape: Tuple[int], radius: float = 1) -> np.ndarray:
    '''
    Generate a random points on a sphere with a specified radius.

    Args:
        shape: The shape of the resulting points, generally shape[0] coordinates with shape[1] dimensions
        radius: The radius of the sphere to generate the points on.

    Returns:
        Array of coordinates on a sphere.
    '''
    x = np.random.randn(*shape)
    x = x/np.linalg.norm(x, axis=1) * radius
    return x


def random_points_in_anular_sphere(shape: Tuple[int], min_radius: float = 0, max_radius: float = 1):
    '''
    Generate a random points in a sphere with specified radii.

    Args:
        shape: The shape of the resulting points, generally shape[0] coordinates with shape[1] dimensions
        min_radius: The lowest radius of the sphere to generate the points in.
        max_radius: The largest radius of the sphere to generate the points in.

    Returns:
        Array of coordinates on a sphere.
    '''
    random_radii = np.random.rand(shape[0]) * (max_radius - min_radius) + min_radius
    return random_points_on_sphere(shape, random_radii)

