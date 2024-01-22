from tcutility.job import ADFJob
from tcutility.data import functionals

for func_name, func_data in functionals.get_available_functionals().items():
    with ADFJob(test_mode=True) as job:
        job.add_preamble('module load ams/2023.101')
        job.molecule('molecule.xyz')
        job.rundir = f'DFT_screening/{func_data.category}'
        job.name = func_data.path_safe_name
        job.sbatch(p='tc', ntasks_per_node=32)
        job.functional(func_name)
        job.basis_set('TZ2P')



from tcutility import results, log
from yutility import pathfunc


rows = []
for rundir, path_data in pathfunc.match('DFT_screening', '{category}/{functional_name}').items():
    res = results.read(rundir)
    rows.append(res.status.code)
log.table(rows, ['Status'])