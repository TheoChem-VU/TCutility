from tcutility.job import ORCAJob

with ORCAJob() as job:
    job.molecule('water.xyz')
    job.sbatch(p='tc', n=32, mem=20000)
    job.name = 'ORCA_opt'
    job.rundir = 'calculations/water'
    job.add_preamble('export ORCA_FP=“/scistor/tc/dra480/bin/orca500/orca”')
    job.add_preamble('export PATH=“/scistor/tc/dra480/bin/ompi411/bin:$PATH”')
    job.add_preamble('export LD_LIBRARY_PATH=“/scistor/tc/dra480/bin/ompi411/lib/:$LD_LIBRARY_PATH”')
    job.optimization()
