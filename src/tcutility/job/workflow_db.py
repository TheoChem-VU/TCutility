import os
import platformdirs
from typing import List, Tuple, Dict
import tcutility

# CACHEDIR = 
DBPATH = platformdirs.user_cache_dir(appname="TCutility", appauthor="TheoCheMVU", ensure_exists=True) + '/workflows.csv'
# DBPATH = 'test.csv'
# create a new db file if it doesnt exist yet
if not os.path.exists(DBPATH):
    with open(DBPATH, 'w+'):
        ...

#### BASIC FUNCTIONS

def write(hsh: str, **kwargs):
    s = f'{hsh}'
    for k, v in kwargs.items():
        s += f', {k}={v}'
    s += '\n'

    with open(DBPATH, 'a') as db:
        db.write(s)

def read(hsh: str) -> dict:
    '''
    Get the status of a workflow with specific args and kwargs.
    '''
    # default status is unknown
    for _hsh, data in read_all().items():
        if hsh == _hsh:
            return data
    return {}


def parse_line(line: str) -> Tuple[str, dict]:
    '''
    Read information from a line from the database.
    '''
    # the hsh is always the first entry
    hsh = line.split(',')[0]
    data = {}
    # read anything after the hash
    for part in line.split(',')[1:]:
        k, v = part.split('=')
        data[k.strip()] = v.strip('')

    # return the hash and data separately
    return hsh, data


def read_all() -> Dict[str, dict]:
    '''
    Return all lines that are in the database.
    '''
    with open(DBPATH) as db:
        lines = db.readlines()

    # parse the lines we found
    parsed_lines = [parse_line(line) for line in lines]
    # and construct a dictionary
    return {hsh: data for hsh, data in parsed_lines}


def update(hsh: str, **kwargs) -> None:
    '''
    Update a record in the database associated with the given hash.
    '''
    data = read(hsh)
    data.update(kwargs)
    delete(hsh)
    write(hsh, **data)


def delete(hsh: str) -> None:
    '''
    Delete records related to the given hash.
    '''
    # make a list of lines that we will rewrite
    # all_data = read_all()
    # all_data.pop(hsh, None)
    # for _hsh, data in all_data.items():
    #     write(_hsh, data)
    with open(DBPATH) as db:
        lines = db.readlines()

    new_lines = [line for line in lines if line.split(',')[0] != hsh]
    with open(DBPATH, 'w+') as db:
        for line in new_lines:
            db.write(line)


# #### CONVENIENCE FUNCTIONS


def get_status(hsh: str) -> str:
    '''
    Get the status of a workflow with specific args and kwargs.
    '''
    return read(hsh).get('status', None)


def get_workflow_name(hsh: str) -> str:
    '''
    Get the status of a workflow with specific args and kwargs.
    '''
    return read(hsh).get('workflow_name', None)


def can_skip(hsh: str, server: tcutility.connect.Server = tcutility.connect.Local()) -> bool:
    '''
    Checks if a workflow with specific args and kwargs has finished.
    '''
    status = get_status(hsh)
    # if the status indicates the workflow already ran we can skip
    if status in ['SUCCESS', 'FAILED']:
        return True

    # if the workflow is still running we need to check if it
    # is being managed by slurm
    elif status == 'RUNNING':
        data = read(hsh)
        # if the workflow is managed by slurm it should have a slurm-job-id
        slurm_job_id = data.get('slurm_job_id', None)
        # if it does not we can assume it failed
        if slurm_job_id is None:
             return False

        # if it does, we need to check if it is in the queue
        sq = tcutility.slurm.squeue(server=server)
        # if it is being managed by slurm we can skip it
        # otherwise something went wrong and the status was not updated
        return slurm_job_id in sq['id']

    return False


def set_status(hsh: str, new_status: str) -> None:
    '''
    Checks if a workflow with specific args and kwargs has finished.
    '''
    update(hsh, status=new_status)


def set_running(hsh: str) -> None:
    '''
    Checks if a workflow with specific args and kwargs has finished.
    '''
    update(hsh, status='RUNNING')


def set_finished(hsh: str) -> None:
    '''
    Checks if a workflow with specific args and kwargs has finished.
    '''
    update(hsh, status='SUCCESS')


def set_failed(hsh: str) -> None:
    '''
    Checks if a workflow with specific args and kwargs has finished.
    '''
    update(hsh, status='FAILED')
