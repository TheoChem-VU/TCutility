from tcutility import molecule
import os


j = os.path.join

root_dir = j(os.path.split(__file__)[0], 'molecules')


def get(name):
    p = j(root_dir, f'{name.removesuffix(".xyz")}.xyz')
    return molecule.load(p)


def get_molecules(tags=None):
    for f in os.listdir(root_dir):
        if f == '.DS_Store':
            continue
        mol = get(f)
        if tags is None or any(tag in mol.flags.tags for tag in tags):
            yield mol


if __name__ == '__main__':
    for mol in get_molecules():
        print(mol, mol.flags)
