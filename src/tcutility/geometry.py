import numpy as np
from math import sin, cos, atan2, sqrt
import scipy
from typing import Tuple, Union, Sequence
from scm import plams


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
        is_mol = isinstance(v, plams.Molecule)
        if is_mol:
            mol = v.copy()

        v = np.array(v)
        v = np.atleast_2d(v)
        v = np.asarray(v).T
        N = v.shape[1]
        v = np.vstack([v, np.ones(N)])
        vprime = self.M @ v

        if is_mol:
            mol.from_array(vprime[:3, :].T)
            return mol

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

        self.M = self._build_matrix(T=T) @ self.M

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

        self.M = self._build_matrix(R=R) @ self.M

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

        self.M = self._build_matrix(S=S) @ self.M

    def reflect(self, normal: np.ndarray = None):
        """
        Add a reflection across a plane given by a normal vector to the transformation matrix.
        The reflection is given as

        :math:`R = \\mathbb{I} - 2\\frac{nn^T}{n^Tn} \\in \\mathbb{R}^{3 \\times 3}`

        where :math:`n` is the normal vector of the plane to reflect along.

        Args:
            normal: the normal vector of the plane to reflect across. 
                If not given or ``None``, it will be set to one unit along the x-axis, i.e. a reflection along the yz-plane.

        References:
            https://en.wikipedia.org/wiki/Reflection_(mathematics)
        """
        if normal is None:
            normal = np.array([[1, 0, 0]])

        normal = np.atleast_2d(np.array(normal))

        # normalize the normal to be sure
        normal = normal.T / np.linalg.norm(normal)
        R = np.eye(3) - 2 * (normal @ normal.T) / (normal.T @ normal)
        self.M = self.M @ self._build_matrix(R=R)

    def _build_matrix(self, R: np.ndarray = None, T: np.ndarray = None, S: np.ndarray = None) -> np.ndarray:
        '''
        Build the transformation matrix for this object.
        '''
        # set the default matrix and vectors
        R = R if R is not None else get_rotmat()
        T = T if T is not None else np.array([0, 0, 0])
        S = S if S is not None else np.array([1, 1, 1])

        return np.array([[R[0, 0] * S[0], R[0, 1], R[0, 2], T[0]], [R[1, 0], R[1, 1] * S[1], R[1, 2], T[1]], [R[2, 0], R[2, 1], R[2, 2] * S[2], T[2]], [0, 0, 0, 1]])

    def get_rotmat(self):
        return self.M[:3, :3]

    def get_translation(self):
        return self.M[:3, 3]

    def to_vtkTransform(self):
        import vtk
        vtktrans = vtk.vtkTransform()
        vtktrans.PostMultiply()

        angles = rotmat_to_angles(self.get_rotmat())
        vtktrans.RotateX(angles[0] * 180 / np.pi)
        vtktrans.RotateY(angles[1] * 180 / np.pi)
        vtktrans.RotateZ(angles[2] * 180 / np.pi)

        vtktrans.Translate(self.get_translation())

        return vtktrans



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
        # We have that Y ~= (R @ (X - centroid_x).T).T + centroid_y
        # the normal order is to first translate X by -centroid_x
        # then rotate with R
        # finally translate by +centroid_y
        self.M = self._build_matrix()
        self.translate(-centroid_x)
        self.rotate(R)
        self.translate(centroid_y)


class MolTransform(Transform):
    '''
    A subclass of :class:`Transform` that is designed to generate transformation for a molecule.
    It adds, among others, methods for aligning atoms to specific vectors, planes, or setting the centroid of the molecule.
    The nice thing is that the class applies the transformations based only on the atom indices given by the user.

    Args:
        mol: the molecule that is used for the alignment.

    .. note::
        Indexing starts at 1 instead of 0.
    '''
    def __init__(self, mol: plams.Molecule):
        self.mol = mol
        super().__init__()

    def center(self, *indices):
        '''
        Center the molecule on given indices or by its centroid.

        Args:
            indices: the indices that are used to center the molecule. 
                If not given the centering will be done based on all atoms.
        '''
        tmol = self.apply(self.mol)
        if len(indices) == 0:
            indices = range(1, len(tmol) + 1)
        C = np.array([tmol.as_array()[i - 1] for i in indices])
        self.translate(-np.mean(C, axis=0))

    def align_to_vector(self, index1: int, index2: int, vector: Sequence[float] = None):
        '''
        Align the molecule such that a bond lays on a given vector.

        Args:
            index1: index of the first atom.
            index2: index of the second atom.
            vector: the vector to align the atoms to. If not given or `None` it defaults to `(1, 0, 0)`.
        '''
        # get the transformed mol
        tmol = self.apply(self.mol)
        # and coordinates
        C1, C2 = tmol.as_array()[index1 - 1], tmol.as_array()[index2 - 1]
        if vector is None:
            vector = [1, 0, 0]

        R = vector_align_rotmat(C1 - C2, vector)
        self.rotate(R)

    def align_to_plane(self, index1: int, index2: int, index3: int, vector: Sequence[float] = None):
        '''
        Align a molecule such that the normal of the plane defined by three atoms is aligned to a given vector.

        Args:
            index1: index of the first atom.
            index2: index of the second atom.
            index3: index of the third atom.
            vector: the vector to align the atoms to. If not given or `None` it defaults to (0, 1, 0).
        '''
        # get the transformed mol
        tmol = self.apply(self.mol)
        # and coordinates
        C1, C2, C3 = tmol.as_array()[index1 - 1], tmol.as_array()[index2 - 1], tmol.as_array()[index3 - 1]
        if vector is None:
            vector = [0, 1, 0]

        # calculate normal vector and align it to the given vector
        n = np.cross(C1 - C2, C3 - C2)
        R = vector_align_rotmat(n, vector)
        self.rotate(R)


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


def rotmat_to_angles(R: np.ndarray) -> Tuple[float]:
    thetax = atan2(R[2, 1], R[2, 2])
    thetay = atan2(-R[2, 0], sqrt(R[2, 1]**2 + R[2, 2]**2))
    thetaz = atan2(R[1, 0], R[0, 0])
    return thetax, thetay, thetaz


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


def RMSD(X: np.ndarray, Y: np.ndarray, axis: Union[int, None] = None, use_kabsch: bool = True, include_mirror: bool = False) -> float:
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
        include_mirror: return the lowest value between the RMSD of the supplied coordinates and also the RMSD of mirrored X with Y.
            This will only be done if ``use_kabsch == True``.

    Returns:
        RMSD in the units of X and Y. If ``axis`` is set to an integer this function will return a vector of RMSD's along that axis.

    .. note::
        It is generally recommended to enable the use of the Kabsch-Umeyama algorithm prior to calculating the RMSD. 
        This will ensure you get the lowest possible RMSD for you sets of coordinates.

    .. seealso::
        :class:`KabschTransform`
    """

    X = np.array(X)
    Y = np.array(Y)

    assert X.shape == Y.shape

    # apply Kabsch transform
    if use_kabsch:
        Tkabsch = KabschTransform(X, Y)
        Xprime = Tkabsch(X)

    rmsd = np.sqrt(np.sum((Xprime - Y) ** 2, axis=axis) / X.shape[0])

    # if we include the mirror image we have to apply a reflection to the coordinates
    # and then recalculate the kabsch transform in the mirror coordinates
    # then we calculate the new RMSD and take the smaller of the new and old RMSD
    if include_mirror and use_kabsch:
        Tmirror = Transform()
        Tmirror.reflect()
        Tkabsch_mirror = KabschTransform(Tmirror(X), Y)
        Xprime = Tkabsch_mirror(Tmirror(X))
        rmsd_mirrored = np.sqrt(np.sum((Xprime - Y) ** 2, axis=axis) / X.shape[0])
        rmsd = min(rmsd, rmsd_mirrored)

    return rmsd


def random_points_on_sphere(shape: Tuple[int], radius: float = 1) -> np.ndarray:
    """
    Generate random points on a sphere with a specified radius.

    Args:
        shape: The shape of the resulting points, generally shape[0] coordinates with shape[1] dimensions
        radius: The radius of the sphere to generate the points on.

    Returns:
        Array of coordinates on a sphere.
    """
    x = np.random.randn(*shape)
    x = x / np.linalg.norm(x, axis=1, keepdims=True) * radius
    return x


def random_points_in_anular_sphere(shape: Tuple[int], min_radius: float = 0, max_radius: float = 1):
    """
    Generate random points in an sphere or anular sphere with specified radii. 
    An anular sphere is a hollow sphere of a certain thickness.

    Args:
        shape: The shape of the resulting points, generally shape[0] coordinates with shape[1] dimensions
        min_radius: The lowest radius of the sphere to generate the points in.
        max_radius: The largest radius of the sphere to generate the points in.

    Returns:
        Array of coordinates on a sphere.
    """
    random_radii = np.random.rand(shape[0]) * (max_radius - min_radius) + min_radius
    return random_points_on_sphere(shape, random_radii)


def random_points_on_spheroid(coordinates: np.ndarray, Nsamples: int = 1, margin: float = 0):
    """
    Generate random points on a spheroid generated by a set of coordinates.

    Args:
        coordinates: The (n x dim) set of coordinates that is used to generate the minimum-volume spheroid.
        Nsamples: The number of samples to return.
        margin: the spacing between the sampling spheroid and the minimum-volume spheroid.

    Returns:
        Array of coordinates on a spheroid.
    """
    # for this to work we should first get the centroid of our molecule
    centroid = np.mean(coordinates, axis=0)
    # and get the centered coordiantes
    Xc = coordinates - centroid

    # we then do a singular-value decomposition to obtain
    # the three principle components (Vh) with their eigenvalues (s)
    _, s, Vh = scipy.linalg.svd(Xc)

    # then compute a transformation matrix for generating the correct spheroid
    transform = Transform()
    transform.translate(centroid)
    transform.rotate((np.diag(s/2 + margin) @ Vh).T)

    # to sample the spheroid we generate points on a 
    # sphere and transform them to our spheroid
    p = random_points_on_sphere((Nsamples, Xc.shape[1]))
    return transform(p)


def parameter(coordinates, *indices, pyramidal=False):
    '''
    Return geometry information about a set of coordinates given indices.
    '''
    assert 1 <= len(indices) <= 4, "Number of indices must be between 1, 2, 3 or 4"

    coordinates = np.array(coordinates)
    selected_coords = [coordinates[i] for i in indices]

    if len(indices) == 1:
        return selected_coords[0]

    if len(indices) == 2:
        return np.linalg.norm(selected_coords[0] - selected_coords[1])

    if len(indices) == 3:
        a = selected_coords[0] - selected_coords[1]
        b = selected_coords[2] - selected_coords[1]
        a = a / np.linalg.norm(a)
        b = b / np.linalg.norm(b)

        return np.arccos(a @ b) / np.pi * 180

    if len(indices) == 4 and not pyramidal:
        a = selected_coords[0] - selected_coords[1]
        b = selected_coords[2] - selected_coords[1]

        u = selected_coords[1] - selected_coords[2]
        v = selected_coords[3] - selected_coords[2]

        n1, n2 = np.cross(a, b), np.cross(u, v)

        n1 = n1 / np.linalg.norm(n1)
        n2 = n2 / np.linalg.norm(n2)

        return np.arccos(n1 @ n2) / np.pi * 180


    if len(indices) == 4 and pyramidal:
        ang1 = parameter(coordinates, indices[1], indices[0], indices[2])
        ang2 = parameter(coordinates, indices[2], indices[0], indices[3])
        ang3 = parameter(coordinates, indices[3], indices[0], indices[1])

        return 360 - ang1 - ang2 - ang3
