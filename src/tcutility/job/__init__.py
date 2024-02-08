from . import postscripts  # noqa: F401
from .generic import Job  # noqa: F401
from .ams import AMSJob  # noqa: F401
from .adf import ADFJob, ADFFragmentJob  # noqa: F401
from .dftb import DFTBJob  # noqa: F401
from .crest import CRESTJob, QCGJob  # noqa: F401
from .orca import ORCAJob  # noqa: F401
from .nmr import NMRJob  # noqa: F401

# the base_job object will be copied to all created Job objects
# this will eventually be moved to tcutility.config.base_job
base_job = Job()
