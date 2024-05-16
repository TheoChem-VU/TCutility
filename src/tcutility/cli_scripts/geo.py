""" Module containing functions for calculating geometrical parameters for molecules """
import argparse
from tcutility import geometry, molecule


def create_subparser(parent_parser: argparse.ArgumentParser):
    desc = """Calculate geometrical parameters for atoms at the provided indices.

For 1 index this program returns the cartesian coordinate for this atom. 
For 2 indices return bond length between atoms. 
For 3 indices return bond angle, with the second index being the central atom. 
For 4 indices return dihedral angle by calculating the angle between normal vectors described by atoms at indices 1-2-3 and indices 2-3-4. 
If the -p/--pyramidal flag is turned on it calculates 360° - ang1 - ang2 - ang3, where ang1, ang2 and ang3 are the angles described by indices 2-1-3, 3-1-4 and 4-1-2 respectively.
"""
    subparser = parent_parser.add_parser('geo', help=desc, description=desc)
    subparser.add_argument("xyzfile",
                           type=str,
                           nargs=1,
                           help="The molecule to calculate the parameter for.")
    subparser.add_argument("atom_indices",
                           type=str,
                           nargs='+',
                           help="The indices of the atoms to calculate the parameters for.")
    subparser.add_argument("-p", "--pyramidal",
                           help="Instead of calculating dihedral angles, calculate pyramidalisation angle.",
                           default=False,
                           action="store_true")


def main(args: argparse.Namespace):
    mol = molecule.load(args.xyzfile[0])
    indices = [int(i) - 1 for i in args.atom_indices]

    assert 1 <= len(indices) <= 4, f"Number of indices must be 1, 2, 3 or 4, not {len(indices)}"

    atoms = "-".join([f'{mol[i+1].symbol}{i+1}' for i in indices])

    param = geometry.parameter(mol, *indices, pyramidal=args.pyramidal)

    if len(indices) == 1:
        param = "  ".join([f"{x: .6f}" for x in mol[indices[0] + 1].coords])
        print(f'Coordinate({atoms}) = {param} Å')
        return


    if len(indices) == 2:
        param_type = 'Distance'
        unit = ' Å'
        precision = 3

    if len(indices) == 3:
        param_type = 'Angle'
        unit = '°'
        precision = 2

    if len(indices) == 4 and not args.pyramidal:
        param_type = 'Dihedral'
        unit = '°'
        precision = 2

    if len(indices) == 4 and args.pyramidal:
        param_type = 'Pyramid'
        unit = '°'
        precision = 2

    print(f'{param_type}({atoms}) = {param: .{precision}f}{unit}')