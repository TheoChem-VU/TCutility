"""This module provides basic and general information about calculations done using AMS given a calculation directory. This includes information about the engine used (ADF, DFTB, BAND, ...), general information such as timings, files, status of the calculation, ... This information is used in further analysis programs.
"""

from yutility import dictfunc
from scm import plams
import os

j = os.path.join


def get_calc_files(calc_dir: str) -> dict:
    '''Function that returns files relevant to AMS calculations stored in calc_dir.

    Args:
        calc_dir: path pointing to the desired calculation

    Returns:
        Dictionary containing filenames and paths
    '''
    # collect all files in the current directory and subdirectories
    files = []
    for root, _, files_ in os.walk(calc_dir):
        # some results are stored in dirs called {name}.results, if the calculations uses fragments there will be additional dirs called
        # {name}.{fragname}.results, which do not contain new information as the required info is copied over to {name}.results. Therefore
        # we should skip the fragment directories 
        if os.path.split(root)[1].endswith('.results') and len(os.path.split(root)[1].split('.')) > 2:
            continue

        # if a calculation is running or did not finish correctly there might be tmp. dirs, which should be ignored
        if os.path.split(root)[1].startswith('tmp.'):
            continue

        # the rest can all be stored
        files.extend([j(root, file) for file in files_])

    # parse the filenames
    ret = {}
    ret['root'] = os.path.abspath(calc_dir)
    for file in files:
        # rkf files are either called /{program}.rkf, or /{name}.{program}.rkf, so we must parse them in a special way
        if file.endswith('.rkf'):
            f = os.path.split(file)[1]
            parts = f.split('.')
            f = f'{parts[-2]}.rkf'
            ret[f] = os.path.abspath(file)

        # logfiles are generally called either {name}.log or {name}.logfile
        if file.endswith('.logfile') or file.endswith('.log') or file.endswith('.err'):
            f = os.path.split(file)[1]
            parts = f.split('.')
            f = '.'.join(parts[1:]).replace('logfile', 'log')
            ret[f] = os.path.abspath(file)

    return ret


def get_calc_info(calc_dir: str) -> dictfunc.DotDict:
    '''Function to read useful info about the calculation in calc_dir.
    Returned information will depend on the type of file that is provided

    Args:
        calc_dir: path pointing to the desired calculation

    Returns:
        Dictionary containing information about the calculation
    '''
    ret = dictfunc.DotDict()
    ret.files = get_calc_files(calc_dir)

    reader_ams = plams.KFReader(ret.files['ams.rkf'])

    # store information about the version of AMS
    ret.ams_version.string = reader_ams.read('General', 'release')

    # decompose the version string
    ret.ams_version.major = ret.ams_version.string.split('.')[0]
    ret.ams_version.minor = ret.ams_version.string.split()[0].split('.')[1]
    ret.ams_version.micro = ret.ams_version.string.split()[1]
    ret.ams_version.date = ret.ams_version.string.split()[-1][1:-1]

    # check what the program is first. The program can be either AMS or one of the engines (ADF, DFTB, ...)
    if ('General', 'engine') in reader_ams:
        ret.engine = reader_ams.read('General', 'engine').strip().lower()
    # if program cannot be read from reader it is probably an old version of ADF, so we should default to ADF
    else:
        ret.engine = 'adf'

    # store the job id, which should be unique for the job
    ret.job_id = reader_ams.read('General', 'jobid') if ('General', 'jobid') in reader_ams else None

    # store the computation timings, only available in ams.rkf
    ret.timing.cpu = reader_ams.read('General', 'CPUTime') if ('General', 'CPUTime') in reader_ams else None
    ret.timing.sys = reader_ams.read('General', 'SysTime') if ('General', 'SysTime') in reader_ams else None
    ret.timing.total = reader_ams.read('General', 'ElapsedTime') if ('General', 'ElapsedTime') in reader_ams else None

    # store the calculation status
    ret.status = calculation_status(calc_dir)

    # check if this was a multijob
    ret.is_multijob = False
    if len([file for file in ret.files if file.endswith('.rkf')]) > 2:
        ret.is_multijob = True

    return ret


def calculation_status(calc_dir: str) -> dictfunc.DotDict:
    '''Function that returns the status of the calculation described in reader. 
    In case of non-succes it will also give possible reasons for the errors/warnings.

    Args:
        reader: plams.KFReader or plams.KFFile object pointing to the desired calculation

    Returns:
        Dictionary containing information about the calculation status
        success: bool - True if calculation reported normal termination, with or without warnings, False otherwise
        reasons: list[str] - list of reasons to explain the status, they can be errors, warnings, etc.
        name: str - calculation status written as a string, ex. "RUNNING", "FAILED", etc.
        code: str - calculation status written as a single character, ex. "S", "F", etc.
    '''
    files = get_calc_files(calc_dir)

    # termination info is stored in ams.rkf
    reader_ams = plams.KFReader(files['ams.rkf'])

    ret = dictfunc.DotDict()
    ret.success = False
    ret.name = None
    ret.code = None
    ret.reasons = []

    termination_status = reader_ams.read('General', 'termination status').strip()

    # parse the logfile to find errors and warnings
    if 'log' in files:
        with open(files['log']) as logfile:
            for line in logfile.readlines():
                # the first 25 characters include the timestamp and two spaces
                line_ = line.strip()[25:]
                # errors and warnings have a predictable format
                if line_.startswith('ERROR:') or line_.startswith('WARNING: '):
                    ret.reasons.append(line_)

    if termination_status == 'NORMAL TERMINATION':
        ret.success = True
        ret.name = 'SUCCESS'
        ret.code = 'S'
        return ret

    if termination_status == 'IN PROGRESS':
        ret.reasons.append('Calculation in progress')
        ret.name = 'RUNNING'
        ret.code = 'R'
        return ret

    if termination_status == 'UNKNOWN':
        ret.reasons.append('Calculation status unknown')
        ret.name = 'UNKNOWN'
        ret.code = 'U'
        return ret

    if termination_status == 'NORMAL TERMINATION with warnings':
        ret.success = True
        ret.name = 'SUCCESS(W)'
        ret.code = 'W'
        return ret

    if termination_status == 'NORMAL TERMINATION with warnings':
        ret.name = 'FAILED'
        ret.code = 'F'
        return ret

    # if we have not exited the function yet we do not know what the status is
    # probably means that there was a parsing error in ams, which will be placed in termination status
    ret.reasons.append(termination_status)
    ret.success = False
    ret.name = 'UNKNOWN'
    ret.code = 'U'
    return ret
