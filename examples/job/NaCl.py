from tcutility.job import ADFFragmentJob

with ADFFragmentJob() as job:
    job.molecule("NaCl.xyz")
