from tcutility.job import ADFJob

# define a new job using the Job context-manager
with ADFJob() as job:
	# add the molecule
	job.molecule('water_dimer.xyz')

	# set the rundir and name of the job, they will 
	# determine where the job will run
	job.rundir = 'calculations'
	job.name = 'GO_water_dimer'
	
	# set the ADF settings
	job.functional('BP86-D3(BJ)')
	job.basis_set('TZ2P')
	job.quality('Good')

	# set the job task
	job.optimization()
