from tcutility.results import cache, Result
from tcutility import ensure_list, constants


def get_calc_settings(info: Result) -> Result:
    """
    Function to read useful calculation settings from kf reader
    """

    assert info.engine == "dftb", f"This function reads DFTB data, not {info.engine} data"

    if info.input.task == 'PESScan':
        return Result()

    assert "dftb.rkf" in info.files, f'Missing dftb.rkf file, [{", ".join([": ".join(item) for item in info.files.items()])}]'

    ret = Result()

    # set the calculation task at a higher level
    ret.task = info.input.task

    return ret


def get_properties(info: Result) -> Result:
    """Function to get properties from an DFTB calculation.

    Args:
        info: Result object containing DFTB properties.

    Returns:
        :Result object containing properties from the DFTB calculation:

            - **energy.bond (float)** – bonding energy (|kcal/mol|).
    """

    assert info.engine == "dftb", f"This function reads DFTB data, not {info.engine} data"

    if info.input.task == 'PESScan':
        return Result()

    assert "dftb.rkf" in info.files, f'Missing dftb.rkf file, [{", ".join([": ".join(item) for item in info.files.items()])}]'

    reader_dftb = cache.get(info.files["dftb.rkf"])
    ret = Result()

    # properties are not given as in ADF. Instead you must first know which index each key is at. For example we might have:
    # (Properties, SubType(k)) == Coulomb
    # therefore, to get the Coulomb energy we first have to know the index k
    # we therefore first loop through every subtype entry and store the substypes in order in a list
    # we also store the main type (e.g. 'Energy', 'Gradient', ...) and the value
    number_of_properties = reader_dftb.read("Properties", "nEntries")
    subtypes = []
    types = []
    values = []
    for i in range(1, number_of_properties + 1):
        subtypes.append(reader_dftb.read("Properties", f"Subtype({i})").strip())
        types.append(reader_dftb.read("Properties", f"Type({i})").strip())
        if types[-1] == 'Energy':
            values.append(reader_dftb.read("Properties", f"Value({i})") * constants.HA2KCALMOL)
        else:
            values.append(reader_dftb.read("Properties", f"Value({i})"))

    # then simply add the properties to ret
    for typ, subtyp, value in zip(types, subtypes, values):
        ret[typ.replace(" ", "_")][subtyp] = value

    if ret.energy['DFTB Final Energy']:
        ret.energy.bond = ret.energy['DFTB Final Energy'] * constants.HA2KCALMOL

    # we also read vibrations
    if ('Vibrations', 'nNormalModes') in reader_dftb:
        ret.vibrations.number_of_modes = reader_dftb.read("Vibrations", "nNormalModes")
        ret.vibrations.frequencies = ensure_list(reader_dftb.read("Vibrations", "Frequencies[cm-1]"))
        if ("Vibrations", "Intensities[km/mol]") in reader_dftb:
            ret.vibrations.intensities = ensure_list(reader_dftb.read("Vibrations", "Intensities[km/mol]"))
        ret.vibrations.number_of_imag_modes = len([freq for freq in ret.vibrations.frequencies if freq < 0])
        ret.vibrations.character = "minimum" if ret.vibrations.number_of_imag_modes == 0 else "transitionstate"
        ret.vibrations.modes = []
        for i in range(ret.vibrations.number_of_modes):
            ret.vibrations.modes.append(reader_dftb.read("Vibrations", f"NoWeightNormalMode({i+1})"))

    if ("Thermodynamics", "Gibbs free Energy") in reader_adf:
        ret.energy.gibbs = reader_adf.read("Thermodynamics", "Gibbs free Energy") * constants.HA2KCALMOL
        ret.energy.enthalpy = reader_adf.read("Thermodynamics", "Enthalpy") * constants.HA2KCALMOL
        ret.energy.nuclear_internal = reader_adf.read("Thermodynamics", "Internal Energy total") * constants.HA2KCALMOL

    return ret
