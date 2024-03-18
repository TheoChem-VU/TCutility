import argparse
import pathlib as pl

import numpy as np

# import matplotlib.pyplot as plt
from scm.plams import AMSJob, AMSResults, Molecule, config, finish, init


def _create_ams_results(file: pl.Path | str) -> AMSResults:
    """Create an AMSResults object from job directory (containing a rkf file)."""
    job: AMSJob = AMSJob.load_external(str(file))
    res: AMSResults = job.results
    res.collect()
    return res


def _get_converged_steps(res: AMSResults) -> list[int]:
    """Return a list of steps where the geometry optimization converged."""
    variables = res.get_history_property("Converged")
    return [i for i, x in enumerate(variables) if x]  # type: ignore


def _get_converged_molecules(res: AMSResults) -> list[Molecule]:
    """Return a list of molecules where the geometry optimization converged."""
    return [res.get_history_molecule(step + 1) for step in _get_converged_steps(res)]  # type: ignore


def _get_converged_energies(res: AMSResults) -> list[float]:
    """Return a list of energies where the geometry optimization converged."""
    return [res.get_history_property("Energy")[i] for i in _get_converged_steps(res)]  # type: ignore


def _concatenate_molecules_by_rmsd(mols1: list[Molecule], mols2: list[Molecule], energies1: list[float], energies2: list[float]) -> tuple[list[Molecule], list[float]]:
    """
    Concatenate two lists of molecules through comparing the RMSD values of the end and beginnings of the trajectory.
    The entries that are closest to each other are used to concatenate the trajectories.
    Compares the first molecule in mols1 with the first and last molecule in mols2.
    Compares the last molecule in mols1 with the first and last molecule in mols2.

    Uses the Molecule.rmsd() static method.
    """

    # Calculate RMSD values and store them in a matrix
    rmsd_matrix = np.array([[Molecule.rmsd(mols1[i], mols2[j]) for j in [0, -1]] for i in [0, -1]])

    # Flatten the matrix and find the index of the minimum value
    lowest_index = np.argmin(rmsd_matrix.flatten())

    if lowest_index == 0:
        _ = mols2.pop(0)
        _ = energies2.pop(0)
        return mols1[::-1] + mols2, energies1[::-1] + energies2
    # elif lowest_index == 1:
    #     _ = mols2.pop(-1)
    #     _ = energies2.pop(-1)
    #     return mols1 + mols2[::-1], energies1 + energies2[::-1]
    # elif lowest_index == 2:
    #     _ = mols2.pop(0)
    #     _ = energies2.pop(0)
    #     return mols2 + mols1[::-1], energies2 + energies1[::-1]
    # elif lowest_index == 3:
    #     _ = mols2.pop(-1)
    #     _ = energies2.pop(-1)
    #     return mols2[::-1] + mols1[::-1], energies2[::-1] + energies1[::-1]
    else:  # This should never happen
        raise ValueError("The RMSD values are not as expected.")


def concatenate_irc_trajectories(job_dirs: list[str] | list[pl.Path], reverse: bool = False) -> tuple[list[Molecule], list[float]]:
    """
    Main function: concatenate trajectories from irc calculations, often being forward and backward, through the RMSD values.

    Arguments:
        job_dirs (list[str] | list[pl.Path]): List of directories containing the ams.rkf files.
        reverse (bool): Reverse the trajectory. Default is False.

    Returns:
        tuple[list[Molecule], list[float]]: A tuple containing a list of Molecule objects and a list of energies.

    Raises:
        Exception: If an exception is raised in the try block, it is caught and printed.

    """
    job_dirs = [pl.Path(file) for file in job_dirs]
    traj_geometries: list[list[Molecule]] = [[] for _ in job_dirs]
    traj_energies: list[list[float]] = [[] for _ in job_dirs]
    current_working_directory = pl.Path.cwd()

    init(path=current_working_directory)
    config.erase_workdir = True
    config.log.stdout = 1

    # This try / except / finally statement is to always remove the plams directory since we do not use it.
    # Could be considered as an alternative to a contextmanager.
    try:
        for i, job_dir in enumerate(job_dirs):
            print(f"Processing {job_dir}")
            res = _create_ams_results(job_dir)
            traj_geometries[i] = _get_converged_molecules(res)
            traj_energies[i] = _get_converged_energies(res)
    except Exception as e:
        print("Got exception in concatenate_irc_trajectories:", e)
    finally:
        finish()

    print("Concatenating trajectories...")
    concatenated_mols, concatenated_energies = _concatenate_molecules_by_rmsd(traj_geometries[0], traj_geometries[1], traj_energies[0], traj_energies[1])

    if reverse:
        print("Reversing the trajectory...")
        concatenated_mols = concatenated_mols[::-1]
        concatenated_energies = concatenated_energies[::-1]
    return concatenated_mols, concatenated_energies


def _xyz_format(mol: Molecule) -> str:
    """Return a string representation of a molecule in the xyz format."""
    return "\n".join([f"{atom.symbol:6s}{atom.x:16.8f}{atom.y:16.8f}{atom.z:16.8f}" for atom in mol.atoms])


def _amv_format(mol: Molecule, step: int, energy: float | None = None) -> str:
    """Return a string representation of a molecule in the amv format."""
    if energy is None:
        return f"Geometry {step}\n" + "\n".join([f"{atom.symbol:6s}{atom.x:16.8f}{atom.y:16.8f}{atom.z:16.8f}" for atom in mol.atoms])
    return f"Geometry {step}, Energy: {energy} Ha\n" + "\n".join([f"{atom.symbol:6s}{atom.x:16.8f}{atom.y:16.8f}{atom.z:16.8f}" for atom in mol.atoms])


def write_mol_to_xyz_file(mols: list[Molecule] | Molecule, filename: str | pl.Path) -> None:
    """Write a list of molecules to a file in a given format."""
    mols = mols if isinstance(mols, list) else [mols]
    out_file = pl.Path(f"{filename}.xyz")

    [mol.delete_all_bonds() for mol in mols]
    write_string = "\n\n".join([_xyz_format(mol) for mol in mols])
    out_file.write_text(write_string)

    return None


def write_mol_to_amv_file(mols: list[Molecule] | Molecule, energies: list[float] | None, filename: str | pl.Path) -> None:
    """Write a list of molecules to a file in a given format."""
    mols = mols if isinstance(mols, list) else [mols]
    out_file = pl.Path(f"{filename}.amv")
    energies = energies if energies is not None else [0.0 for _ in mols]

    [mol.delete_all_bonds() for mol in mols]
    write_string = "\n\n".join([_amv_format(mol, step, energy) for step, (mol, energy) in enumerate(zip(mols, energies), 1)])
    out_file.write_text(write_string)

    return None


def create_subparser(parent_parser: argparse.ArgumentParser):
    subparser = parent_parser.add_parser('concat-irc', 
                                         help="Combine separated IRC paths.",
                                         description="""
        Scripts that takes in two directories containing an IRC file ("ams.rkf") and concatenates them through the RMSD values. Produces a .xyz and .amv file in the specified output directory.
        The output directory is specified with the -o flag. If not specified, the output will be written to the current working directory.
        In addition, the -r flag can be used to reverse the trajectory.

        Note: ALWAYS visualize the .amv file in AMSView to verify the trajectory.
    """)

    # Add the arguments
    subparser.add_argument("-f", "--forward", type=str, help="Job directory containing the ams.rkf with the forward irc calculation")
    subparser.add_argument("-b", "--backward", type=str, help="Job directory containing the ams.rkf with the backward irc calculation")
    subparser.add_argument("-r", "--reverse", action="store_true", help="Reverses the trajectory")
    subparser.add_argument("-o", "--output", type=str, default="./", help="Directory in which the outputfile will be saved")


def main(args):
    outputdir = pl.Path(args.output).resolve()
    job_dirs = [pl.Path(args.forward).resolve(), pl.Path(args.backward).resolve()]
    molecules, energies = concatenate_irc_trajectories(job_dirs, args.reverse)

    outputdir.mkdir(parents=True, exist_ok=True)
    write_mol_to_amv_file(molecules, energies, outputdir / "concatenated_mols")
    write_mol_to_xyz_file(molecules, outputdir / "concatenated_mols")

    print(f"Output written to {outputdir / 'concatenated_mols'}")


if __name__ == "__main__":
    main()
