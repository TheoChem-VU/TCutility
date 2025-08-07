import os


candidates = ['crest_conformers.xyz', 'crest_rotamers.xyz', 'ensemble/final_ensemble.xyz']
out_dirs = ['conformers', 'rotamers', 'ensembles']
for out_dir, candidate in zip(out_dirs, candidates):
	if not os.path.exists(candidate):
		continue

	os.makedirs(out_dir, exist_ok=True)
	with open(candidate) as xyz:
		lines = xyz.readlines()
		natoms = int(lines[0].strip())
		nmols = len(lines)//(natoms + 2)
		mol_lines = [lines[(natoms+2)*i:(natoms+2)*(i+1)] for i in range(nmols)]
