from tcutility.job import ORCAJob

with ORCAJob() as job:
    job.molecule('water.xyz')
