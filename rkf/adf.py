from yutility import log, dictfunc
from TCutility.rkf import info as rkf_info
from scm import plams


def get_calc_settings(info: dictfunc.DotDict) -> dictfunc.DotDict:
    '''
    Function to read useful info about orbitals from kf reader
    '''

    assert info.engine == 'adf', f'This function reads ADF data, not {info.engine} data'
    assert 'adf.rkf' in info.files, f'Missing adf.rkf file, [{", ".join([": ".join(item) for item in info.files.items()])}]'

    reader_adf = cache.get(info.files['adf.rkf'])
    reader_ams = cache.get(info.files['ams.rkf'])
    ret = dictfunc.DotDict()

    # determine if calculation used relativistic corrections
    # if it did, variable 'escale' will be present in 'SFOs'
    # if it didnt, only variable 'energy' will be present
    ret.relativistic = ('SFOs', 'escale') in reader

    # determine if SFOs are unrestricted or not
    ret.unrestricted_sfos = ('SFOs', 'energy_B') in reader

    if ('Geometry', 'grouplabel') in reader:
    	ret.symmetry.group = reader.read('Geometry', 'grouplabel').strip()

    # get the symmetry labels
    if ('Symmetry', 'symlab') in reader:
        ret.symmetry.labels = reader.read('Symmetry', 'symlab').strip().split()
    elif ('Geometry', 'grouplabel') in reader:
        ret.symmetry.labels = symmetry.labels[reader.read('Geometry', 'grouplabel').strip()]
    else:
        ret.symmetry.labels = symmetry.labels['NOSYM']

    # determine if MOs are unrestricted or not
    ret.unrestricted_mos = (ret.symmetry.labels[0], 'eps_B') in reader

    # determine if the calculation used regions or not
    frag_order = reader.read('Geometry', 'fragment and atomtype index')
    frag_order = frag_order[:len(frag_order)//2]
    ret.used_regions = max(frag_order) != len(frag_order)

    return ret