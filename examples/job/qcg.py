from tcutility.job import QCGJob

with QCGJob(test_mode=True) as job:
    job.molecule("asc.xyz")
    job.solvent("acetone", 5)
    job.rundir = "calculations/ASC"
    job.name = "QCG"
    job.md_length(5)
    job.md_temperature(1000)
    job.sbatch(p="tc", n=32)
    job.ensemble_mode("MTD")
