from tcutility import cite, get_functional

for doi in get_functional("r2SCAN").dois:
    cite(doi)
