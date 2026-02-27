from pprint import pprint
from typing import List

import click

from tcutility import workflow_db, log
from tcutility.job.workflow import WorkFlowOutput
import time
import datetime

LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K'


def clear_lines(n):
    for _ in range(n):
        print(LINE_UP, end=LINE_CLEAR)



@click.group("workflow")
def workflow():
    '''
    The ``tcutility workflow`` subcommand gives a few tools for reading the statuses of, and clearing of past workflow runs.
    '''
    pass

@click.command("status")
@click.option("-h", "--hash", "use_hash", is_flag=True)
@click.argument("name", required=False)
def status(use_hash: bool = False, name: str = None):
    '''
    Read the statuses of completed and currently running workflow runs.
    Use the ``name`` argument to specify a specific workflow type or a specific hash when the ``-h/--hash`` flag is turned on.
    If ``name`` is not given, prints the statuses of all workflow runs and provides an overview of the number of runs per workflow.
    '''

    def get_str():
        s = ''
        if use_hash:
            s += workflow_db.get_status(name) + '\n'
        else:
            log.print_date = False
            rows = []
            status_counts = {}
            workflow_name_counts = {}
            for hsh, data in workflow_db.read_all().items():
                if name is None or data.get('workflow_name', None) == name:
                    status = data.get('status', 'UNKOWN')
                    status_counts.setdefault(status, 0)
                    status_counts[status] += 1

                    workflow_name = data.get('workflow_name', '')
                    workflow_name_counts.setdefault(workflow_name, 0)
                    workflow_name_counts[workflow_name] += 1

                    start_time = data.get('start_time', None)
                    if start_time is not None and status == 'RUNNING':
                        t = datetime.datetime.strptime(start_time, '%Y-%m-%d-%H-%M-%S')
                        td = datetime.datetime.now() - t
                        run_time = ''
                        if td >= datetime.timedelta(days=1):
                            run_time += f'{td.days}-'
                        if td >= datetime.timedelta(hours=1):
                            run_time += f'{td.hours}:'
                        run_time += f'{td.seconds//60}:{td.seconds%60:02}'

                    else:
                        run_time = ''

                    if name is None:
                        rows.append((status, workflow_name, data.get('slurm_job_id', ''), hsh, run_time, data.get('stage', '')))
                    else:
                        rows.append((status, data.get('slurm_job_id', ''), hsh, run_time, data.get('stage', '')))

            if len(rows) == 0:
                if name is None:
                    print(f'I could not find any workflow runs.')
                else:
                    print(f'I could not find any runs for WorkFlow({name}).')
                return

            if name is None:
                s += f'Found {sum(list(status_counts.values()))} total run(s).' + '\n\n'
                s += f' From the following workflows:' + '\n'
                for workflow_name, nums in workflow_name_counts.items():
                    s += f'  {nums:>5} {workflow_name}\n'

            else:
                s += f'Found {sum(list(status_counts.values()))} total run(s) for WorkFlow({name}):\n\n'

            s += f' With the following statuses:\n'
            for status, nums in status_counts.items():
                s += f'  {nums:>5} {status}\n'

            s += '\n' 
            if name is None:
                s += log.table(rows, header=('Status', 'Workflow', 'SlurmJobID', 'Hash', 'RunTime', 'Stage'), as_str=True)
            else:
                s += log.table(rows, header=('Status', 'SlurmJobID', 'Hash', 'RunTime', 'Stage'), as_str=True)

        return s + '\n'

    s = get_str()
    print(s)
    while True:
        s = get_str()
        n_lines = len(s.splitlines())
        clear_lines(n_lines+1)
        print(s)
        time.sleep(1)

workflow.add_command(status)


@click.command("clear")
@click.option("-h", "--hash", "use_hash", is_flag=True)
@click.argument("name", required=True)
def clear(use_hash: bool = False, name: str = None):
    '''
    Clears data related to workflow runs.
    Use the ``name`` argument to specify a specific workflow type or a specific hash when the ``-h/--hash`` flag is turned on.
    '''
    if use_hash:
        workflow_db.delete(name)
        return

    hashes = []
    for hsh, data in workflow_db.read_all().items():
        if data.get('workflow_name', None) == name:
            hashes.append(hsh)

    if len(hashes) == 0:
        print(f'I could not find any runs for WorkFlow({name}).')
        return

    proceed = input(f'This will delete {len(hashes)} workflow runs; proceed? (y/[n]): ')
    if proceed == 'y':
        for hsh in hashes:
            workflow_db.delete(hsh)
        print()
    else:
        print('Cancelling ...')


workflow.add_command(clear)


@click.command("where")
def where():
    '''
    Prints where workflow data is stored.
    '''
    print(f'CACHEDIR: {workflow_db.CACHEDIR}')
    print(f'DBPATH:   {workflow_db.DBPATH}')

workflow.add_command(where)
