import pathlib as pl
from typing import List

import click
from tcutility.analysis.task_specific.irc import concatenate_irc_trajectories, create_result_objects
from tcutility.log import log
from tcutility.molecule import write_mol_to_amv_file, write_mol_to_xyz_file


@click.command("concat-irc")
@click.argument("jobs", nargs=-1, type=click.Path(exists=True))
@click.option("-r", "--reverse", is_flag=True, help="Reverses the trajectory")
@click.option("-o", "--output", type=click.Path(), default="./", help="Directory in which the output file will be saved")
@click.option("-l", "--log_level", type=int, default=20, help="Set the log level. The lower the value, the more is printed. Default is 20 (info).")
def concatenate_irc_paths(jobs: List[str], reverse: bool, output: str, log_level: int) -> None:
    """
    Combine separated IRC paths.

    Scripts that takes in two or more directories containing an IRC file ("ams.rkf") and concatenates them through the RMSD values. Produces a .xyz and .amv file in the specified output directory.
    The output directory is specified with the -o flag. If not specified, the output will be written to the current working directory.
    In addition, the -r flag can be used to reverse the trajectory.

    Note: ALWAYS visualize the .amv file in AMSView to verify the trajectory.
    """
    outputdir = pl.Path(output).resolve()
    job_dirs = [pl.Path(directory).resolve() for directory in jobs]

    if len(job_dirs) > 2:
        raise ValueError("Only two IRC paths can be concatenated at a time as is currently implemented.")

    log(f"Concatenating trajectories... with reverse = {reverse}", log_level)
    res_objects = create_result_objects(job_dirs)
    molecules, energies = concatenate_irc_trajectories(res_objects, reverse)
    log(f"Trajectories concatenated successfully (total length = {len(molecules)}) .", log_level)

    outputdir.mkdir(parents=True, exist_ok=True)
    write_mol_to_amv_file(out_file=outputdir / "concatenated_mols.amv", mols=molecules, energies=energies)
    write_mol_to_xyz_file(out_file=outputdir / "concatenated_mols.xyz", mols=molecules)

    log(f"Output written to {outputdir / 'concatenated_mols'}", log_level)


if __name__ == "__main__":
    concatenate_irc_paths()
