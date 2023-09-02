"""
This module provides basic and general information about calculations done using AMS given a calculation directory.
This includes information about the engine used (ADF, DFTB, BAND, ...), general information such as timings, files, status of the calculation, etc.
This information is used in further analysis programs.

Typical usage example:
    
    >>> import TCutility.results
    >>> calc_dir = '../test/fixtures/ethanol'
    >>> info = TCutility.results.read(calc_dir)
    >>> print(info.engine)
    >>> print(info.properties.energy.bond)
"""

from . import result
Result = result.Result

from . import adf, dftb, ams  # noqa: E402


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
    elif ret.engine == 'dftb':
        ret.dftb = dftb.get_calc_settings(ret)
    return ret
