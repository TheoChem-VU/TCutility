>>> import TCutility.results
>>> calc_dir = '../test/fixtures/ethanol'
>>> info = TCutility.results.read(calc_dir)
>>> info.engine
adf
>>> info.ams_version.full
2022.103 r104886 (2022-06-17)
>>> info.adf.symmetry
{'group': 'C(S)', 'labels': ['AA', 'AAA']}
>>> info.properties.energy.orbint
{'AA': -2738.644830445246,
 'AAA': -1056.9706925183411,
 'total': -3795.615522963587}
>>> info.properties.vibrations.number_of_imag_modes
0