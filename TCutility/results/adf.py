from TCutility.results import cache, Result
from TCutility import constants, ensure_list
from typing import List


def get_calc_settings(info: Result) -> Result:
    '''Function to read calculation settings for an ADF calculation.

    Args:
        info: Result object containing ADF calculation settings.

    Returns:
        :Result object containing properties from the ADF calculation:

            - **task (str)** – the task that was set for the calculation.
            - **relativistic (bool)** – whether or not relativistic effects were enabled.
            - **unrestricted_sfos (bool)** – whether or not SFOs are treated in an unrestricted manner.
            - **unrestricted_mos (bool)** – whether or not MOs are treated in an unrestricted manner.
            - **symmetry.group (str)** – the symmetry group selected for the molecule.
            - **symmetry.labels (list[str])** – the symmetry labels associated with the symmetry group.
            - **used_regions (bool)** – whether regions were used in the calculation.
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
    '''Function to get properties from an ADF calculation.

    Args:
        info: Result object containing ADF properties.

    Returns:
        :Result object containing properties from the ADF calculation:

            - **energy.bond (float)** – bonding energy (|kcal/mol|).
            - **energy.elstat (float)** – total electrostatic potential (|kcal/mol|).
            - **energy.orbint.total (float)** – total orbital interaction energy containing contributions from each symmetry label (|kcal/mol|).
            - **energy.orbint.{symmetry label} (float)** – orbital interaction energy from a specific symmetry label (|kcal/mol|).
            - **energy.pauli.total (float)** – total Pauli repulsion energy (|kcal/mol|).
            - **energy.dispersion (float)** – total dispersion energy (|kcal/mol|).
            - **vibrations.number_of_modes (int)** – number of vibrational modes for this molecule, 3N-5 for non-linear molecules and 3N-6 for linear molecules, where N is the number of atoms.
            - **vibrations.number_of_imaginary_modes (int)** – number of imaginary vibrational modes for this molecule.
            - **vibrations.frequencies (float)** – vibrational frequencies associated with the vibrational modes, sorted from low to high (|cm-1|).
            - **vibrations.intensities (float)** – vibrational intensities associated with the vibrational modes (|km/mol|).
            - **vibrations.modes (list[float])** – list of vibrational modes sorted from low frequency to high frequency.
            - **vdd.charges (list[float])** - list of Voronoi Deformation Denisty (VDD) charges in [electrons], being the difference between the final (SCF) and initial VDD charges. 
    '''

    assert info.engine == 'adf', f'This function reads ADF data, not {info.engine} data'
    assert 'adf.rkf' in info.files, f'Missing adf.rkf file, [{", ".join([": ".join(item) for item in info.files.items()])}]'

    reader_adf = cache.get(info.files['adf.rkf'])
    ret = Result()

    # read energies (given in Ha in rkf files)
    ret.energy.bond = reader_adf.read('Energy', 'Bond Energy') * constants.HA2KCALMOL
    ret.energy.elstat = reader_adf.read('Energy', 'elstat') * constants.HA2KCALMOL
    ret.energy.orbint.total = reader_adf.read('Energy', 'Orb.Int. Total') * constants.HA2KCALMOL
    for symlabel in info.adf.symmetry.labels:
        symlabel = symlabel.split(':')[0]
        ret.energy.orbint[symlabel] = reader_adf.read('Energy', f'Orb.Int. {symlabel}') * constants.HA2KCALMOL
    ret.energy.pauli.total = reader_adf.read('Energy', 'Pauli Total') * constants.HA2KCALMOL
    ret.energy.dispersion = reader_adf.read('Energy', 'Dispersion Energy') * constants.HA2KCALMOL

    # vibrational information
    if ('Vibrations', 'nNormalModes') in reader_adf:
        ret.vibrations.number_of_modes = reader_adf.read('Vibrations', 'nNormalModes')
        freqs = reader_adf.read('Vibrations', 'Frequencies[cm-1]')
        ints = reader_adf.read('Vibrations', 'Intensities[km/mol]')
        ret.vibrations.frequencies = freqs if isinstance(freqs, list) else [freqs]
        ret.vibrations.intensities = ints if isinstance(ints, list) else [ints]
        ret.vibrations.number_of_imag_modes = len([freq for freq in freqs if freq < 0])
        ret.vibrations.modes = []    
        for i in range(ret.vibrations.number_of_modes):
            ret.vibrations.modes.append(reader_adf.read('Vibrations', f'NoWeightNormalMode({i+1})'))

    # read the Voronoi Deformation Charges Deformation (VDD) before and after SCF convergence (being "inital" and "SCF")
    vdd_scf: List[float] = ensure_list(reader_adf.read('Properties', 'AtomCharge_SCF Voronoi'))  # type: ignore since plams does not include typing for KFReader. List[float] is returned
    vdd_ini: List[float] = ensure_list(reader_adf.read('Properties', 'AtomCharge_initial Voronoi'))  # type: ignore since plams does not include typing for KFReader. List[float] is returned

    # VDD charges are scf - initial charges. Note, these are in units of electrons while most often these are denoted in mili-electrons
    ret.vdd.charges = [float((scf - ini)) for scf, ini in zip(vdd_scf, vdd_ini)]

    # Possible enhancement: get the VDD charges per irrep, denoted by the "Voronoi chrg per irrep" in the "Properties" section in the adf.rkf. 
    # The ordering is not very straightfoward so this is a suggestion for the future with keys: ret.vdd.[IRREP]

    return ret


def get_level_of_theory(info: Result) -> Result:
    '''Function to get the level-of-theory from an input-file.

    Args:
        inp_path: Path to the input file. Can be a .run or .in file create for AMS

    Returns:
        :Dictionary containing information about the level-of-theory:
            
            - **summary (str)** - a summary string that gives the level-of-theory in a human-readable format.
            - **xc.functional (str)** - XC-functional used in the calculation.
            - **xc.category (str)** - category the XC-functional belongs to. E.g. GGA, MetaHybrid, etc ...
            - **xc.dispersion (str)** - the dispersion correction method used during the calculation.
            - **xc.summary (str)** - a summary string that gives the XC-functional information in a human-readable format.
            - **basis.type (str)** - the size/type of the basis-set.
            - **basis.core (str)** - the size of the frozen-core approximation.
            - **quality (str)** - the numerical quality setting.
    '''
    sett = info.input
    ret = Result()
    # print(json.dumps(sett, indent=4))
    xc_categories = ['GGA', 'LDA', 'MetaGGA', 'MetaHybrid', 'Model', 'LibXC', 'DoubleHybrid', 'Hybrid', 'MP2', 'HartreeFock']
    ret.xc.functional = 'VWN'
    ret.xc.category = 'LDA'
    for cat in xc_categories:
        if cat.lower() in [key.lower() for key in sett.adf.xc]:
            ret.xc.functional = sett.adf.xc[cat]
            ret.xc.category = cat

    ret.basis.type = sett.adf.basis.type
    ret.basis.core = sett.adf.basis.core
    ret.quality = sett.adf.NumericalQuality or 'Normal'

    ret.xc.dispersion = None
    if 'dispersion' in [key.lower() for key in sett.adf.xc]:
        ret.xc.dispersion = " ".join(sett.adf.xc.dispersion.split())

    ret.xc.empirical_scaling = None
    if 'empiricalscaling' in [key.lower() for key in sett.adf.xc]:
        ret.xc.empiricalscaling = " ".join(sett.adf.xc.empiricalscaling)

    # build the level-of-theory string, as we often have in papers
    ret.xc.summary = f'{ret.xc.functional}'
    if ret.xc.dispersion:
        if ret.xc.dispersion.lower() == 'grimme3':
            ret.xc.summary += '-D3'
        if ret.xc.dispersion.lower() == 'grimme3 bjdamp':
            ret.xc.summary += '-D3(BJ)'
        if ret.xc.dispersion.lower() == 'grimme4':
            ret.xc.summary += '-D4'
        if ret.xc.dispersion.lower() == 'ddsc':
            ret.xc.summary += '-dDsC'
        if ret.xc.dispersion.lower() == 'UFF':
            ret.xc.summary += '-dUFF'
        if ret.xc.dispersion.lower() == 'MBD':
            ret.xc.summary += '-MBD@rsSC'
        if ret.xc.dispersion.lower() == 'default':
            ret.xc.summary += '-D'

    ret.summary = ret.xc.summary + f'/{ret.basis.type}/{ret.quality}'
    return ret
