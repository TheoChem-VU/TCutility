from tcutility.results2 import result, detect_filetype
from tcutility import cache, ensure_list
import numpy as np
from scm import plams



@cache.cache
def get_adf_reader(path: str) -> plams.KFReader:
    '''
    Get the KFReader associated with the path.
    This function is expected to be slow so we cache it.
    '''
    if detect_filetype.detect(path) == 'adf_rkf':
        reader = plams.KFReader(path)
        return reader


def _read_settings(path: str) -> result.NestedDict:
    """Function to read calculation settings for an ADF calculation.

    Args:
        info: result.NestedDict object containing ADF calculation settings.

    Returns:
        :result.NestedDict object containing properties from the ADF calculation:

            - **task (str)** – the task that was set for the calculation.
            - **relativistic (bool)** – whether or not relativistic effects were enabled.
            - **relativistic_type (str)** – the name of the relativistic approximation used.
            - **unrestricted_sfos (bool)** – whether or not SFOs are treated in an unrestricted manner.
            - **unrestricted_mos (bool)** – whether or not MOs are treated in an unrestricted manner.
            - **symmetry.group (str)** – the symmetry group selected for the molecule.
            - **symmetry.labels (list[str])** – the symmetry labels associated with the symmetry group.
            - **used_regions (bool)** – whether regions were used in the calculation.
            - **charge (int)** - the charge of the system.
            - **spin_polarization (int)** - the spin-polarization of the system.
            - **multiplicity (int)** - the multiplicity of the system. This is equal to 2|S|+1 for spin-polarization S.
    """
    reader = get_adf_reader(path)
    ret = result.NestedDict()

    # set the calculation task at a higher level
    ret.set('task', reader.read('General', 'runtype').title().replace(' ', ''))

    relativistic_type_map = {
        0: "None",
        1: "scalar Pauli",
        3: "scalar ZORA",  # scalar ZORA + MAPA
        4: "scalar ZORA + full pot.",
        5: "scalar ZORA + APA",
        6: "scalar X2C + MAPA",
        7: "scalar X2C ZORA + MAPA",
        11: "spin-orbit Pauli",
        13: "spin-orbit ZORA",  # spin-orbit ZORA + MAPA
        14: "spin-orbit ZORA + full pot.",
        15: "spin-orbit ZORA + APA",
        16: "spin-orbit X2C + MAPA",
        17: "spin-orbit X2C ZORA + MAPA",
    }
    # determine if calculation used relativistic corrections
    # if it did, variable 'escale' will be present in 'SFOs'
    # if it didnt, only variable 'energy' will be present
    ret.set('relativistic_type', ("SFOs", "escale") in reader)
    ret.set('relativistic_type', relativistic_type_map[reader.read("General", "ioprel")])

    # determine if MOs are unrestricted or not
    # general, nspin is 1 for restricted and 2 for unrestricted calculations
    ret.set('unrestricted_mos', reader.read("General", "nspin") == 2)

    # determine if SFOs are unrestricted or not
    ret.set('unrestricted_sfos', reader.read("General", "nspinf") == 2)

    # get the symmetry group
    ret.set('symmetry', 'group', reader.read("Geometry", "grouplabel").strip())

    # get the symmetry labels
    ret.set('symmetry', 'labels', reader.read("Symmetry", "symlab").strip().split())

    # determine if the calculation used regions or not
    frag_order = reader.read("Geometry", "fragment and atomtype index")
    frag_order = frag_order[: len(frag_order) // 2]
    ret.set('used_regions', max(frag_order) != len(frag_order))

    ret.set('charge', reader.read("Molecule", "Charge"))

    ret.set('spin_polarization', 0)
    if ret.get('unrestricted_mos'):
        nalpha = 0
        nbeta = 0
        for label in ret.get('symmetry', 'labels'):
            nalpha += sum(ensure_list(reader.read(label, "froc_A")))
            nbeta += sum(ensure_list(reader.read(label, "froc_B")))
        ret.set('spin_polarization', nalpha - nbeta)
    ret.set('multiplicity', 2 * ret.get('spin_polarization') + 1)

    return ret


def _read_excitations(path: str) -> result.NestedDict:
    reader = get_adf_reader(path)
    ret = result.NestedDict()

    # check if there are excitations
    if ('Symmetry', 'symlab excitations') not in reader:
        return ret

    excitation_types = []
    symlab_exc = reader.read('Symmetry', 'symlab excitations').split()
    for section, variable in reader:
        if not section.startswith('Excitations'):
            continue

        _, exctyp, irrep = section.split()
        if (exctyp, irrep) in excitation_types:
            continue

        excitation_types.append((exctyp, irrep))

        ret.set(irrep, exctyp, 'number_of_excitations', reader.read(section, 'nr of excenergies'))
        ret.set(irrep, exctyp, 'energies', np.array(reader.read(section, 'excenergies')))  # in Ha

        # values used to convert excitation photon energies to wavelengths
        c = 299_792_458e9  # nm/s
        h = 0.0367502 * 4.135_667_696e-15  # Ha s
        ret.set(irrep, exctyp, 'wavelengths', (h * c) / ret.get(irrep, exctyp, 'energies')) # in nm
        ret.set(irrep, exctyp, 'oscillator_strengths', np.array(reader.read(section, 'oscillator strengths')))  # in km mol
        ret.set(irrep, exctyp, 'transition_dipole_moments', np.array(reader.read(section, 'transition dipole moments')).reshape(ret.get(irrep, exctyp, 'number_of_excitations'), 3))

        ret.set(irrep, exctyp, 'contributions', [])
        ret.set(irrep, exctyp, 'from_MO', [])
        ret.set(irrep, exctyp, 'to_MO', [])
        ret.set(irrep, exctyp, 'from_MO_idx', [])
        ret.set(irrep, exctyp, 'to_MO_idx', [])
        ret.set(irrep, exctyp, 'from_MO_spin', [])
        ret.set(irrep, exctyp, 'to_MO_spin', [])
        ret.set(irrep, exctyp, 'from_MO_irrep', [])
        ret.set(irrep, exctyp, 'to_MO_irrep', [])

        for exc_index in range(1, ret.get(irrep, exctyp, 'number_of_excitations') + 1):
            contr = ensure_list(reader.read(section, f'contr {exc_index}'))
            contr_idx = ensure_list(reader.read(section, f'contr index {exc_index}'))
            contr_spin = ensure_list(reader.read(section, f'contr spin {exc_index}'))
            is_unrestricted = 2 in contr_spin
            contr_irrep = ensure_list(reader.read(section, f'contr irep index {exc_index}'))
            ncontr = len(contr_idx) // 2 

            MO_names = []
            for idx, spin, irrep_idx in zip(contr_idx, contr_spin, contr_irrep):
                spin = {
                    1: 'A',
                    2: 'B'
                }[spin]
                if is_unrestricted:
                    MO_names.append(f'{idx}{symlab_exc[irrep_idx-1]}_{spin}')
                else:
                    MO_names.append(f'{idx}{symlab_exc[irrep_idx-1]}')

            ret[irrep][exctyp]['contributions'].append(contr)
            ret[irrep][exctyp]['from_MO'].append(MO_names[:ncontr])
            ret[irrep][exctyp]['to_MO'].append(MO_names[ncontr:])
            ret[irrep][exctyp]['from_MO_idx'].append(contr_idx[:ncontr])
            ret[irrep][exctyp]['to_MO_idx'].append(contr_idx[ncontr:])
            ret[irrep][exctyp]['from_MO_spin'].append(contr_spin[:ncontr])
            ret[irrep][exctyp]['to_MO_spin'].append(contr_spin[ncontr:])
            ret[irrep][exctyp]['from_MO_irrep'].append(contr_irrep[:ncontr])
            ret[irrep][exctyp]['to_MO_irrep'].append(contr_irrep[ncontr:])

    return ret


def _read_vibrations(path: str) -> result.NestedDict:
    reader = get_adf_reader(path)
    ret = result.NestedDict()

    # check if we have vibrations
    if ("Vibrations", "nNormalModes") not in reader:
        return ret

    ret.set('number_of_modes', reader.read("Vibrations", "nNormalModes"))
    ret.set('frequencies', ensure_list(reader.read("Vibrations", "Frequencies[cm-1]")))
    if ("Vibrations", "Intensities[km/mol]") in reader:
        ret.intensities = ensure_list(reader.read("Vibrations", "Intensities[km/mol]"))
    ret.set('number_of_imag_modes', len([freq for freq in ret['frequencies'] if freq < 0]))
    ret.set('character', "minimum" if ret['number_of_imag_modes'] == 0 else "transitionstate")
    ret.set('modes', [])
    for i in range(ret.get('number_of_modes')):
        ret.get('modes').append(reader.read("Vibrations", f"NoWeightNormalMode({i+1})"))
    return ret
