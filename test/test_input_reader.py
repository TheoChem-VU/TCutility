import os
from TCutility import results
from pprint import pprint

j = os.path.join


def test_reading() -> None:
    input_dir = j('..', 'test', 'fixtures', 'input_files')
    for file in os.listdir(input_dir):
        with open(j(input_dir, file)) as inp:
            sett = results.ams.get_ams_input(inp.read())
            pprint(sett)


if __name__ == '__main__':
    test_reading()
