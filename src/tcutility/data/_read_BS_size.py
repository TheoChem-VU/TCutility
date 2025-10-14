import json

from tcutility import pathfunc
from tcutility.results.result import Result

degeneracies = {
    "S": 1,
    "P": 3,
    "D": 5,
    "F": 7,
    "G": 9,
}

ret_data = Result()
for d, info in pathfunc.match("/Applications/AMS2023.104.app/Contents/Resources/amshome/atomicdata/ADF/ZORA", "{BS}/{element}").items():
    if "." in info.element:
        continue

    if info.element == "Ni_d9":
        continue

    if info.element == "00README":
        continue

    with open(d) as bsfile:
        lines = bsfile.readlines()

    lines = [line.strip() for line in lines if line.strip()]

    orbs = []
    start_reading = False
    for line in lines:
        if line.lower() == "basis":
            start_reading = True
            continue

        if start_reading:
            if line.lower() == "end":
                break
            orbs.append(line.split()[0])

    norbs = sum([degeneracies[orb[-1].upper()] for orb in orbs])
    ret_data[info.bs][info.element] = norbs

with open("_atom_data_info/norbs.json", "w+") as out:
    out.write(json.dumps(ret_data, indent=4))
