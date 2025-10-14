from typing import TypeVar

import numpy as np
import numpy.typing as npt

DType = TypeVar("DType", bound=np.generic)
Array1D = npt.NDArray[DType]
Array2D = npt.NDArray[DType]
Array3D = npt.NDArray[DType]


ensure_list = lambda x: [x] if not isinstance(x, (list, tuple, set)) else list(x)  # noqa: E731
squeeze_list = lambda x: x[0] if len(x) == 1 else x  # noqa: E731


def ensure_2d(x, transposed=False):
    x = ensure_list(x)
    if transposed:
        if not isinstance(x[0], (list, tuple, set)):
            x = [ensure_list(x)]
        else:
            x = [ensure_list(y) for y in x]
    else:
        x = [ensure_list(y) for y in x]
    return x
