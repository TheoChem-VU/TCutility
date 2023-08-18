"""This module provides info about calculations done using AMS based on rkf files. 
This includes information about the engine used (ADF, DFTB, BAND, ...), general calculation settings such as relativistic corrections, symmetries, status of the calculations, ...
This information are then used in further analysis programs.
"""

import numpy as np
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
        if os.path.split(root)[1].endswith('.results') and len(os.path.split(root)[1].split('.')) > 2:
            continue
        if os.path.split(root)[1].startswith('tmp.'):
            continue
        files.extend([j(root, file) for file in files_])

    # parse the filenames
    # first parse the rkf files. This will tell us how many fragments there are in the calculation. There should be only two rkf files for a normal calculation
    # there are therefore n_file_ending_in_rkf - 2 fragments
    ret = {}
    for file in files:
        # rkf files are either called /{program}.rkf, or /{name}.{program}.rkf, so we must parse them in a special way
        if file.endswith('.rkf'):
            f = os.path.split(file)[1]
            parts = f.split('.')
            f = f'{parts[-2]}.rkf'
            ret[f] = os.path.abspath(file)

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
    ret.files.root = os.path.abspath(calc_dir)

    reader_ams = plams.KFReader(ret.files['ams.rkf'])

    # store information about the version of AMS
    ret.ams_version.string = reader_ams.read('General', 'release')
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
        Tuple containing (success, reasons), where success indicates whether the calculation has successfully finished.
        If it is not finished, reasons will contain the reasons that the calculation is not finished.
    '''
    files = get_calc_files(calc_dir)
    reader_ams = plams.KFReader(files['ams.rkf'])

    ret = dictfunc.DotDict()
    ret.success = False
    ret.name = None
    ret.code = None
    ret.reasons = []

    termination_status = reader_ams.read('General', 'termination status').strip()

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

    if termination_status in ('NORMAL TERMINATION with warnings', 'NORMAL TERMINATION with errors'):
        if termination_status == 'NORMAL TERMINATION with warnings':
            ret.success = True
            ret.name = 'SUCCESS(W)'
            ret.code = 'W'
        else:
            ret.name = 'FAILED'
            ret.code = 'F'

        with open(files['log']) as logfile:
            for line in logfile.readlines():
                line_ = line.strip()[25:]
                if line_.startswith('ERROR:') or line_.startswith('WARNING: '):
                    ret.reasons.append(line_)
        return ret

    ret.reasons.append(termination_status)
    ret.success = False
    ret.name = 'UNKNOWN'
    ret.code = 'U'
    return ret

