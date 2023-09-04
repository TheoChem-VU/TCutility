"""
This module provides basic and general information about calculations done using AMS given a calculation directory.
This includes information about the engine used (ADF, DFTB, BAND, ...), general information such as timings, files, status of the calculation, etc.
This information is used in further analysis programs.

Typical usage example:

.. literalinclude:: ../docs/shared/usage_results.rst
"""

from . import result
Result = result.Result

from . import adf, dftb, ams, cache  # noqa: E402
import os  # noqa: E402


def read(calc_dir: str) -> Result:
    '''Master function for reading data from calculations. It reads general information as well as engine-specific information.

    Args:
        calc_dir: path pointing to the working directory for the desired calculation

    Returns:
        dictionary containing information about the calculation
    '''
    ret = Result()
    ret.update(ams.get_ams_info(calc_dir))
    if ret.engine == 'adf':
        ret.adf = adf.get_calc_settings(ret)
        ret.properties = adf.get_properties(ret)
    elif ret.engine == 'dftb':
        ret.dftb = dftb.get_calc_settings(ret)
        ret.properties = dftb.get_properties(ret)

    # unload cached KFReaders associated with this calc_dir
    to_delete = [key for key in cache._cache if key.startswith(os.path.abspath(calc_dir))]
    [cache.unload(key) for key in to_delete]
    return ret
