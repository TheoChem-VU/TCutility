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

    # set the calculation task at a higher level
    ret.task = info.input.task

    # read properties of the calculation
    number_of_properties = int(reader_dftb.read('Properties', 'nEntries'))  # type: ignore plams does not include type hints. Returns int
    for i in range(1, number_of_properties + 1):
        prop_type = str(reader_dftb.read('Properties', f'Type({i})')).strip()
        prop_subtype = str(reader_dftb.read('Properties', f'Subtype({i})')).strip()
        ret.properties[prop_type][prop_subtype] = reader_dftb.read('Properties', f'Value({i})')

    return ret


def get_properties(info: Result) -> Result:
    '''Function to get properties from an ADF calculation.

    Args:
        info: Result object containing ADF properties.

    Returns:
        :Result object containing properties from the ADF calculation:

            - **energy.bond (float)** – bonding energy (|kcal/mol|).
    '''

    assert info.engine == 'dftb', f'This function reads DFTB data, not {info.engine} data'
    assert 'dftb.rkf' in info.files, f'Missing dftb.rkf file, [{", ".join([": ".join(item) for item in info.files.items()])}]'

    reader_dftb = cache.get(info.files['dftb.rkf'])
    ret = Result()

    # properties are not given as in ADF. Instead you must first know which index each key is at. For example we might have:
    # (Properties, SubType(k)) == Coulomb
    # therefore, to get the Coulomb energy we first have to know the index k
    # we therefore first loop through every property entry and store the properties in order in a list
    number_of_properties = reader_dftb.read('Properties', 'nEntries')
    properties = []
    for i in range(1, number_of_properties+1):
        properties.append(reader_dftb.read('Properties', f'Subtype({i})').strip())
    print(properties)

    # read energies (given in Ha i
    return ret

