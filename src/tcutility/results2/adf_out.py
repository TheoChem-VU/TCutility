from tcutility.results2 import result, detect_filetype, ams_input_parser
from tcutility import cache, ensure_list, timer, constants
import numpy as np
from scm import plams
import os
from typing import List


@timer.timer
@cache.cache
def _get_adf_output(path: str) -> plams.KFReader:
    '''
    Get the KFReader associated with the path.
    This function is expected to be slow so we cache it.
    '''
    if detect_filetype.detect(path) == 'adf_out':
        with open(path) as file:
            lines = file.readlines()
        return lines


@timer.timer
def _read_jobid(path: str) -> str:
    for line in _get_adf_output(path):
        if 'AMS jobid  :' in line:
            return line.split(':')[1].strip()


def _get_output_input_matcher():
    with open('output_input_match') as file:
        lines = file.readlines()

    match = {}
    caster = {}
    for line in lines:
        match[line.split('=')[1].strip()] = line.split(':')[0].strip()
        c = eval(line.split(':')[1].split('=')[0].strip())
        if c is bool:
            c = lambda v: v == 'Yes'
        caster[line.split('=')[1].strip()] = c
    
    return match, caster


@timer.timer
def _read_settings(path: str) -> result.NestedDict:
    ret = result.NestedDict()
    ret['charge'] = 0
    ret['spin_polarization'] = 0
    ret['multiplicity'] = 1
    ret['relativistic'] = True
    ret['relativistic_type'] = 'scalar ZORA'
    for line in _get_adf_output(path):
        if 'Total System Charge' in line:
            ret['charge'] = float(line.split()[-1].strip())
            continue

        if '* SINGLE POINT CALCULATION *' in line:
            ret['task'] = 'SinglePoint'
            continue

        if '*  GEOMETRY OPTIMIZATION  *' in line:
            ret['task'] = 'GeometryOptimization'
            continue

        if 'Relativistic Corrections: ' in line:
            rel = line.split()[2]

            ret['relativistic_type'] = {
                '---': 'None',
                'scalar': 'scalar ZORA',
                'Spin-Orbit': 'spin-orbit ZORA',
                }[rel]
            if rel == '---':
                ret['relativistic'] = False

    return ret


def _get_block(path: str, start: str, end: str, skip_first=0, skip_last=0) -> List[str]:
    # get the index to start reading lines from
    inp_lines = _get_adf_output(path)
    for i, line in enumerate(inp_lines):
        if start in line:
            start_idx = i + 1 + skip_first
            break

    read = None
    lines = []
    for line in inp_lines[start_idx:]:
        if end in line:
            break
        lines.append(line.strip())

    if skip_last > 0:
        return lines[:-(skip_last+1)]
    return lines


def _get_line(path: str, part: str) -> str:
    return [line for line in _get_adf_output(path) if part in line]

@timer.timer
def _read_input(path: str) -> result.NestedDict:
    # get the ADF input
    input_lines = _get_block(path, 'ADF Engine Input', 'Title:', skip_first=1)
    ret = ams_input_parser._parse_input('\n'.join(input_lines), ['ams', 'engine ADF'])

    # read the AMS input
    match, caster = _get_output_input_matcher()
    for line in _get_adf_output(path):
        for inpt, outp in match.items():
            if inpt not in line:
                continue

            try:
                value = caster[inpt](line.split(inpt)[1].strip())
                ret.set(*outp.split('.'), value)
            except ValueError:
                pass

    # read the system block
    atom_lines = _get_block(path, 'Atoms', 'Total System Charge')
    atom_lines = ["    ".join(line.strip().split()[1:]) for line in atom_lines]
    ret.set('system', 'atoms', atom_lines)

    # read the task
    for line in _get_adf_output(path):
        if '* SINGLE POINT CALCULATION *' in line:
            ret['task'] = 'SinglePoint'
            break

        if '*  GEOMETRY OPTIMIZATION  *' in line:
            ret['task'] = 'GeometryOptimization'
            break

    return ret


@timer.timer
def _read_properties(path: str) -> result.NestedDict:
    ret = result.NestedDict()

    # read the energies
    lines = _get_line(path, 'Total Bonding Energy:')
    value = float(lines[0].split(':')[1].split()[0]) * constants.HA2KCALMOL
    ret.set('energy', 'bond', value)

    lines = _get_line(path, 'Electrostatic Energy:')
    value = float(lines[0].split(':')[1].split()[0]) * constants.HA2KCALMOL
    ret.set('energy', 'elstat', 'total', value)

    lines = _get_line(path, 'Pauli Repulsion (Delta E^Pauli):')
    value = float(lines[0].split(':')[1].split()[0]) * constants.HA2KCALMOL
    ret.set('energy', 'pauli', 'total', value)

    lines = _get_line(path, 'Total Steric Interaction:')
    value = float(lines[0].split(':')[1].split()[0]) * constants.HA2KCALMOL
    ret.set('energy', 'steric', value)

    lines = _get_line(path, 'Dispersion Energy:')
    if len(lines) > 0:
        value = float(lines[0].split(':')[1].split()[0]) * constants.HA2KCALMOL
        ret.set('energy', 'dispersion', value)
    else:
        ret.set('energy', 'dispersion', 0.0)

    lines = _get_block(path, 'Orbital Interactions\n', '--------------------')
    value = float(lines[0].split(':')[1].split()[0]) * constants.HA2KCALMOL
    value = {line.split()[0][:-1]: float(line.split(':')[1].split()[0]) * constants.HA2KCALMOL for line in lines}
    orbint_sum = sum(value.values())
    ret.set('energy', 'orbint', value)

    lines = _get_line(path, 'Total Orbital Interactions:')
    value = float(lines[0].split(':')[1].split()[0]) * constants.HA2KCALMOL
    ret.set('energy', 'orbint', 'total', value)
    ret.set('energy', 'orbint', 'correction', ret['energy']['orbint']['total'] - orbint_sum)

    return ret
