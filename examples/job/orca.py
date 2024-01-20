from tcutility.job import ORCAJob

with ORCAJob() as job:
    job.molecule('water.xyz')
    job.sbatch(p='tc', n=32, mem=20000)
    job.name = 'ORCA_opt'
    job.rundir = 'calculations/water'
    job.optimization()
