import os
from TCutility import results
from pprint import pprint


for calc_dir in os.listdir():
    if calc_dir == '.DS_Store':
        continue
    if not os.path.isdir(calc_dir):
        continue

    try: 
        info = results.read(calc_dir)
        if info.engine == 'dftb':
            pprint(info)
    except AssertionError:
        pass
    except:
        print('Warning:', calc_dir)
        raise

    print()
