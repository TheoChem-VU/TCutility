'''
Module used for obtaining information about exchange-correlation functionals.
For example, it can be useful to obtain 
'''
import os
from tcutility import results, cache
import re


j = os.path.join


@cache.cache
def get(functional_name: str) -> results.Result:
    '''
    Return information about a given functional.

    Args:
        functional_name: the name of the functional. It should exist in the :func:`get_available_functionals` keys.

    Return:
        A :class:`Result <tcutility.results.result.Result>` object containing information about the functional if it exists. Else it will return ``None``.
    
    .. seealso::
        :func:`get_available_functionals` for an overview of the information returned.
    '''
    info = functionals.get(functional_name, None)
    if info is None:
        info = functionals.get(functional_name_from_path_safe_name(functional_name), None)

    if info is None:
        raise KeyError(f'Could not find info for functional {functional_name}.')

    return info


def functional_name_from_path_safe_name(path_safe_name: str) -> results.Result:
    '''
    Return information about a given functional given its path-safe name.
    This can be useful when you want to know the functional from a path name.

    Return:
        A :class:`Result <tcutility.results.result.Result>` object containing information about the functional if it exists. Else it will return ``None``.
    
    .. seealso::
        :func:`get_available_functionals` for an overview of the information returned.
    '''
    for functional, functional_info in functionals.items():
        if path_safe_name.lower() == functional_info.path_safe_name.lower():
            return functional
        elif path_safe_name.replace('-', '').lower() == functional_info.path_safe_name.replace('-', '').lower():
            return functional



def get_available_functionals():
    '''
    Function that returns a dictionary of all available XC-functionals.

    Returns:
        : A :class:`Result <tcutility.results.result.Result>` object containing information about all available XC-functionals.
            The functional names are stored as the keys and the functional information is stored as the values.
            The values contain the following information:

                - ``name`` **(str)** - the name of the functional.
                - ``path_safe_name`` **(str)** - the name of the functional made suitable for file paths. 
                    This name is the same as the normal name, but without parentheses. Asterisks are replaced with lower-case ``s``.
                - ``name_no_disp`` **(str)** - the name of functional without the dispersion correction.
                - ``category`` **(str)** - the category the functional belongs to.
                - ``dispersion`` **(str)** - the dispersion correction part of the functional name.
                - ``dispersion_name`` **(str)** - the name of the dispersion correction as it would be written in ADF.
                - ``includes_disp`` **(bool)** - whether the functional already includes a dispersion correction.
                - ``use_libxc`` **(bool)** - whether the functional is from the LibXC library.
                - ``available_in_adf`` **(bool)** - whether the functional is available in ADF.
                - ``available_in_band`` **(bool)** - whether the functional is available in BAND.
                - ``available_in_orca`` **(bool)** - whether the functional is available in ORCA.
                - ``adf_settings`` **(:class:`Result <tcutility.results.result.Result>`)** - the settings that are used to select the functional in the ADF input.
                - ``name_latex`` **(str)** - the name of the functional formatted to be used with LaTeX renderers.
                - ``name_html`` **(str)** - the name of the functional formatted to be used with HTML renderers.
                - ``dois`` **(List[str])** - a list of relevant dois for this functional.
    '''
    def set_dispersion(func):
        disp_map = {
            '-D4': 'GRIMME4',
            '-D3(BJ)': 'GRIMME3 BJDAMP',
            '-D3BJ': 'GRIMME3 BJDAMP',
            '-D3': 'GRIMME3',
            '-dDsC': 'dDsC',
            '-dUFF': 'UFF',
            '-MBD': 'MBD',
            '-MBD@rsSC': 'MBD',
            '-D': 'DEFAULT'
        }

        # set some default values for useful parameters
        func.name_no_disp = func.name
        func.dispersion = None
        func.dispersion_name = None

        # go through every dispersion correction and check if we are using it
        for disp_suffix, disp_name in disp_map.items():
            if func.name.endswith(disp_suffix):
                # dispersion will be the suffix without the -
                func.dispersion = disp_suffix[1:]
                func.dispersion_name = disp_name

                # check if the functional already includes the dispersion correction
                if func.includes_disp:
                    break

                # else we set the name of the functional without dispersion for later
                func.name_no_disp = func.name[:-len(disp_suffix)]
                # get the dispersion settings for ADF. Try to get custom values if they were provided.
                func.adf_settings.XC.Dispersion = func.disp_params or disp_name
                break

    def set_functional(func):
        # set the functional settings for ADF
        # first go through some special functionals that require special settings
        if func.name_no_disp == 'BMK':
            func.adf_settings.XC.LibXC = 'HYB_MGGA_X_BMK GGA_C_BMK'
            return

        if func.name in ['LCY-BLYP', 'LCY-BP86', 'LCY-PBE']:
            func.adf_settings.XC.GGA = func.name.split('-')[1]
            func.adf_settings.XC.RANGESEP = ''
            func.adf_settings.XC.xcfun = ''
            return

        if func.name in ['CAMY-B3LYP']:
            func.adf_settings.XC.Hybrid = 'CAMY-B3LYP'
            func.adf_settings.XC.RANGESEP = ''
            func.adf_settings.XC.xcfun = ''
            return

        if func.name == 'GGA:SSB-D':
            func.adf_settings.XC.GGA = 'SSB-D'
            return

        if func.name == 'MetaGGA:SSB-D':
            func.adf_settings.XC.MetaGGA = 'SSB-D'
            return

        if func.name_no_disp == 'HartreeFock':
            func.adf_settings.XC.HartreeFock = ''
            return

        if func.name == 'MP2':
            func.adf_settings.XC.MP2 = ''
            return

        if func.name in ['SOS-MP2', 'SCS-MP2']:
            func.adf_settings.XC.MP2 = ''
            func.adf_settings.XC.EmpiricalScaling = func.name[:-4]
            return

        # the normal functionals are defined based on their category, or selected from libxc
        if func.use_libxc:
            func.adf_settings.XC.LibXC = func.name_no_disp
        else:
            func.adf_settings.XC[func.category] = func.name_no_disp

    # gather all data about available functionals
    functionals = results.Result()  # store all info in this dict

    with open(j(os.path.split(__file__)[0], 'available_functionals.txt')) as file:
        lines = file.readlines()

    # read the references first
    # references are given as 
    # [refname] doi
    # and in-line
    # - xcname {options} [refname1][refname2]...
    dois = {}
    for line in lines:
        if not line.startswith('['):
            continue

        line = line.split('#')[0].strip()

        ref, doi = line.strip().split()
        ref = ref[1:-1]
        dois[ref] = doi

    for line in lines:
        # there can be empty lines
        if not line.strip():
            continue

        # and comment lines
        if line.startswith('#'):
            continue

        # we don't read the references here
        if line.startswith('['):
            continue

        # functional names are given starting with -
        # category names without -
        if not line.startswith('- '):
            curr_category = line.strip()
            continue

        line = line.split('#')[0].strip()

        # store data about the func in a dict
        func = results.Result()
        func.category = curr_category
        # separate the functional name from the line
        functional_name = line[2:].split('!')[0].split(',')[0].split('[')[0].strip()
        func.name = functional_name
        func.name_latex = functional_name
        func.name_html = functional_name
        func.path_safe_name = functional_name.replace(')', '').replace('(', '').replace('*', 's').replace(' ', '-')

        if functional_name.startswith('WB'):
            func.name_latex = func.name_latex.replace('WB', r'$\omega$B')
            func.name_html = func.name_html.replace('WB', '&omega;B')

        if 'r2SCAN' in functional_name:
            func.name_latex = func.name_latex.replace('r2SCAN', r'r$^2$SCAN')
            func.name_html = func.name_html.replace('r2SCAN', 'r<sup>2</sup>SCAN')

        if 'and' in functional_name:
            func.name_latex = func.name_latex.replace('and', '&')
            func.name_html = func.name_html.replace('and', '&amp;')

        if '*' in functional_name:
            func.name_latex = func.name_latex.replace('*', r'$^*$')
            func.name_html = func.name_html.replace('*', '<sup>*</sup>')

        if 'B2PIPLYP' in functional_name:
            func.name_latex = func.name_latex.replace('B2PIPLYP', r'B2$\pi$PLYP')
            func.name_html = func.name_html.replace('B2PIPLYP', 'B2&pi;PLYP')

        # check if custom params were given for dispersion
        if 'GRIMME' in line:
            func.disp_params = line.split('!')[0].split(',')[1].strip().strip("'")

        func.use_libxc = '!libxc' in line
        func.includes_disp = '!includesdisp' in line
        func.available_in_adf = '!noadf' not in line
        func.available_in_band = '!band' in line
        func.available_in_orca = '!orca' in line

        # get references
        refs = re.findall(r'\[([a-zA-Z0-9]+)\]', line)
        func.dois = [dois[ref] for ref in refs]

        set_dispersion(func)
        set_functional(func)

        functionals[functional_name] = func

    return functionals

functionals = get_available_functionals()

categories = []
for functional in functionals:
    if get(functional).category not in categories:
        categories.append(get(functional).category)
