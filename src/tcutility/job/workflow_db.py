import os
# import fcntl
import platformdirs


DBPATH = platformdirs.user_cache_dir(appname="TCutility", appauthor="TheoCheMVU", ensure_exists=True) + '/.workflow.txt'
if not os.path.exists(DBPATH):
    with open(DBPATH, 'w+'):
        ...


def db_readlines():
    with open(DBPATH) as db:
        # fcntl.flock(db.fileno(), fcntl.LOCK_EX)
        lines = db.readlines()
        # fcntl.flock(db.fileno(), fcntl.LOCK_UN)
    return lines


def delete_data(hsh):
    '''
    Get the status of a workflow with specific args and kwargs.
    '''
    with open(DBPATH) as db:
        # fcntl.flock(db.fileno(), fcntl.LOCK_EX)
        lines = db.readlines()
    with open(DBPATH, 'w+') as db:
        for line in lines:
            if line.startswith(hsh):
                continue
            db.write(line)


def get_data(hsh):
    '''
    Get the status of a workflow with specific args and kwargs.
    '''
    lines = db_readlines()
    data = {}
    for line in lines:
        parts = line.split(',')
        _hsh, status = parts[0], parts[1]

        if _hsh != hsh:
            continue

        data['status'] = status.strip()
        for part in parts[2:]:
            k, v = part.split('=')
            data[k.strip()] = v.strip('\n')

    return data


def get_status(hsh):
    '''
    Get the status of a workflow with specific args and kwargs.
    '''
    return get_data(hsh).get('status', 'UNKNOWN')


def can_skip(hsh):
    '''
    Checks if a workflow with specific args and kwargs has finished.
    '''
    status = get_status(hsh)
    if status in ['SUCCESS', 'FAILED']:
        return True
    elif status == 'RUNNING':
        data = get_data(hsh)

    return False


def set_status(hsh, status, **kwargs):
    '''
    Checks if a workflow with specific args and kwargs has finished.
    '''
    s = f'{hsh}, {status}'
    for k, v in kwargs.items():
        s += f', {k}={v}'

    with open(DBPATH, 'a') as db:
        # fcntl.flock(db.fileno(), fcntl.LOCK_EX)
        db.write(f'{s}\n')
        # fcntl.flock(db.fileno(), fcntl.LOCK_UN)


def set_running(hsh, **kwargs):
    '''
    Checks if a workflow with specific args and kwargs has finished.
    '''
    set_status(hsh, 'RUNNING', **kwargs)


def set_finished(hsh, **kwargs):
    '''
    Checks if a workflow with specific args and kwargs has finished.
    '''
    set_status(hsh, 'SUCCESS', **kwargs)


def set_failed(hsh, **kwargs):
    '''
    Checks if a workflow with specific args and kwargs has finished.
    '''
    set_status(hsh, 'FAILED', **kwargs)