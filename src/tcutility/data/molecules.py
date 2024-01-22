from tcutility import molecule
import os


j = os.path.join

root_dir = j(os.path.split(__file__)[0], 'molecules')

def get_mol(name):
	p = j(root_dir, f'{name.removesuffix(".xyz")}.xyz')
	return molecule.load(p)


def get_available_molecules():
	for f in os.listdir(root_dir):
		if f == '.DS_Store':
			continue

		yield get_mol(f)

if __name__ == '__main__':
	for mol in get_available_molecules():
		print(mol.flags.tags)
