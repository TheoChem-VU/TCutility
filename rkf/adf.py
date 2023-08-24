from yutility import log, dictfunc
from TCutility.rkf import cache


def get_calc_settings(info: dictfunc.DotDict) -> dictfunc.DotDict:
    '''
    Function to read useful calculation settings from kf reader
    '''

    assert info.engine == 'adf', f'This function reads ADF data, not {info.engine} data'
    assert 'adf.rkf' in info.files, f'Missing adf.rkf file, [{", ".join([": ".join(item) for item in info.files.items()])}]'

    reader_adf = cache.get(info.files['adf.rkf'])
    reader_ams = cache.get(info.files['ams.rkf'])
    ret = dictfunc.DotDict()

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
    elif ('Geometry', 'grouplabel') in reader_adf:
        ret.symmetry.labels = symmetry.labels[reader_adf.read('Geometry', 'grouplabel').strip()]
    else:
        ret.symmetry.labels = symmetry.labels['NOSYM']

    # determine if MOs are unrestricted or not
    ret.unrestricted_mos = (ret.symmetry.labels[0], 'eps_B') in reader_adf

    # determine if the calculation used regions or not
    frag_order = reader_adf.read('Geometry', 'fragment and atomtype index')
    frag_order = frag_order[:len(frag_order)//2]
    ret.used_regions = max(frag_order) != len(frag_order)

    return ret


def get_properties(info: dictfunc.DotDict) -> dictfunc.DotDict:
	'''
	
	'''
