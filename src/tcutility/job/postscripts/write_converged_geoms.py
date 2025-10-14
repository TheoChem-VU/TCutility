if __name__ == "__main__":
    import os

    from tcutility import constants, molecule
    from tcutility.results.read import read

    # load this calculation
    res = read(os.getcwd())

    # check if the calculation succeeded
    if res.status.fatal:
        exit()

    os.makedirs("converged_mols", exist_ok=True)
    # get the molecules that converged
    converged_mols = [mol for mol, converged in zip(res.history.molecule, res.history.converged) if converged]
    energies = [energy for energy, converged in zip(res.history.energy, res.history.converged) if converged]
    # write the molecules to a file
    with open("ams.amv", "w+") as amv:
        # the molecules should not have a header like a regular amv file, but only the coordinates
        for i, (mol, energy) in enumerate(zip(converged_mols, energies)):
            for atom in mol:
                amv.write(f"{atom.symbol} {atom.x} {atom.y} {atom.z}\n")

            # molecules are separated by empty lines
            amv.write("\n")

            molecule.save(mol, f"converged_mols/{i}.xyz", comment=f"E = {energy * constants.HA2KCALMOL:.6f} kcal/mol")

            if energy == max(energies):
                molecule.save(mol, "converged_mols/highest_energy.xyz", comment=f"E = {energy * constants.HA2KCALMOL:.6f} kcal/mol")

            if energy == min(energies):
                molecule.save(mol, "converged_mols/lowest_energy.xyz", comment=f"E = {energy * constants.HA2KCALMOL:.6f} kcal/mol")
