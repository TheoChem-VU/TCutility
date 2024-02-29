"""
This script demonstrates how to get properties from a finished calculation. In this case, we optimized ethanol using ADF.
Using the read function, we can extract information such as the symmetry and vibrations.
"""

import pathlib as pl
from pprint import pprint

import tcutility.results as results

calc_dir = pl.Path(__file__).parent.parent / "test" / "fixtures" / "ethanol"
info = results.read(calc_dir)
pprint(info.multi_keys())
pprint(info.adf.symmetry)
pprint(info.properties.vibrations.number_of_imag_modes)
pprint(info.properties.vibrations.vdd)
pprint(info.level)
