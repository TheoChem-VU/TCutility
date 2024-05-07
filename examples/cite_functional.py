from tcutility import data, cite

for doi in data.functionals.get('r2SCAN').dois:
	print(cite.cite(doi))
