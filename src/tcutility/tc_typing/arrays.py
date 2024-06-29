from typing import TypeVar
import numpy.typing as npt
import numpy as np

DType = TypeVar("DType", bound=np.generic)
Array1D = npt.NDArray[DType]
Array2D = npt.NDArray[DType]
Array3D = npt.NDArray[DType]
