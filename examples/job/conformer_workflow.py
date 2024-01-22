from tcutility.job import ADFJob, DFTBJob, CRESTJob
import os

j = os.path.join

mol_name = 'Pentane'

with CRESTJob() as crest_job:
	crest_job.molecule('pentane.xyz')
	crest_job.md_length(0.2)
	crest_job.md_temperature(1000)
	crest_job.sbatch(p='tc', n=64)
	crest_job.rundir = f'calculations/{mol_name}'
	crest_job.name = 'CREST'

for i, xyzfile in enumerate(crest_job.get_conformer_xyz(number=10)):
	with DFTBJob() as dftb_job:
		dftb_job.molecule(xyzfile)
		dftb_job.sbatch(p='tc', n=8)
		dftb_job.optimization()
		dftb_job.rundir = f'calculations/{mol_name}/DFTB'
		dftb_job.name = f'conformer_{i}'
		dftb_job.dependency(crest_job)
		dftb_job.delete_on_failure = True

	# with ADFJob() as adf_job:
	# 	adf_job.molecule(dftb_job.output_mol_path)
	# 	adf_job.sbatch(p='tc', n=32)
	# 	adf_job.optimization()
	# 	adf_job.functional('BLYP-D3(BJ)')
	# 	adf_job.basis_set('TZ2P')
	# 	adf_job.rundir = f'calculations/{mol_name}/ADF'
	# 	adf_job.name = f'conformer_{i}'
	# 	adf_job.dependency(dftb_job)
