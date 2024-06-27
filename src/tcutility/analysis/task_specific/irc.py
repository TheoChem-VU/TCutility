import pathlib as pl
from typing import List, Tuple, Union

import numpy as np
from scm.plams import Molecule
from tcutility.log import log
from tcutility.results import read
from tcutility.results.result import Result


def create_result_objects(job_dirs: Union[List[str], List[pl.Path]]) -> List[Result]:
    """Creates a list of Result objects from a list of directories."""
    return [read(pl.Path(file)) for file in job_dirs]


def _get_converged_energies(res: Result) -> List[float]:
    """Returns a list of energies of the converged geometries."""
    return [energy for converged, energy in zip(res.history.converged, res.history.energy) if converged]  # type: ignore


def _get_converged_molecules(res: Result) -> List[Molecule]:
    """Returns a list of molecules of the converged geometries."""
    return [mol for converged, mol in zip(res.history.converged, res.history.molecule) if converged]  # type: ignore


def _concatenate_irc_trajectories_by_rmsd(irc_trajectories: List[List[Molecule]], energies: Union[List[List[float]], None]) -> Tuple[List[Molecule], List[float]]:
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
    concatenated_energies: List[float] = energies[0][::-1] if energies is not None else []

    for traj_index in range(len(irc_trajectories) - 1):
        # Calculate RMSD values of two connected trajectories to compare the connection points / molecules
        rmsd_matrix = np.array([[Molecule.rmsd(irc_trajectories[traj_index][i], irc_trajectories[traj_index + 1][j]) for j in [0, -1]] for i in [0, -1]])

        # Flatten the matrix and find the index of the minimum value
        lowest_index = np.argmin(rmsd_matrix.flatten())

        log(f"Lowest RMSD values: {rmsd_matrix.flatten()}", 10)

        # Starting points are connected
        if lowest_index == 0:
            concatenated_mols += irc_trajectories[traj_index + 1][1:]
            concatenated_energies += energies[traj_index + 1][1:] if energies is not None else []
        # Ending points are connected
        elif lowest_index == 1:
            concatenated_mols += irc_trajectories[traj_index + 1][::-1]
            concatenated_energies += energies[traj_index + 1][::-1] if energies is not None else []
        # Something went wrong
        else:
            raise ValueError(f"The RMSD values are not as expected: {rmsd_matrix.flatten()} with {lowest_index=}.")

    return concatenated_mols, concatenated_energies


def concatenate_irc_trajectories(result_objects: List[Result], reverse: bool = False) -> Tuple[List[Molecule], List[float]]:
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
        traj_geometries[i] = _get_converged_molecules(res_obj)
        traj_energies[i] = _get_converged_energies(res_obj)

    concatenated_mols, concatenated_energies = _concatenate_irc_trajectories_by_rmsd(traj_geometries, traj_energies)

    if reverse:
        concatenated_mols = concatenated_mols[::-1]
        concatenated_energies = concatenated_energies[::-1]
    return concatenated_mols, concatenated_energies
