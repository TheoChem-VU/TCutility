from TCutility.results import cache, Result


def get_calc_settings(info: Result) -> Result:
    '''
    Function to read useful calculation settings from kf reader
    '''

    assert info.engine == 'dftb', f'This function reads DFTB data, not {info.engine} data'
    assert 'dftb.rkf' in info.files, f'Missing dftb.rkf file, [{", ".join([": ".join(item) for item in info.files.items()])}]'

    reader_dftb = cache.get(info.files['dftb.rkf'])
    reader_ams = cache.get(info.files['ams.rkf'])
    ret = Result()

    # get the run type of the calculation
    # read and split user input into words
    user_input = str(reader_ams.read('General', 'user input')).strip()
    words = user_input.split()

    # default task is SinglePoint
    ret.task = 'SinglePoint'
    for i, word in enumerate(words):
        # task is always given with the task keyword
        if word.lower() == 'task':
            ret.task = words[i+1]
            break

    # read properties of the calculation
    number_of_properties = int(reader_dftb.read('Properties', 'nEntries'))  # type: ignore plams does not include type hints. Returns int
    for i in range(1, number_of_properties + 1):
        prop_type = str(reader_dftb.read('Properties', f'Type({i})')).strip()
        prop_subtype = str(reader_dftb.read('Properties', f'Subtype({i})')).strip()
        ret.properties[prop_type][prop_subtype] = reader_dftb.read('Properties', f'Value({i})')

    return ret


def get_properties(info: Result) -> Result:
    '''

    '''
    raise NotImplementedError
