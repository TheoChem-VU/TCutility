import numpy as np
from math import sin, cos
import scipy
from typing import Tuple, Union


class Transform:
    '''
    Transformation matrix that handles rotation, translation and scaling of sets of 3D coordinates.

    Build and return a transformation matrix.
    This 4x4 matrix encodes rotations, translations and scaling.
    
    :math:`\\textbf{M} = \\begin{bmatrix} \\textbf{R}\\text{diag}(S) & \\textbf{T} \\\\ \\textbf{0}_3 & 1 \\end{bmatrix}`

    where :math:`\\textbf{R} \\in \\mathbb{R}^{3 \\times 3}`, :math:`\\textbf{T} \\in \\mathbb{R}^{3 \\times 1}` and :math:`\\textbf{0}_3 = [0, 0, 0] \\in \\mathbb{R}^{1 \\times 3}`.

    When applied to a coordinates :math:`[\\textbf{x}, \\textbf{y}, \\textbf{z}, \\textbf{1}]^T \\in \\mathbb{R}^{n \\times 4}` it will apply these transformations simultaneously.
    '''
    def __init__(self):
        # initialize an empty transformation matrix
        self.M = self._build_matrix()

    def __str__(self):
        return str(self.M)

    def __call__(self, *args, **kwargs):
        return self.apply(*args, **kwargs)

    def apply(self, v: np.ndarray) -> np.ndarray:
        """
        Applies the transformation matrix to vector(s) :math:`v \\in \\mathbb{R}^{N \\times 3}`.

        Application is a three-step process:

        #. Append row vector of ones to the bottom of :math:`v`
        #. Apply the transformation matrix: :math:`\\textbf{M}v`
        #. Remove the bottom row vector of ones and return the result

        Returns:
            A new array :math:`v' = \\textbf{M}v` that has been transformed using this transformation matrix.

        .. note::

            The ``Transform.__call__()`` method redirects to this method. Calling ``transform.apply(coords)`` is the same as ``transform(coords)``.
        """
        v = np.atleast_2d(v)
        v = np.asarray(v).T
        N = v.shape[1]
        v = np.vstack([v, np.ones(N)])
        vprime = self.M @ v
        return vprime[:3, :].T

    def __matmul__(self, other):
        if isinstance(other, Transform):
            return self.combine_transforms(other)

    def combine_transforms(self, other: "Transform") -> "Transform":
        """
        Combine two different transform objects. This involves creating
        a new Transform object and multiplying the two transform matrices
        and assigning it to the new object.

        Args:
            other: the transformation matrix object to combine this one with.

        Returns:
            A new transformation matrix that is a product of the original (left side) and other (right side) matrices.

        .. note::

            The ``Transform.__matmul__()`` method redirects to this method. Calling ``new = this.combine_transforms(other)`` is the same as ``new = this @ other``.
        """
        new = Transform()
        new.M = self.M @ other.M
        return new

    def translate(self, T: np.ndarray = None, x: float = None, y: float = None, z: float = None):
        """
        Add a translation component to the transformation matrix.
        Arguments can be given as a container of x, y, z values. They can also be given separately.
        You can also specify x, y and z components separately

        Example usage:
            | ``Transform.translate([2, 3, 0])``
            | ``Transform.translate(x=2, y=3)``
        """
        if T is None:
            T = [x or 0, y or 0, z or 0]

        self.M = self.M @ self._build_matrix(T=T)

    def rotate(self, R: np.ndarray = None, x: float = None, y: float = None, z: float = None):
        r"""
        Add a rotational component to transformation matrix.
        Arguments can be given as a rotation matrix R \in R^3x3 or by specifying the angle to rotate along the x, y or z axes

        Example usage:
            | ``Transform.rotate(get_rotmat(x=1, y=-1))``
            | ``Transform.rotate(x=1, y=-1)``

        .. seealso::

            :func:`get_rotmat`
            :func:`rotate`
        """
        if R is None:
            R = get_rotmat(x=x, y=y, z=z)

        self.M = self.M @ self._build_matrix(R=R)

    def scale(self, S: np.ndarray = None, x: float = None, y: float = None, z: float = None):
        """
        Add a scaling component to the transformation matrix.
        Arguments can be given as a container of x, y, z values.
        You can also specify x, y and z components separately

        Example usage:
            | ``Transform.scale([0, 0, 3])``
            | ``Transform.scale(z=3)``
        """
        if S is None:
            S = [x or 1, y or 1, z or 1]
        elif isinstance(S, (float, int)):
            S = [S, S, S]

        self.M = self.M @ self._build_matrix(S=S)

    def _build_matrix(self, R: np.ndarray = None, T: np.ndarray = None, S: np.ndarray = None) -> np.ndarray:
        '''
        Build the transformation matrix for this object.
        '''
        # set the default matrix and vectors
        R = R if R is not None else get_rotmat()
        T = T if T is not None else np.array([0, 0, 0])
        S = S if S is not None else np.array([1, 1, 1])

        return np.array([[R[0, 0] * S[0], R[0, 1], R[0, 2], T[0]], [R[1, 0], R[1, 1] * S[1], R[1, 2], T[1]], [R[2, 0], R[2, 1], R[2, 2] * S[2], T[2]], [0, 0, 0, 1]])


class KabschTransform(Transform):
    """
    Use Kabsch-Umeyama algorithm to calculate the optimal transformation matrix :math:`T_{Kabsch}` that minimizes the 
    RMSD between two sets of coordinates :math:`X \\in \\mathbb{R}^{N \\times 3}` and :math:`Y \\in \\mathbb{R}^{N \\times 3}`, such that 
    
    :math:`\\text{arg}\\min_{T_{Kabsch}} \\text{RMSD}(T_{Kabsch}(X), Y)`

    It is numerically stable and works when the covariance matrix is singular.
    Both sets of points must be the same size for this algorithm to work.
    The coordinates are first centered onto their centroids before determining the optimal rotation matrix.

    Args:
        X: array containing the first set of coordinates. The Kabsch transformation matrix will be made such that applying it to ``X`` will yield ``Y``.
        Y: array containing the second set of coordinates. These coordinates is the target to transform to.

    .. warning::
        In principle, the Kabsch-Umeyama algorithm does not care about the dimensions of the coordinates, 
        however we will always assume 3D coordinates as that is our most common use-case. Further, the :class:`Transform` class also assumes 3D coordinates. 
        If you would like to make use of 2D or 1D Transforms we suggest you simply set the correct axes to zero.

    .. seealso::
        :class:`Transform`
            The main transformation class.

    Example:

        .. code-block:: python

            from tcutility import geometry
            import numpy as np
    
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


    References:
        | https://en.wikipedia.org/wiki/Orthogonal_Procrustes_problem
        | https://en.wikipedia.org/wiki/Kabsch_algorithm
    """
    def __init__(self, X: np.ndarray, Y: np.ndarray):
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
        sign = np.sign(np.linalg.det(V.T @ U.T))
        # then build the optimal rotation matrix
        d = np.diag([1, 1, sign])
        R = V.T @ d @ U.T

        # build the transformation:
        # for a sequence of transformation operations we have to invert their order
        # We have that Y ~= (R @ (X - centroid_x).T).T + centroid_y
        # the normal order is to first translate X by -centroid_x
        # then rotate with R
        # finally translate by +centroid_y
        self.M = self._build_matrix()
        self.translate(centroid_y)
        self.rotate(R)
        self.translate(-centroid_x)


def get_rotmat(x: float = None, y: float = None, z: float = None) -> np.ndarray:
    """
    Create a rotation matrix based on the Tait-Bryant sytem.
    In this system, x, y, and z are angles of rotation around
    the corresponding axes. This function uses the right-handed
    convention

    Args:
        x: Rotation around the x-axis in radians.
        y: Rotation around the y-axis in radians.
        z: Rotation around the z-axis in radians.

    Returns:
        the rotation matrix :math:`\\textbf{R} \\in \\mathbb{R}^{3 \\times 3}` with the specified axis rotations.


    .. seealso::

        :func:`apply_rotmat`
            For applying the rotation matrix to coordinates.

        :func:`rotate`
            For rotating coordinates directly, given Tait-Bryant angles.

        :meth:`Transform.rotate`
            The :class:`Transform` class allows you to also rotate.
    """
    # start with identity matrix
    R = np.eye(3)

    # apply rotation around each axis separately
    if x is not None:
        c = cos(x)
        s = sin(x)
        R = R @ np.array(([1, 0, 0], [0, c, -s], [0, s, c]))

    if y is not None:
        c = cos(y)
        s = sin(y)
        R = R @ np.array(([c, 0, s], [0, 1, 0], [-s, 0, c]))

    if z is not None:
        c = cos(z)
        s = sin(z)
        R = R @ np.array(([c, -s, 0], [s, c, 0], [0, 0, 1]))

    return R


def apply_rotmat(coords: np.ndarray, R: np.ndarray) -> np.ndarray:
    """
    Apply a rotation matrix to a set of coordinates.

    Args:
        coords: the coordinates :math`\\in \\mathbb{R}^{n \\times 3}` to rotate.
        R: the rotation matrix to apply. 

    Returns:
        New coordinates :math`\\in \\mathbb{R}^{n \\times 3}` rotated using the given rotation matrix.

    .. seealso::

        :func:`get_rotmat`
            For creating a rotation matrix.

        :func:`rotate`
            For rotating coordinates directly, given Tait-Bryant angles.
    """
    coords = np.atleast_2d(coords)
    return (R @ coords.T).T.squeeze()


def rotate(coords: np.ndarray, x: float = None, y: float = None, z: float = None) -> np.ndarray:
    """
    Build and apply a rotation matrix to a set of coordinates.

    Args:
        coords: the coordinates :math`\\in \\mathbb{R}^{n \\times 3}` to rotate.
        x: Rotation around the x-axis in radians.
        y: Rotation around the y-axis in radians.
        z: Rotation around the z-axis in radians.

    .. seealso::
        :func:`get_rotmat`
            For creating a rotation matrix.
    """
    return apply_rotmat(coords, get_rotmat(x, y, z))


def vector_align_rotmat(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    Calculate a rotation matrix that aligns vector a onto vector b.

    Args:
        a: vector that is to be aligned.
        b: vector that is the target of the alignment.

    Returns:
        Rotation matrix R, such that ``geometry.apply_rotmat(a, R) == b``.
    """
    # normalize the vectors first
    a = np.array(a) / np.linalg.norm(a)
    b = np.array(b) / np.linalg.norm(b)

    c = a @ b
    if c == 1:
        # if a == b we simply return the identity matrix
        return np.eye(3)
    if c == -1:
        # when a == -b we cannot directly calculate R, as 1/(1+c) is undefined
        # instead, we first create a random rotation matrix and apply it to a
        # to get a new vector aprime. We then align aprime to b, which is possible since aprime != -b
        # to get the final rotation matrix we simply multiply the random and alignment rotation matrices
        Rrand = get_rotmat(np.pi / 3, np.pi / 3, np.pi / 3)
        return vector_align_rotmat(apply_rotmat(a, Rrand), b) @ Rrand

    v = np.cross(a, b)
    skew = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    R = np.eye(3) + skew + skew @ skew / (1 + c)
    return R


def RMSD(X: np.ndarray, Y: np.ndarray, axis: Union[int, None] = None, use_kabsch: bool = True) -> float:
    r"""
    Calculate Root Mean Squared Deviations between two sets of points ``X`` and ``Y``.
    By default Kabsch' algorithm is used to align the sets of points prior to calculating the RMSD.
    Optionally the axis can be given to calculate the RMSD along different axes.

    RMSD is given as

    :math:`\text{RMSD}(X, Y) = \frac{1}{N}\sqrt{\sum_i^N (X_i - Y_i)^2}`

    when using the Kabsch algorithm to align the two sets of coordinates we first obtain the :class:`KabschTransform` :math:`T_{Kabsch}` and then

    :math:`\text{RMSD}(X, Y) = \frac{1}{N}\sqrt{\sum_i^N (T_{Kabsch}(X_i) - Y_i)^2}`

    Args:
        X: the first set of coordinates to compare. It must have the same dimensions as ``Y``.
        Y: the second set of coordinates to compare. It must have the same dimensions as ``X``.
        axis: axis to compare. Defaults to ``None``. 
        use_kabsch: whether to use Kabsch' algorithm to align ``X`` and ``Y`` before calculating the RMSD. Defaults to ``True``.

    Returns:
        RMSD in the units of X and Y. If ``axis`` is set to an integer this function will return a vector of RMSD's along that axis.

    .. note::
        It is generally recommended to enable the use of the Kabsch-Umeyama algorithm prior to calculating the RMSD. 
        This will ensure you get the lowest possible RMSD for you sets of coordinates.

    .. seealso::
        :class:`KabschTransform`
    """
    assert X.shape == Y.shape

    # apply Kabsch transform
    if use_kabsch:
        Tkabsch = KabschTransform(X, Y)
        X = Tkabsch(X)

    return np.sqrt(np.sum((X - Y) ** 2, axis=axis) / X.shape[0])


def random_points_on_sphere(shape: Tuple[int], radius: float = 1) -> np.ndarray:
    """
    Generate a random points on a sphere with a specified radius.

    Args:
        shape: The shape of the resulting points, generally shape[0] coordinates with shape[1] dimensions
        radius: The radius of the sphere to generate the points on.

    Returns:
        Array of coordinates on a sphere.
    """
    x = np.random.randn(*shape)
    x = x / np.linalg.norm(x, axis=1) * radius
    return x


def random_points_in_anular_sphere(shape: Tuple[int], min_radius: float = 0, max_radius: float = 1):
    """
    Generate a random points in a sphere with specified radii.

    Args:
        shape: The shape of the resulting points, generally shape[0] coordinates with shape[1] dimensions
        min_radius: The lowest radius of the sphere to generate the points in.
        max_radius: The largest radius of the sphere to generate the points in.

    Returns:
        Array of coordinates on a sphere.
    """
    random_radii = np.random.rand(shape[0]) * (max_radius - min_radius) + min_radius
    return random_points_on_sphere(shape, random_radii)
