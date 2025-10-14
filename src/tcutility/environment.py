import functools
import os
from importlib.util import find_spec
from typing import Optional

from tcutility import errors


def requires_optional_package(package_name: str, os_name: Optional[str] = None):
    """
    Ensures a given package is available before running a function, otherwise raises an ImportError.
    This can be used to check for optional dependencies which are required for specific functionality.

    Arguments:
        package_name (str): name of the required package
        os_name (Optional[str]): name of the os that this package must be specified on, if omitted defaults to all os
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if (os_name is None or os.name == os_name) and find_spec(package_name) is None:
                raise errors.MissingOptionalPackageError(package_name)
            return func(*args, **kwargs)

        return wrapper

    return decorator
