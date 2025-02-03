from tcutility.job import ADFJob, ADFFragmentJob


# uv/vis calculations can be run on singlepoint jobs
with ADFJob() as job:
	job.rundir = 'uvvis'
	job.name = 'restricted'
	job.molecule('NH3BH3.xyz')
	job.excitations()

# and also fragment jobs
# in this case the SFOs are simply built up of the fragment densities
with ADFFragmentJob() as job:
	job.rundir = 'uvvis'
	job.name = 'fragment'
	job.molecule('NH3BH3.xyz')
	job.excitations()


with ADFJob() as job:
	job.rundir = 'uvvis'
	job.name = 'unrestricted'
	job.molecule('NH3BH3.xyz')
	job.excitations()
	job.unrestricted(True)


