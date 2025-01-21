from pprint import pprint
from typing import List

import click
from tcutility import results


@click.command()
@click.option("-s", "--status", is_flag=True, help="Shortcut to only print the status of the calculation.")
@click.option("-p", "--properties", is_flag=True, help="Shortcut to only print calculated properties for the calculation.")
@click.argument("workdir")
@click.argument("keys", nargs=-1)
def read_results(status: bool, properties: bool, workdir: str, keys: List[str]):
    """Read results from a calculation."""
    res = results.read(workdir)

    if status:
        print(res.status.name)  # type: ignore # status is a str
        return

    if properties:
        pprint(res.properties)
        return

    if len(keys) > 0:
        ret = {k: res.get_multi_key(k) for k in keys}
        if len(ret) == 1:
            print(list(ret.values())[0])
            return
        pprint(ret)
        return

    pprint(res)
