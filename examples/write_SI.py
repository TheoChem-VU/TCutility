from TCutility import report, formula
import os

j = os.path.join

pwd = os.path.split(__file__)[0]
with report.SI('test.docx') as si:
	si.add_heading('Test molecules:')
	si.add_xyz(j(pwd, '..', 'test', 'fixtures', 'level_of_theory', 'M06_2X'), 'Cyclo-octatriene')
	si.add_xyz(j(pwd, '..', 'test', 'fixtures', 'ethanol'), formula.molecule('C2H5OH'))
