"""Module containing functions for calculating geometrical parameters for molecules"""

from typing import Dict, List, Tuple

import click
from strenum import StrEnum
from tcutility import geometry, molecule, results


class GeometricParameter(StrEnum):
    """Enum class for geometric parameters"""

    COORDINATE = "Coordinate"
    DISTANCE = "Distance"
    ANGLE = "Angle"
    DIHEDRAL = "Dihedral"
    PYRAMIDAL = "Pyramidal"
    SUMOFANGLES = 'SumOfAngles'


geometric_character_to_info_mapping: Dict[GeometricParameter, Tuple[str, str, int]] = {
    GeometricParameter.COORDINATE: ("Coordinate", "Å", 6),
    GeometricParameter.DISTANCE: ("Distance", " Å", 3),
    GeometricParameter.COORDINATE: ("Angle", "°", 2),
    GeometricParameter.DIHEDRAL: ("Dihedral", "°", 2),
    GeometricParameter.SUMOFANGLES: ("SumOfAngles", "°", 2),
}


@click.command()
@click.argument("path", type=click.Path(exists=True))
@click.argument("atom_indices", type=str, nargs=-1)
@click.option("-p", "--pyramidal", is_flag=True, default=False, help="Instead of calculating a dihedral angle, calculate pyramidalisation angle.")
@click.option("-s", "--soa", is_flag=True, default=False, help="Instead of calculating a dihedral angle, calculate sum-of-angles angle.")
def calculate_geometry_parameter(path: str, atom_indices: List[str], pyramidal: bool, soa: bool) -> None:
    """
    \b
    Calculate geometrical parameters for atoms at the provided ATOM_INDICES (NB: counting starts at 1).
    PATH should be an XYZ-file or a calculation directory.
    
    \b
    For 1 index this program returns the cartesian coordinate for this atom.
    For 2 indices return bond length between atoms.
    For 3 indices return bond angle, with the second index being the central atom.
    For 4 indices return dihedral angle by calculating the angle between normal vectors
        described by atoms at indices 1-2-3 and indices 2-3-4.
    \b
    If the -p/--pyramidal flag is turned on it calculates 360° - ang1 - ang2 - ang3, 
        where ang1, ang2 and ang3 are the angles described by indices 2-1-3, 3-1-4 
        and 4-1-2 respectively.
    If the -s/--soa flag is turned on it calculates ang1 + ang2 + ang3.
    """
    try:
        mol = molecule.load(path)
    except IsADirectoryError:
        mol = results.read(path).molecule.output
    indices = [int(i) - 1 for i in atom_indices]

    assert 1 <= len(indices) <= 4, f"Number of indices must be 1, 2, 3 or 4, not {len(indices)}"

    atoms = "-".join([f"{mol[i+1].symbol}{i+1}" for i in indices])

    param_value = geometry.parameter(mol, *indices, pyramidal=pyramidal, sum_of_angles=soa)

    if len(indices) == 1:
        param_value = "  ".join([f"{x: .6f}" for x in mol[indices[0] + 1].coords])
        param_type = GeometricParameter.COORDINATE
    elif len(indices) == 2:
        param_type = GeometricParameter.DISTANCE
    elif len(indices) == 3:
        param_type = GeometricParameter.ANGLE
    elif len(indices) == 4:
        if pyramidal:
            param_type = GeometricParameter.PYRAMIDAL
        elif soa:
            param_type = GeometricParameter.SUMOFANGLES
        else:
            param_type = GeometricParameter.DIHEDRAL
    else:
        raise ValueError("Invalid number of indices")

    param_type, unit, precision = geometric_character_to_info_mapping[param_type]
    print(f"{param_type}({atoms}) = {param_value: .{precision}f}{unit}")


if __name__ == "__main__":
    calculate_geometry_parameter()
