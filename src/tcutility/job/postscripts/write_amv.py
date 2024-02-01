from tcutility import results
import os

# load this calculation
res = results.read(os.getcwd())

# check if the calculation succeeded
if res.status.fatal:
	exit()

# get the molecules that converged
converged_mols = [mol for mol, converged in zip(res.history.coords, res.history.converged) if converged]

# write the molecules to a file
with open('ams.amv', 'w+') as amv:
	# the molecules should not have a header like a regular amv file, but only the coordinates
	for mol in converged_mols:
		for atom in mol:
			amv.write(f'{atom.symbol} {atom.x} {atom.y} {atom.z}\n')
		
		# molecules are separated by empty lines
		amv.write('\n')
