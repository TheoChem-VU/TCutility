import json
import pathlib as pl
from tcutility import data


available_basis_sets = { 
'ADF': [
	'SZ',
	'DZ',
	'DZP',
	'TZP',
	'TZ2P',
	'QZ4P',
	'mTZ2P',
	'AUG/ASZ',
	'AUG/ADZ',
	'AUG/ADZP',
	'AUG/ATZP',
	'AUG/ATZ2P',
	'Corr/TZ3P',
	'Corr/QZ6P',
	'Corr/ATZ3P',
	'Corr/AQZ6P',
	'ET/ET-pVQZ',
	'ET/ET-QZ3P',
	'ET/ET-QZ3P-1DIFFUSE',
	'ET/ET-QZ3P-2DIFFUSE',
	'ET/ET-QZ3P-3DIFFUSE',
	'TZ2P-J',
	'QZ4P-J',
	'POLTDDFT/DZ',
	'POLTDDFT/DZP',
	'POLTDDFT/TZP',
],
'BAND': {},
'ORCA': {},
}


# read data
data_dir = pl.Path(__file__).parents[0] / "_atom_data_info"

with open(data_dir / "norbs.json") as inp:
	_number_of_orbitals = json.loads(inp.read())


def number_of_orbitals(element, basis_set):
	'''
	Get the number of atomic orbitals for a certain element and basis-set.

	Args:
		element: the element for which to get the number of AOs.
		basis_set: the basis-set for which to get the number of AOs.

	.. warning::
		This function currently only works for the following basis-sets: 
		[``SZ``, ``DZ``, ``DZP``, ``TZP``, ``TZ2P``, ``TZ2P-J``, ``mTZ2P``, ``QZ4P``, ``QZ4P-J``, ``jcpl``].
		It also only works for no-frozen-core calculations.
	'''
	symbol = data.atom.symbol(element)
	return _number_of_orbitals[basis_set][symbol]


def number_of_virtuals(element, basis_set):
	'''
	Get the number of virtual atomic orbitals for a certain element and basis-set.
	The number of virtuals is equal to the total number of AOs minus half the number of electrons in the atom.

	Args:
		element: the element for which to get the number of AOs.
		basis_set: the basis-set for which to get the number of AOs.

	.. warning::
		This function currently only works for the following basis-sets: 
		[``SZ``, ``DZ``, ``DZP``, ``TZP``, ``TZ2P``, ``TZ2P-J``, ``mTZ2P``, ``QZ4P``, ``QZ4P-J``, ``jcpl``].
		It also only works for no-frozen-core calculations.
	'''
	num = data.atom.atom_number(element)
	symbol = data.atom.symbol(element)
	return _number_of_orbitals[basis_set][symbol] - num//2


if __name__ == '__main__':
	print(number_of_orbitals('Pd', 'DZ'))
	print(number_of_virtuals('Pd', 'DZ'))
