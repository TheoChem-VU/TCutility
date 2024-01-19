from tcutility.job import DFTBJob, CRESTJob
from scm import plams
import os

j = os.path.join

mol_name = 'Butane'
nconformers = 3
input_xyz = '''C      -1.48876411      -0.32487538       0.28696349
C      -0.11771486       0.30395569      -0.02351266
C       1.24116705      -0.41059891      -0.14372778
C       2.50584571       0.40788204      -0.46353526
H      -1.40769822      -1.40121453       0.25059944
H      -2.21084004       0.00667833      -0.44452710
H      -1.80926913      -0.02108835       1.27255467
H       0.02770267       1.04215784       0.75128495
H      -0.25194941       0.80045831      -0.97317904
H       1.13926570      -1.14862383      -0.92560715
H       1.41891779      -0.90692430       0.79885684
H       3.30465969       0.10999788       0.19945889
H       2.29831005       1.45900634      -0.32764317
H       2.80148487       0.22864153      -1.48670207
'''
input_mol = plams.Molecule()
for line in input_xyz.splitlines():
	sym, *coords = line.split()
	input_mol.add_atom(plams.Atom(symbol=sym, coords=coords))


with CRESTJob() as crest_job:
	crest_job.molecule(input_mol)
	crest_job.md_length(1)
	crest_job.md_temperature(1000)
	crest_job.sbatch(p='tc', n=32)
	crest_job.rundir = f'calculations/{mol_name}'
	crest_job.name = 'CREST'

for i in range(nconformers):
	with DFTBJob() as dftb_job:
		dftb_job.molecule(j(crest_job.conformer_directory, f'{str(i).zfill(5)}.xyz'))
		dftb_job.sbatch(p='tc', n=32)
		dftb_job.optimization()
		dftb_job.rundir = f'calculations/DFTB/{mol_name}'
		dftb_job.name = f'conformer_{i}'
		dftb_job.dependency(crest_job)

	with ADFJob() as adf_job:
		adf_job.molecule(dftb_job.output_mol_path)
		adf_job.sbatch(p='tc', n=32)
		adf_job.optimization()
		adf_job.functional('BLYP-D3(BJ)')
		adf_job.basis_set('TZ2P')
		adf_job.rundir = f'calculations/ADF/{mol_name}'
		adf_job.name = f'conformer_{i}'
		adf_job.dependency(dftb_job)
