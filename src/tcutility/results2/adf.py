from tcutility.results2 import result, adf_rkf


def read_adfrkf(path: str, ret: result.NestedDict = None):
    if ret is None:
        ret = result.NestedDict()

    ret.set('adf', adf_rkf._read_settings(path))
    ret.set('properties', 'excitations', adf_rkf._read_excitations(path))
    ret.set('properties', 'vibrations', adf_rkf._read_vibrations(path))

    return ret


# if __name__ == '__main__':
#     def equal_dicts(d1: dict, d2: dict) -> bool:
#         '''
#         Test if two dictionaries are the same
#         '''
#         import dictfunc
#         for row1, row2 in zip(dictfunc.dict_to_list(d1), dictfunc.dict_to_list(d2)):
#             for x, y in zip(row1, row2):
#                 if isinstance(x, np.ndarray):
#                     if (x != y).any():
#                         return False
#                 else:
#                     if x != y:
#                         return False
#         return True

#     ref_res = results.read('/Users/yumanhordijk/PhD/Projects/Students/felix_research/test/Excitations_Approx/M06-2X_range/exc.results')
#     test_res = read_adfrkf('/Users/yumanhordijk/PhD/Projects/Students/felix_research/test/Excitations_Approx/M06-2X_range/exc.results/adf.rkf')

#     # print(equal_dicts(ref_res.adf, test_res.adf))
#     # print(equal_dicts(ref_res.properties.excitations, test_res.get('properties', 'excitations')))

#     import pprint

#     # pprint.pprint(ref_res.adf)
#     pprint.pprint(test_res['properties']['excitations'])


#     ref_res = results.read('/Users/yumanhordijk/PhD/Programs/TheoCheM/TCutility/test/fixtures/ethanol/geometry_optimization.results')
#     test_res = read_adfrkf('/Users/yumanhordijk/PhD/Programs/TheoCheM/TCutility/test/fixtures/ethanol/geometry_optimization.results/adf.rkf')
#     # print(test_res)

#     # print(equal_dicts(ref_res.adf, test_res.get('adf')))

#     import pprint

#     # pprint.pprint(ref_res.adf)
#     pprint.pprint(test_res['properties']['vibrations'])

#     # print(equal_dicts(ref_res.properties.vibrations, test_res.get('properties', 'vibrations')))

