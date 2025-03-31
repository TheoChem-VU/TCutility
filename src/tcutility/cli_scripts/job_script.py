"""Module containing functions for quickly submitting geometry optimization jobs via the command line"""

import os

import click
import tcutility
from tcutility import job as tcjob


@click.command()
@click.option(
    "-l",
    "--level",
    type=str,
    help='Set the level of theory for the optimization. For example, "GFN1-xTB" or "BLYP-D3(BJ)/TZ2P" Can be set in the xyz-file with the \'level_of_theory\' flag.',
    default=None,
)
@click.option("-c", "--charge", type=int, help="The charge of the system. Can be set in the xyz-file with the 'charge' flag.", default=None)
@click.option("-s", "--spinpol", type=int, help="The spin-polarization of the system. Can be set in the xyz-file with the 'spinpol' flag.", default=None)
@click.option("-o", "--output", type=str, help=r"The file to write the optimized result to. By default will be written to '{xyzfile}_optimized.xyz'.", default=None)
@click.option("-k", "--keep", is_flag=True, help="Whether to keep the calculation directory after finishing the calculation.")
@click.argument("xyzfile", type=str)
def optimize_geometry(level: str, charge: int, spinpol: int, output: str, keep: bool, xyzfile: str) -> None:
    """Set up and run a geometry optimization on a given structure."""
    # set a default output
    if output is None:
        output = xyzfile.removesuffix(".xyz") + "_optimized.xyz"

    mol = tcutility.molecule.load(xyzfile)

    # get the correct job class object and set the level-of-theory
    level = level or mol.flags.level_of_theory or "GFN1-xTB"  # type: ignore # mol flags can be any
    if level.lower() == "gfn1-xtb":
        job = tcjob.DFTBJob(delete_on_finish=not keep)  # by default DFTBJob uses GFN1-xTB
    else:
        # if we are not using GFN1-xTB we will use ADF
        parts = level.split("/")
        job = tcjob.ADFJob(delete_on_finish=not keep)
        job.functional(parts[0])
        if len(parts) > 1:
            job.basis_set(parts[1])

    job.molecule(mol)
    job.optimization()
    job.charge(charge or mol.flags.charge or 0)  # type: ignore # mol flags can be any
    if isinstance(job, tcjob.ADFJob):
        job.spin_polarization(spinpol or mol.flags.spinpol or 0)  # type: ignore # mol flags can be any

    job.rundir = os.path.split(xyzfile)[0]
    job.name = f".tmp.{os.getpid()}"

    # copy the optimized mol to the output file
    job.add_postamble(f"cp {job.output_mol_path} {output}")

    job.run()
