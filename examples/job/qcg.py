from tcutility.job import QCGJob

with QCGJob() as job:
    job.molecule('asc.xyz')
    job.solvent('dmso.xyz')
    job.rundir = 'calculations/ASC'
    job.name = 'QCG'
    job.md_length(5)
    job.md_temperature(1000)
    job.crest_path = 'crest'
    job.sbatch(p='tc', n=32)
    job.ensemble_mode('MTD')
