import TCutility.results
from pprint import pprint

calc_dir = '../test/fixtures/ethanol'
info = TCutility.results.read(calc_dir)
pprint(info.adf.symmetry)
pprint(info.properties.vibrations.number_of_imag_modes)
