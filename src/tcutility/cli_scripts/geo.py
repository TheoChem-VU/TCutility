"""Module containing functions for calculating geometrical parameters for molecules"""

from typing import Dict, List, Tuple

import click
from strenum import StrEnum

from tcutility import geometry, molecule
from tcutility.results.read import read


class GeometricParameter(StrEnum):
    """Enum class for geometric parameters"""

    COORDINATE = "Coordinate"
    DISTANCE = "Distance"
    ANGLE = "Angle"
    DIHEDRAL = "Dihedral"
    PYRAMIDAL = "Pyramidal"
    SUMOFANGLES = "SumOfAngles"


geometric_character_to_info_mapping: Dict[GeometricParameter, Tuple[str, str, int]] = {
    GeometricParameter.COORDINATE: ("Coordinate", "Å", 6),
    GeometricParameter.DISTANCE: ("Distance", " Å", 3),
    GeometricParameter.ANGLE: ("Angle", "°", 2),
    GeometricParameter.DIHEDRAL: ("Dihedral", "°", 2),
    GeometricParameter.PYRAMIDAL: ("Pyramidal", "°", 2),
    GeometricParameter.SUMOFANGLES: ("SumOfAngles", "°", 2),
}


@click.command("geo")
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
    For 0 indices we return all coordinates of the molecule in PATH.
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
        mol = read(path).molecule.output

    assert 0 <= len(atom_indices) <= 4, f"Number of atom indices must be 1, 2, 3 or 4, not {len(atom_indices)}"

    if len(atom_indices) == 0:
        mol.delete_all_bonds()
        print(mol)
        return

    atom_indices = [int(i) - 1 for i in atom_indices]

    atoms = "-".join([f"{mol[i + 1].symbol}{i + 1}" for i in atom_indices])

    param_value = geometry.parameter(mol, *atom_indices, pyramidal=pyramidal, sum_of_angles=soa)

    if len(atom_indices) == 1:
        param_type, unit, precision = geometric_character_to_info_mapping[GeometricParameter.COORDINATE]
        param_value = "  ".join([f"{x: .{precision}f}" for x in mol[atom_indices[0] + 1].coords])
        print(f"{param_type}({atoms}) = {param_value} {unit}")
        return

    elif len(atom_indices) == 2:
        param_type = GeometricParameter.DISTANCE
    elif len(atom_indices) == 3:
        param_type = GeometricParameter.ANGLE
    elif len(atom_indices) == 4:
        if pyramidal:
            param_type = GeometricParameter.PYRAMIDAL
        elif soa:
            param_type = GeometricParameter.SUMOFANGLES
        else:
            param_type = GeometricParameter.DIHEDRAL
    else:
        raise ValueError("Invalid number of atom indices")

    param_type, unit, precision = geometric_character_to_info_mapping[param_type]
    print(f"{param_type}({atoms}) = {param_value: .{precision}f}{unit}")


if __name__ == "__main__":
    calculate_geometry_parameter()
