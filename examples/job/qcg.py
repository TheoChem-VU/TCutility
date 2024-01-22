from tcutility.job import QCGJob

with QCGJob() as job:
	job.molecule('pentane.xyz')
	job.solvent('water')
	job.rundir = 'calculations/pentane'
	job.name = 'QCG'
	job.crest_path = 'crest'
