import argparse
import pathlib as pl
from typing import List, Tuple, Union

import numpy as np
from scm.plams import Molecule
from tcutility.log import log
from tcutility.results import read
from tcutility.results.result import Result


def _create_result_objects(job_dirs: Union[List[str], List[pl.Path]]) -> List[Result]:
    """Creates a list of Result objects from a list of directories."""
    return [read(pl.Path(file)) for file in job_dirs]


def _get_converged_energies(res: Result) -> List[float]:
    """Returns a list of energies of the converged geometries."""
    return [energy for converged, energy in zip(res.history.converged, res.history.energy) if converged]  # type: ignore


def _get_converged_molecules(res: Result) -> List[Molecule]:
    """Returns a list of molecules of the converged geometries."""
    return [mol for converged, mol in zip(res.history.converged, res.history.molecule) if converged]  # type: ignore


def _concatenate_irc_trajectories_by_rmsd(irc_trajectories: List[List[Molecule]], energies: List[List[float]]) -> Tuple[List[Molecule], List[float]]:
    """
    Concatenates lists of molecules by comparing the RMSD values of the end and beginnings of the trajectory.
    The entries that are closest to each other are used to concatenate the trajectories.

    Parameters:
        irc_trajectories: A list of lists of Molecule objects representing the trajectories.
        energies: A list of lists of float values representing the energies.

    Returns:
        A tuple containing a list of Molecule objects and a list of energies.

    Raises:
        ValueError: If the RMSD values are not as expected.
    """
    concatenated_mols: List[Molecule] = irc_trajectories[0][::-1]
    concatenated_energies: List[float] = energies[0][::-1]

    for traj_index in range(len(irc_trajectories) - 1):
        # Calculate RMSD values of two connected trajectories to compare the connection points / molecules
        rmsd_matrix = np.array([[Molecule.rmsd(irc_trajectories[traj_index][i], irc_trajectories[traj_index + 1][j]) for j in [0, -1]] for i in [0, -1]])

        # Flatten the matrix and find the index of the minimum value
        lowest_index = np.argmin(rmsd_matrix.flatten())

        log(f"Lowest RMSD values: {rmsd_matrix.flatten()}", 10)

        # Starting points are connected
        if lowest_index == 0:
            concatenated_mols += irc_trajectories[traj_index + 1][1:]
            concatenated_energies += energies[traj_index + 1][1:]
        # Ending points are connected
        elif lowest_index == 1:
            concatenated_mols += irc_trajectories[traj_index + 1][::-1]
            concatenated_energies += energies[traj_index + 1][::-1]
        # Something went wrong
        else:
            raise ValueError(f"The RMSD values are not as expected: {rmsd_matrix.flatten()} with {lowest_index=}.")

    return concatenated_mols, concatenated_energies


def concatenate_irc_trajectories(result_objects: List[Result], user_log_level: int, reverse: bool = False) -> Tuple[List[Molecule], List[float]]:
    """
    Concatenates trajectories from irc calculations, often being forward and backward, through the RMSD values.

    Parameters:
        job_dirs: A list of directories containing the ams.rkf files.
        user_log_level: The log level set by the user.
        reverse: A boolean indicating whether to reverse the trajectory. Default is False.

    Returns:
        A tuple containing a list of Molecule objects and a list of energies.

    Raises:
        Exception: If an exception is raised in the try block, it is caught and printed.
    """
    traj_geometries: List[List[Molecule]] = [[] for _ in result_objects]
    traj_energies: List[List[float]] = [[] for _ in result_objects]

    for i, res_obj in enumerate(result_objects):
        log(f"Processing {res_obj.files.root}", user_log_level)  # type: ignore # root is a valid attribute
        traj_geometries[i] = _get_converged_molecules(res_obj)
        traj_energies[i] = _get_converged_energies(res_obj)
        log(f"IRC trajectory {i+1} has {len(traj_geometries[i])} geometries.", user_log_level)

    log("Concatenating trajectories...", user_log_level)
    concatenated_mols, concatenated_energies = _concatenate_irc_trajectories_by_rmsd(traj_geometries, traj_energies)

    if reverse:
        log("Reversing the trajectory...", user_log_level)
        concatenated_mols = concatenated_mols[::-1]
        concatenated_energies = concatenated_energies[::-1]
    return concatenated_mols, concatenated_energies


def _xyz_format(mol: Molecule) -> str:
    """Returns a string representation of a molecule in the xyz format, e.g.:

    Geometry 1, Energy: -0.5 Ha
    C      0.00000000      0.00000000      0.00000000
    ...
    """
    return "\n".join([f"{atom.symbol:6s}{atom.x:16.8f}{atom.y:16.8f}{atom.z:16.8f}" for atom in mol.atoms])


def _amv_format(mol: Molecule, step: int, energy: Union[float, None] = None) -> str:
    """Returns a string representation of a molecule in the amv format, e.g.:

    Geometry 1, Energy: -0.5 Ha
    C      0.00000000      0.00000000      0.00000000
    ...

    If no energy is provided, the energy is not included in the string representation"""
    if energy is None:
        return f"Geometry {step}\n" + "\n".join([f"{atom.symbol:6s}{atom.x:16.8f}{atom.y:16.8f}{atom.z:16.8f}" for atom in mol.atoms])
    return f"Geometry {step}, Energy: {energy} Ha\n" + "\n".join([f"{atom.symbol:6s}{atom.x:16.8f}{atom.y:16.8f}{atom.z:16.8f}" for atom in mol.atoms])


def write_mol_to_xyz_file(mols: Union[List[Molecule], Molecule], filename: Union[str, pl.Path]) -> None:
    """Writes a list of molecules to a file in xyz format."""
    mols = mols if isinstance(mols, list) else [mols]
    out_file = pl.Path(f"{filename}.xyz")

    [mol.delete_all_bonds() for mol in mols]
    write_string = "\n\n".join([_xyz_format(mol) for mol in mols])
    out_file.write_text(write_string)

    return None


def write_mol_to_amv_file(mols: Union[List[Molecule], Molecule], energies: Union[List[float], None], filename: Union[str, pl.Path]) -> None:
    """Writes a list of molecules to a file in amv format."""
    mols = mols if isinstance(mols, list) else [mols]
    out_file = pl.Path(f"{filename}.amv")
    energies = energies if energies is not None else [0.0 for _ in mols]

    [mol.delete_all_bonds() for mol in mols]
    write_string = "\n\n".join([_amv_format(mol, step, energy) for step, (mol, energy) in enumerate(zip(mols, energies), 1)])
    out_file.write_text(write_string)

    return None


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
    subparser.add_argument("-j", "--jobs", nargs="*", type=str, help="Job directories containing the ams.rkf of the irc calculation(s)")
    subparser.add_argument("-r", "--reverse", action="store_true", help="Reverses the trajectory")
    subparser.add_argument("-o", "--output", type=str, default="./", help="Directory in which the outputfile will be saved")
    subparser.add_argument("-l", "--log_level", type=int, default=20, help="Set the log level. The lower the value, the more is printed. Default is 20 (info).")


def main(args):
    outputdir = pl.Path(args.output).resolve()
    job_dirs = [pl.Path(directory).resolve() for directory in args.jobs]
    res_objects = _create_result_objects(job_dirs)
    molecules, energies = concatenate_irc_trajectories(res_objects, args.log_level, args.reverse)

    outputdir.mkdir(parents=True, exist_ok=True)
    write_mol_to_amv_file(molecules, energies, outputdir / "read_concatenated_mols")
    write_mol_to_xyz_file(molecules, outputdir / "read_concatenated_mols")

    log(f"Output written to {outputdir / 'concatenated_mols'}")
