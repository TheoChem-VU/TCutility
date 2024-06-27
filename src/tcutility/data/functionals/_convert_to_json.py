import json

from tcutility.data.functionals import functionals

with open("available_functionals.json", "w+") as outp:
    for functional, functional_info in functionals.get_available_functionals().items():
        outp.write(json.dumps(functional_info, indent=4))
        outp.write("\n\n")
