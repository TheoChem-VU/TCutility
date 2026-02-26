from pprint import pprint
from typing import List

import click

from tcutility import workflow_db, log
from tcutility.job.workflow import WorkFlowOutput
import os


@click.group("workflow")
def workflow():
    pass

@click.command("status")
@click.option("-h", "--hash", "use_hash", is_flag=True)
@click.argument("name")
def status(use_hash: bool = False, name: str = None):
    if use_hash:
        print(workflow_db.get_status(name))
        return

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

            if name is None:
                rows.append((status, workflow_name, hsh))
            else:
                rows.append((status, hsh))

    if len(rows) == 0:
        if name is None:
            print(f'I could not find any workflow runs.')
        else:
            print(f'I could not find any runs for WorkFlow({name}).')
        return

    if name is None:
        print(f'Found {sum(list(status_counts.values()))} total run(s).')
        print()
        print(f' From the following workflows:')
        for workflow_name, nums in workflow_name_counts.items():
            print(f'  {nums:>5} {workflow_name}')

    else:
        print(f'Found {sum(list(status_counts.values()))} total run(s) for WorkFlow({name}):')

    print()
    print(f' With the following statuses:')
    for status, nums in status_counts.items():
        print(f'  {nums:>5} {status}')

    print()
    if name is None:
        log.table(rows, header=('Status', 'Workflow', 'Hash'))
    else:
        log.table(rows, header=('Status', 'Hash'))

workflow.add_command(status)


@click.command("clear")
@click.option("-h", "--hash", "use_hash", is_flag=True)
@click.argument("name")
def clear(use_hash: bool = False, name: str = None):
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
    else:
        print('Cancelling ...')


workflow.add_command(clear)


@click.command("where")
def where():
    print(f'CACHEDIR: {workflow_db.CACHEDIR}')
    print(f'DBPATH:   {workflow_db.DBPATH}')

workflow.add_command(where)
