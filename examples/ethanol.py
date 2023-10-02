'''
This script demonstrates how to get properties from a finished calculation. In this case, we optimized ethanol using ADF. Using the read function, we can extract information such as the symmetry and vibrations.
'''

import TCutility.results
from pprint import pprint

calc_dir = '../test/fixtures/ethanol'
info = TCutility.results.read(calc_dir)
pprint(info.adf.symmetry)
pprint(info.properties.vibrations.number_of_imag_modes)
pprint(info.level)