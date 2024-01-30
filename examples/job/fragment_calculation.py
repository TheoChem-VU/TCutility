from tcutility.job import ADFFragmentJob
from tcutility import molecule

# this example will demonstrate how you may separate two fragments from each other

'''
The NH3BH3.xyz file looks like this:

	8

	N       0.00000000       0.00000000      -0.81474153 frag=Donor  # method 1
	B      -0.00000000      -0.00000000       0.83567034 frag=Acceptor
	H       0.47608351      -0.82460084      -1.14410295 frag=Donor
	H       0.47608351       0.82460084      -1.14410295 frag=Donor
	H      -0.95216703       0.00000000      -1.14410295 frag=Donor
	H      -0.58149793       1.00718395       1.13712667 frag=Acceptor
	H      -0.58149793      -1.00718395       1.13712667 frag=Acceptor
	H       1.16299585      -0.00000000       1.13712667 frag=Acceptor

	frag_Donor = 1, 3, 4, 5  # method 2
	frag_Acceptor = 2, 6, 7, 8
'''

# a simple donor-acceptor complex with randomly ordered atoms
# the atoms have tags with them that denote the fragment they belong to
# two ways are presented. first is to put the tags on the atoms
# second is to put the tags at the bottom in a list
mol = molecule.load('NH3BH3.xyz')  # load the molecule using our own function. This also loads meta-data


# ### Method 1 ### #
'''
The first method uses the atom flags defined in the xyz file. 
This reads anything after the atom definition, for example it 
will read the frag= part and store it as atom.flags.frag.
'''
fragment_names = set(atom.flags.frag for atom in mol)  # store fragment names here
fragment_atoms = {name: [] for name in fragment_names}  # store atoms here

for atom in mol:
	# get the fragment the atom belongs to and add it to the list
	fragment_atoms[atom.flags.frag].append(atom)

with ADFFragmentJob(test_mode=True) as job1:
	# add the fragments to the job one by one
	for fragment_name, atoms in fragment_atoms.items():
		job1.add_fragment(atoms, fragment_name)

	# set the job settings
	job1.functional('BLYP')
	job1.basis_set('TZ2P')


# ### Method 2 ### #
'''
This method uses the molecular flags defined below the atom definitions.
The flags are stored as mol.flags.frag_Donor and mol.flags.frag_Acceptor. 
They both hold a list of integers which we will first turn into lists of atoms.
'''
frag_flags = {flag.removeprefix('frag_'): data for flag, data in mol.flags.items() if flag.startswith('frag_')}
frag_atoms = {frag: [mol[i] for i in x] for frag, x in frag_flags.items()}

with ADFFragmentJob(test_mode=True) as job2:
	# add the fragments to the job one by one
	for fragment_name, atoms in fragment_atoms.items():
		job2.add_fragment(atoms, fragment_name)

	# set the job settings
	job2.functional('BLYP')
	job2.basis_set('TZ2P')


# ### Method 3 ### #
'''
This method is similar to method 2, but we can now supply a molecule to the 
parent job and then define the fragments based on atom indices.
'''
molecule.guess_fragments(mol)
fragment_indices = {flag.removeprefix('frag_'): x for flag, x in mol.flags.items() if flag.startswith('frag_')}

with ADFFragmentJob(test_mode=True) as job3:
	job3.molecule(mol)
	for fragment_name, indices in fragment_indices.items():
		job3.add_fragment(indices, fragment_name)

	# set the job settings
	job3.functional('BLYP')
	job3.basis_set('TZ2P')


# check the fragments for each method
print('# ### Method 1 ### #')
print(job1.childjobs)
[print(frag_name, j._molecule) for frag_name, j in job1.childjobs.items()]

print('# ### Method 2 ### #')
print(job2.childjobs)
[print(frag_name, j._molecule) for frag_name, j in job2.childjobs.items()]

print('# ### Method 3 ### #')
print(job3.childjobs)
[print(frag_name, j._molecule) for frag_name, j in job3.childjobs.items()]
