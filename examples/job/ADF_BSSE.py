from tcutility.job.adf import ADFBSSEJob


with ADFBSSEJob(test_mode=True) as job:
    job.rundir = 'calculations/CrCO6'
    job.name = 'BSSE_DZ'
    job.molecule('CrCO6.xyz')
    job.basis_set('DZ')


with ADFBSSEJob(test_mode=True) as job:
    job.rundir = 'calculations/CrCO6'
    job.name = 'BSSE_TZP'
    job.molecule('CrCO6.xyz')
    job.basis_set('TZP')
