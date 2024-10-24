from tcutility.job import ADFJob
from tcutility.data import functionals
from tcutility import results, log, pathfunc

# run the calculations:
available_functionals = functionals.get_available_functionals()
for functional_name, functional_info in available_functionals.items():
    with ADFJob(test_mode=True) as job:
        # load your ams version
        job.add_preamble('module load ams/2023.101')
        # load your molecule
        job.molecule('molecule.xyz')

        # sort calculation by their category
        job.rundir = f'DFT_screening/{functional_info.category}'
        job.name = functional_info.path_safe_name

        # slurm settings
        job.sbatch(p='tc', ntasks_per_node=32)

        # ADF settings
        job.functional(functional_name)
        job.basis_set('TZ2P')

# analyse the results
rows = []
for rundir, path_data in pathfunc.match('DFT_screening', '{category}/{functional_name}').items():
    res = results.read(rundir)
    rows.append(res.status.code)
log.table(rows, ['Status'])
