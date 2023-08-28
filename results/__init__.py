from TCutility import result
Result = result.Result

from TCutility import adf, dftb, ams  # noqa: E402


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
