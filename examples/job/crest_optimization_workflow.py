from tcutility import WorkFlow
import os

# to create a WorkFlow we simply decorate a function
# with a WorkFlow object
@WorkFlow()
def find_global_minimum(molecule: str):
    # any imports that are needed in the workflow
    # need to be imported within the function
    from tcutility import CRESTJob, ADFJob, read

    # we first perform a CRESTJob calculation to
    # obtain the conformers of the molecule of interest
    with CRESTJob() as crest_job:
        crest_job.molecule(molecule)
        crest_job.name = 'crest'

    new_molecules = []
    new_energies = []
    # we now go through the 5 lowest-energy conformers
    for i, xyz in enumerate(crest_job.get_conformer_xyz(5)):
        # and reoptimize them using ADF
        with ADFJob() as adf_job:
            adf_job.molecule(xyz)
            adf_job.functional('OLYP')
            adf_job.basis_set('DZP')
            adf_job.name = f'optimization_{i+1}'

        results = read(adf_job.calc_dir)


find_global_minimum(os.path.abspath('butane.xyz'))




