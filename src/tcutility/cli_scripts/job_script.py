""" Module containing functions for quickly submitting geometry optimization jobs via the command line """
import argparse
from tcutility import job as tcjob
import tcutility
import os


def create_subparser(parent_parser: argparse.ArgumentParser):
    desc = "Set up and run a geometry optimization on a given structure."
    subparser = parent_parser.add_parser('optimize', help=desc, description=desc)
    subparser.add_argument("-l", "--level", 
                           type=str, 
                           help="Set the level of theory for the optimization. For example, \"GFN1-xTB\" or \"BLYP-D3(BJ)/TZ2P\" Can be set in the xyz-file with the 'level_of_theory' flag.", 
                           default=None)
    subparser.add_argument("-c", "--charge",
                           type=int,
                           help="The charge of the system. Can be set in the xyz-file with the 'charge' flag.",
                           default=None)
    subparser.add_argument("-s", "--spinpol",
                           type=int,
                           help="The spin-polarization of the system. Can be set in the xyz-file with the 'spinpol' flag.",
                           default=None)
    subparser.add_argument("-o", "--output",
                           type=str,
                           help="The file to write the optimized result to. By default will be written to '{xyzfile}_optimized.xyz'.",
                           default=None)
    subparser.add_argument("-k", "--keep",
                           help="Keep the calculation directory after finishing the calculation.",
                           default=False,
                           action="store_true")
    subparser.add_argument("xyzfile",
                           type=str,
                           help="The molecule to optimize, in extended xyz-format. See https://theochem-vu.github.io/TCutility/api/tcutility.html#module-tcutility.molecule for more information.")


def main(args: argparse.Namespace):
    # set a default output
    if args.output is None:
        args.output = args.xyzfile.removesuffix('.xyz') + '_optimized.xyz'

    mol = tcutility.molecule.load(args.xyzfile)

    # get the correct job class object and set the level-of-theory
    level = args.level or mol.flags.level_of_theory or 'GFN1-xTB'
    if level.lower() == 'gfn1-xtb':
        job = tcjob.DFTBJob(delete_on_finish=not args.keep)  # by default DFTBJob uses GFN1-xTB
    else:
        # if we are not using GFN1-xTB we will use ADF
        parts = level.split('/')
        job = tcjob.ADFJob(delete_on_finish=not args.keep)
        job.functional(parts[0])
        if len(parts) > 1:
            job.basis_set(parts[1])

    job.molecule(mol)
    job.optimization()
    job.charge(args.charge or mol.flags.charge or 0)
    if isinstance(job, tcjob.ADFJob):
        job.spin_polarization(args.spinpol or mol.flags.spinpol or 0)

    job.rundir = os.path.split(args.xyzfile)[0]
    job.name = f'.tmp.{os.getpid()}'

    # copy the optimized mol to the output file
    job.add_postamble(f'cp {job.output_mol_path} {args.output}')

    job.run()
