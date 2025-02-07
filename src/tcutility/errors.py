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
