from tcutility.job import ADFJob
from tcutility import data, results, pathfunc, log
import pyfmo
from scm import plams



rows = []
for d, info in log.loadbar(pathfunc.match('calculations/virtual_counting', '{atnum}.{symbol}.{basis_set}').items()):
    orbs = pyfmo.orbitals.Orbitals(f'{d}/adf.rkf')
    occupations = sum([mo.occupation for mo in orbs.mos])
    predicted = data.basis_sets.number_of_virtuals(info.symbol, info.basis_set)
    if int(info.atnum) % 2 == 1:
        predicted *= 2
        nocc = occupations
    else:
        nocc = occupations/2
    
    nvirt = round(len(orbs.mos.mos) - nocc)

    predicted = round(predicted)

    emoji = log.Emojis.good if nvirt == predicted else log.Emojis.fail
    rows.append((emoji, int(info.atnum), info.symbol, info.basis_set, len(orbs.mos.mos), round(nocc), nvirt, predicted, int(info.atnum)%2==1))

rows = list(sorted(rows, key=lambda row: row[3]))
rows = list(sorted(rows, key=lambda row: row[1]))
with open('virtual_counting.txt', 'w+') as out:
	s = log.table(rows, ['Correct?', 'Atom number', 'Symbol', 'Basis', 'Ntotal', 'Nocc', 'Nvirt', 'Nvirtpredicted', 'Unrestricted?'])
	out.write(s)


for basis_set, basis_set_data in data.basis_sets._number_of_orbitals.items():
	if basis_set == 'jcpl':
		continue

	for atom, nvirtuals in basis_set_data.items():
		mol = plams.Molecule()
		symbol = data.atom.symbol(atom)
		atnum = data.atom.atom_number(atom)
		if atnum > 118:
			continue

		mol.add_atom(plams.Atom(symbol=symbol))
		with ADFJob(test_mode=False) as job:
			job.basis_set(basis_set)
			job.molecule(mol)
			job.rundir = 'calculations/virtual_counting'
			job.name = f'{atnum}.{symbol}.{basis_set}'
			job.sbatch(p='tc', n=4)
			job.spin_polarization(atnum%2)

