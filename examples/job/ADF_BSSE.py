from tcutility.job.adf import ADFFragmentJob


with ADFFragmentJob(counter_poise=True) as job:
    job.sbatch(p='tc', n=32)
    job.functional('BLYP-D3(BJ)')
    job.basis_set('DZ')
    job.molecule('HF_dimer.xyz')
    job.rundir = 'calculations'
    job.name = 'HF_dimer_CPC'
