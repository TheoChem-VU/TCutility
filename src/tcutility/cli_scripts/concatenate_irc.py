import argparse
import pathlib as pl

from tcutility.analysis.task_specific.irc import concatenate_irc_trajectories, create_result_objects
from tcutility.log import log
from tcutility.molecule import write_mol_to_amv_file, write_mol_to_xyz_file


def create_subparser(parent_parser: argparse.ArgumentParser):
    subparser = parent_parser.add_parser(  # type: ignore # add_parser is a valid method
        "concat-irc",
        help="Combine separated IRC paths.",
        description="""
        Scripts that takes in two or more directories containing an IRC file ("ams.rkf") and concatenates them through the RMSD values. Produces a .xyz and .amv file in the specified output directory.
        The output directory is specified with the -o flag. If not specified, the output will be written to the current working directory.
        In addition, the -r flag can be used to reverse the trajectory.

        Note: ALWAYS visualize the .amv file in AMSView to verify the trajectory.
    """,
    )

    # Add the arguments
    subparser.add_argument("jobs", nargs="*", type=str, help="Job directories containing the ams.rkf of the irc calculation(s)")
    subparser.add_argument("-r", "--reverse", action="store_true", help="Reverses the trajectory")
    subparser.add_argument("-o", "--output", type=str, default="./", help="Directory in which the outputfile will be saved")
    subparser.add_argument("-l", "--log_level", type=int, default=20, help="Set the log level. The lower the value, the more is printed. Default is 20 (info).")


def main(args):
    outputdir = pl.Path(args.output).resolve()
    job_dirs = [pl.Path(directory).resolve() for directory in args.jobs]

    if len(job_dirs) > 2:
        raise ValueError("Only two IRC paths can be concatenated at a time as is currently implemented.")

    log(f"Concatenating trajectories... with reverse = {args.reverse}", args.log_level)
    res_objects = create_result_objects(job_dirs)
    molecules, energies = concatenate_irc_trajectories(res_objects, args.reverse)
    log(f"Trajectories concatenated successfully (total length = {len(molecules)}) .", args.log_level)

    outputdir.mkdir(parents=True, exist_ok=True)
    write_mol_to_amv_file(molecules, energies, outputdir / "read_concatenated_mols")
    write_mol_to_xyz_file(molecules, outputdir / "read_concatenated_mols")

    log(f"Output written to {outputdir / 'concatenated_mols'}")
