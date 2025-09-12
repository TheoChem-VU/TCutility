from tcutility.results2 import result, adf_rkf, adf_out


def read_adfrkf(path: str, ret: result.NestedDict = None):
    if ret is None:
        ret = result.NestedDict()

    ret.set('engine', 'adf')
    ret.set('status', adf_rkf._read_status(path))
    ret.set('job_id', adf_rkf._read_jobid(path))
    ret.set('input', 'adf', adf_rkf._read_adf_input(path))
    ret.set('level', adf_rkf._read_level_of_theory(path))
    ret.set('adf', adf_rkf._read_settings(path))
    ret.set('properties', 'excitations', adf_rkf._read_excitations(path))
    ret.set('properties', 'vibrations', adf_rkf._read_vibrations(path))

    return ret


def read_adfout(path: str, ret: result.NestedDict = None):
    if ret is None:
        ret = result.NestedDict()

    ret.set('engine', 'adf')
    ret.set('job_id', adf_out._read_jobid(path))
    # ret.set('adf', adf_out._read_settings(path))
    ret.set('input', adf_out._read_input(path))
    ret.set('properties', adf_out._read_properties(path))
    return ret


if __name__ == '__main__':
    # from pprint import pprint
    # from tcutility import results
    from time import perf_counter

    # start = perf_counter()
    # ret = read_adfrkf('/Users/yumanhordijk/PhD/Programs/TheoCheM/TCutility/examples/job/uvvis/restricted/adf.rkf')
    # print(perf_counter() - start)

    start = perf_counter()
    ret = read_adfout('/Users/yumanhordijk/PhD/Programs/TheoCheM/TCutility/examples/job/uvvis/restricted/restricted.out')
    print(perf_counter() - start)

    # start = perf_counter()
    # ref_ret = results.read('/Users/yumanhordijk/PhD/Programs/TheoCheM/TCutility/examples/job/uvvis/restricted')
    # print(perf_counter() - start)

    # start = perf_counter()
    # ref_ret = results.quick_status('/Users/yumanhordijk/PhD/Programs/TheoCheM/TCutility/examples/job/uvvis/restricted')
    # print(perf_counter() - start)





    from time import perf_counter
    start = perf_counter()
    import rust_outp
    rust_outp.read_adf_output('/Users/yumanhordijk/PhD/Programs/TheoCheM/TCutility/examples/job/uvvis/restricted/restricted.out')
    print(perf_counter() - start)
