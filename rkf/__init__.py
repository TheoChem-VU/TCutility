from yutility import dictfunc
from . import adf, dftb, info


def read(calc_dir: str) -> dictfunc.DotDict:
    ret = dictfunc.DotDict()
    ret.update(info.get_calc_info(calc_dir))
    if ret.engine == 'adf':
        ret.adf = adf.get_calc_settings(ret)
    elif ret.engine == 'dftb':
        ret.dftb = dftb.get_calc_settings(ret)
    return ret
