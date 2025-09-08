from tcutility.job import ADFFragmentJob
from tcutility import molecule

# load a molecule
mol = molecule.load("NH3BH3.xyz")

# define a new job using the Job context-manager
with ADFFragmentJob() as job:
    # add the molecule
    job.molecule(mol)
    # add the fragments. The fragment atoms are defined in the input xyz file
    for fragment_name, fragment in molecule.guess_fragments(mol).items():
        job.add_fragment(fragment, fragment_name)
