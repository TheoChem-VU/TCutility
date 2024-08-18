import pathlib as pl

from tcutility.job import ADFJob

current_file_path = pl.Path(__file__).parent
mol_path = current_file_path / "water_dimer.xyz"

# define a new job using the Job context-manager
with ADFJob(use_slurm=False) as job:
    # add the molecule
    job.molecule(str(mol_path))

    # set the rundir and name of the job, they will
    # determine where the job will run
    job.rundir = str(current_file_path / "calculations")
    job.name = "GO_water_dimer"

    # set the ADF settings
    job.functional("BP86-D3(BJ)")
    job.basis_set("TZ2P")
    job.quality("Good")

    # set the job task
    job.optimization()
