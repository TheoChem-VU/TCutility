from tcutility import WorkFlow
import os
from tcutility.results.read import quick_status

# to create a WorkFlow we simply decorate a function with a WorkFlow object
@WorkFlow(delete_files=True)
def find_global_minimum(molecule: str):
    # any imports that are needed in the workflow
    # need to be imported within the function
    from tcutility import CRESTJob, ADFJob, read
    from tcutility import workflow_status

    workflow_status.stage('Performing CREST calculation')
    # we first perform a CRESTJob calculation to
    # obtain the conformers of the molecule of interest
    with CRESTJob(use_slurm=False) as crest_job:
        crest_job.molecule(molecule)
        crest_job.name = 'crest'
        crest_job.md_temperature(500)
        crest_job.md_length('2x')
        crest_job.do_crossing(False)

    new_molecules = []
    new_energies = []
    conformers = crest_job.get_conformer_xyz(5)
    for i, xyz in enumerate(conformers):
        workflow_status.stage(f'Performing conformer optimization {i+1}/{len(conformers)}')
        # and reoptimize them using ADF
        with ADFJob(use_slurm=False) as adf_job:
            adf_job.molecule(xyz)
            adf_job.functional('OLYP')
            adf_job.basis_set('DZP')
            adf_job.name = f'optimization_{i+1}'

        # load the results
        results = read(adf_job.workdir)
        # and store the energies and molecules
        new_molecules.append(results.molecule.output)
        new_energies.append(results.properties.energy.bond)

    lowest_energy_molecule = min(new_molecules, key=lambda mol: new_energies[new_molecules.index(mol)])
    return lowest_energy_molecule


mol = find_global_minimum(os.path.abspath('water_dimer.xyz'))
print(mol)
mol = find_global_minimum(os.path.abspath('butane.xyz'))
print(mol)
