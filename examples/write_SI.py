from tcutility import report, formula

import pathlib as pl

pwd = pl.Path(__file__).parent
with report.SI("test.docx") as si:
    si.add_heading("Test molecules:")
    si.add_xyz(str(pwd.parent / "test" / "fixtures" / "level_of_theory" / "M06_2X"), "Cyclo-octatriene")
    si.add_xyz(str(pwd.parent / "test" / "fixtures" / "ethanol"), formula.molecule("C2H5OH"))
