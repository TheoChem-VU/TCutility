"""
This module provides basic and general information about calculations done using AMS given a calculation directory.
This includes information about the engine used (ADF, DFTB, BAND, ...), general information such as timings, files, status of the calculation, etc.
This information is used in further analysis programs.

"""

from typing import Union

from . import result

Result = result.Result

import os  # noqa: E402
import pathlib as pl  # noqa: E402

from .. import slurm  # noqa: E402
from . import adf, ams, cache, dftb, orca, xtb, crest  # noqa: E402


def get_info(calc_dir: str):
    try:
        return ams.get_ams_info(calc_dir)
    except:  # noqa
        pass

    try:
        return orca.get_info(calc_dir)
    except:  # noqa
        pass

    try:
        return xtb.get_info(calc_dir)
    except:  # noqa
        pass

    try:
        return crest.get_info(calc_dir)
    except:  # noqa
        pass


    res = Result()

    # if we cannot correctly read the info, we return some generic result object
    # before that, we check the job status by checking slurm
    if slurm.workdir_info(os.path.abspath(calc_dir)):
        res.engine = "unknown"

        state = slurm.workdir_info(os.path.abspath(calc_dir)).statuscode
        state_name = {"CG": "COMPLETING", "CF": "CONFIGURING", "PD": "PENDING", "R": "RUNNING"}.get(state, "UNKNOWN")

        res.status.fatal = False
        res.status.name = state_name
        res.status.code = state
        res.status.reasons = []
    else:
        res.engine = "unknown"
        res.status.fatal = True
        res.status.name = "UNKNOWN"
        res.status.code = "U"
        res.status.reasons = []

        # give a little more specific information about the error
        if not os.path.exists(calc_dir):
            res.status.reasons.append(f"Could not find folder {calc_dir}")
        elif not os.path.isdir(calc_dir):
            res.status.reasons.append(f"Path {calc_dir} is not a directory")
        else:
            res.status.reasons.append(f"Could not read calculation in {calc_dir}")

    return res


def read(calc_dir: Union[str, pl.Path]) -> Result:
    """Master function for reading data from calculations. It reads general information as well as engine-specific information.

    Args:
        calc_dir: path pointing to the working directory for the desired calculation

    Returns:
        dictionary containing information about the calculation
    """
    calc_dir = str(calc_dir) if isinstance(calc_dir, pl.Path) else calc_dir

    ret = Result()
    ret.update(get_info(calc_dir))
    if ret.engine == "adf":
        try:
            ret.adf = adf.get_calc_settings(ret)
        except:  # noqa
            ret.adf = None

        try:
            ret.properties = adf.get_properties(ret)
        except:  # noqa
            ret.properties = None

        try:
            ret.level = adf.get_level_of_theory(ret)
        except:  # noqa
            ret.level = None

    elif ret.engine == "dftb":
        ret.dftb = dftb.get_calc_settings(ret)
        ret.properties = dftb.get_properties(ret)
    elif ret.engine == "xtb":
        # ret.xtb = xtb.get_calc_settings(ret)
        ret.properties = xtb.get_properties(ret)

    elif ret.engine == "orca":
        try:
            ret.orca = orca.get_calc_settings(ret)
        except:  # noqa
            ret.orca = None

        try:
            ret.properties = orca.get_properties(ret)
        except:  # noqa
            ret.properties = None

    # unload cached KFReaders associated with this calc_dir
    to_delete = [key for key in cache._cache if key.startswith(os.path.abspath(calc_dir))]
    [cache.unload(key) for key in to_delete]
    return ret


def quick_status(calc_dir: Union[str, pl.Path]) -> Result:
    """
    Quickly check the status of a calculation.

    Args:
        calc_dir: the directory of the calculation to check.
    
    Returns:
        :Dictionary containing information about the calculation status:

            - **fatal (bool)** – `True` if calculation cannot be read correctly, `False` otherwise
            - **reasons (list[str])** – list of reasons to explain the status, they can be errors, warnings, etc.
            - **name (str)** – calculation status written as a string, one of ("SUCCESS", "RUNNING", "UNKNOWN", "SUCCESS(W)", "FAILED").
                If the job is being managed by slurm it can also take values of ("COMPLETING", "CONFIGURING", "PENDING").
            - **code (str)** – calculation status written as one or two characters, one of ("S", "R", "U", "W" "F")
                If the job is being managed by slurm it can also take values of ("CG", "CF", "PD").
    """
    for engine in [ams, orca, crest, xtb]:
        status = engine.get_calculation_status(calc_dir)
        if status != 'UNKNOWN':
            return status

    # otherwise we check if the job is being managed by slurm
    if not slurm.workdir_info(calc_dir):
        return ret

    # get the statuscode from the workdir
    state = slurm.workdir_info(calc_dir).statuscode
    state_name = {
        'CG': 'COMPLETING',
        'CF': 'CONFIGURING',
        'PD': 'PENDING',
        'R': 'RUNNING'
    }.get(state, 'UNKNOWN')

    ret.fatal = False
    ret.name = state_name
    ret.code = state
    ret.reasons = []
