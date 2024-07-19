#!/usr/bin/env python3

from tcutility.job import ADFJob, DFTBJob, CRESTJob
import os
import sys

j = os.path.join

mol_file = sys.argv[1]
mol_name = mol_file.removesuffix('.xyz')

with CRESTJob(wait_for_finish=True) as crest_job:
    crest_job.molecule(mol_file)
    crest_job.md_length(3)
    crest_job.md_temperature(1000)
    crest_job.sbatch(p='tc', n=64)
    crest_job.rundir = f'calculations/{mol_name}'
    crest_job.name = 'CREST'

for i, xyzfile in enumerate(crest_job.get_conformer_xyz()):
    with DFTBJob() as dftb_job:
        dftb_job.molecule(xyzfile)
        dftb_job.sbatch(p='tc', n=8)
        dftb_job.optimization()
        dftb_job.rundir = f'calculations/{mol_name}/DFTB'
        dftb_job.name = f'conformer_{i}'
        dftb_job.dependency(crest_job)

    with ADFJob() as adf_job:
        adf_job.molecule(dftb_job.output_mol_path)
        adf_job.sbatch(p='tc', n=32)
        adf_job.optimization()
        adf_job.functional('BLYP-D3(BJ)')
        adf_job.basis_set('TZ2P')
        adf_job.rundir = f'calculations/{mol_name}/ADF'
        adf_job.name = f'conformer_{i}'
        adf_job.dependency(dftb_job)
