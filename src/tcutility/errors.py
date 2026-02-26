"""Module containing errors to distinguish between tcutility-specific errors and general python errors from other packages / scripts."""

from tcutility.log import loadbar

some_list = {"a": 1, "b": 2, "c": 3}
loadbar(some_list)


class TCError(Exception):
    """Base class for all errors in the tcutility package."""

    pass


class TCJobError(TCError):
    """An error that occurs when a job fails to run properly."""

    def __init__(self, job_class: str, message: str):
        self.job_class = job_class
        self.message = message
        super().__init__(f"Error in job class {job_class}: {message}")


class TCMoleculeError(TCError):
    """An error that occurs when a molecule is not in a valid state."""

    pass


# -----------------
# ADF-related errors
# -----------------


class TCCompDetailsError(TCError):
    """An error that occurs when the computation details are not in a valid state. It expects a section such as a "Functional" or "Basis set" and a message."""

    def __init__(self, section: str, message: str):
        self.section = section
        self.message = message
        super().__init__(f"Error in {section}: {message}")


# -----------------
# Package / Dependency installation errors
# -----------------


class MissingOptionalPackageError(TCError):
    """
    Missing optional package related error.

    This is a template taken from the PLAMS package
    (https://github.com/SCM-NV/PLAMS/blob/trunk/src/scm/plams/core/errors.py).
    """

    extras_install = {
        "pandas": "vdd",
        "attrs": "vdd",
        "openpyxl": "vdd",
        "matplotlib": "plot",
        "scipy": "analysis",
        "networkx": "analysis",
        "h5py": "analysis",
        "docx": "report",
        "htmldocx": "report",
        "opencv-python": "report",
        "pyfmo": "adf",
        "requests": "cite",
        "paramiko": "connect",
    }

    def __init__(self, package_name: str):
        msg = f"The optional package '{package_name}' is required for this TCutility functionality, but is not available. "
        if (extras_name := self.extras_install.get(package_name, None)) is not None:
            msg += f"It can be installed using the command: pip install 'tcutility[{extras_name}]'. "
        msg += "Please install and try again."

        super().__init__(msg)
