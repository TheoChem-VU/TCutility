import pathlib as pl

from scm.plams import AMSJob, Molecule, Settings, config, finish, init
from tcutility.job import ADFJob

current_file_path = pl.Path(__file__).parent
mol_path = current_file_path / "water_dimer.xyz"


def try_plams_job(mol: Molecule) -> None:
    # Test case with plams for checking if plams works solely on Windows
    run_set = Settings()
    run_set.input.ams.Task = "GeometryOptimization"
    run_set.input.adf.Basis.Type = "DZP"
    run_set.input.adf.XC.GGA = "BP86"

    config.log.file = 7
    config.log.stdout = 7

    init(path=str(current_file_path), folder="GO_water_dimer", config_settings=config)
    AMSJob(molecule=mol, name="water_dimer", settings=run_set).run()
    finish()


def try_tcutility_job(mol: Molecule) -> None:
    # Test case with tcutility for checking if tcutility works solely on Windows
    with ADFJob(use_slurm=False) as job:
        job.molecule(mol)
        job.rundir = str(current_file_path / "calculations")
        job.name = "GO_water_dimer"
        job.functional("BP86-D3(BJ)")
        job.basis_set("TZ2P")
        job.quality("Good")
        job.optimization()


def main():
    current_file_path = pl.Path(__file__).parent
    mol_path = current_file_path / "water_dimer.xyz"

    mol = Molecule(str(mol_path))

    # Use these functions to test if a plams and tcutility job can be run on Windows, Mac, and Linux. Both do not use slurm.
    try_plams_job(mol)
    try_tcutility_job(mol)


if __name__ == "__main__":
    main()
