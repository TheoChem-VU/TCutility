import pathlib as pl

from tcutility import formula
from tcutility.analysis.report import report

pwd = pl.Path(__file__).parent
with report.SI("test.docx") as si:
    si.add_heading("Test molecules:")
    si.add_xyz(str(object=pwd.parent / "test" / "fixtures" / "level_of_theory" / "M06_2X"), title="Cyclo-octatriene")
    si.add_xyz(str(object=pwd.parent / "test" / "fixtures" / "ethanol"), title=formula.molecule("C2H5OH"))
