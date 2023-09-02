from TCutility.results import cache, Result


ha2kcalmol = 627.509474


def get_calc_settings(info: Result) -> Result:
    '''
    Function to read useful calculation settings from kf reader
    '''

    assert info.engine == 'adf', f'This function reads ADF data, not {info.engine} data'
    assert 'adf.rkf' in info.files, f'Missing adf.rkf file, [{", ".join([": ".join(item) for item in info.files.items()])}]'

    reader_adf = cache.get(info.files['adf.rkf'])
    reader_ams = cache.get(info.files['ams.rkf'])
    ret = Result()

    # get the run type of the calculation
    # read and split user input into words
    user_input = reader_ams.read('General', 'user input').strip()
    words = user_input.split()

    # default task is SinglePoint
    ret.task = 'SinglePoint'
    for i, word in enumerate(words):
        # task is always given with the task keyword
        if word.lower() == 'task':
            ret.task = words[i+1]
            break

    # determine if calculation used relativistic corrections
    # if it did, variable 'escale' will be present in 'SFOs'
    # if it didnt, only variable 'energy' will be present
    ret.relativistic = ('SFOs', 'escale') in reader_adf

    # determine if SFOs are unrestricted or not
    ret.unrestricted_sfos = ('SFOs', 'energy_B') in reader_adf

    if ('Geometry', 'grouplabel') in reader_adf:
        ret.symmetry.group = reader_adf.read('Geometry', 'grouplabel').strip()

    # get the symmetry labels
    if ('Symmetry', 'symlab') in reader_adf:
        ret.symmetry.labels = reader_adf.read('Symmetry', 'symlab').strip().split()

    # determine if MOs are unrestricted or not
    ret.unrestricted_mos = (ret.symmetry.labels[0], 'eps_B') in reader_adf

    # determine if the calculation used regions or not
    frag_order = reader_adf.read('Geometry', 'fragment and atomtype index')
    frag_order = frag_order[:len(frag_order)//2]
    ret.used_regions = max(frag_order) != len(frag_order)

    return ret


def get_properties(info: Result) -> Result:
    '''
    
    '''

    assert info.engine == 'adf', f'This function reads ADF data, not {info.engine} data'
    assert 'adf.rkf' in info.files, f'Missing adf.rkf file, [{", ".join([": ".join(item) for item in info.files.items()])}]'

    reader_adf = cache.get(info.files['adf.rkf'])
    reader_ams = cache.get(info.files['ams.rkf'])
    ret = Result()

    # read energies (given in Ha in rkf files)
    ret.energy.bond = reader_adf.read('Energy', 'Bond Energy') * ha2kcalmol
    ret.energy.elstat = reader_adf.read('Energy', 'elstat') * ha2kcalmol
    ret.energy.orbint.total = reader_adf.read('Energy', 'Orb.Int. Total') * ha2kcalmol
    for symlabel in info.adf.symmetry.labels:
        ret.energy.orbint[symlabel] = reader_adf.read('Energy', f'Orb.Int. {symlabel}') * ha2kcalmol
    ret.energy.pauli.total = reader_adf.read('Energy', 'Pauli Total') * ha2kcalmol
    ret.energy.dispersion = reader_adf.read('Energy', 'Dispersion Energy') * ha2kcalmol

    # vibrational information
    ret.vibrations.number_of_modes = reader_adf.read('Vibrations', 'nNormalModes')
    freqs = reader_adf.read('Vibrations', 'Frequencies[cm-1]')
    ints = reader_adf.read('Vibrations', 'Intensities[km/mol]')
    ret.vibrations.frequencies = freqs if isinstance(freqs, list) else [freqs]
    ret.vibrations.intensities = ints if isinstance(ints, list) else [ints]
    ret.vibrations.number_of_imag_modes = len([freq for freq in freqs if freq < 0])
    ret.vibrations.modes = []    
    for i in range(ret.vibrations.number_of_modes):
        ret.vibrations.modes.append(reader_adf.read('Vibrations', f'NoWeightNormalMode({i+1})'))

    return ret
