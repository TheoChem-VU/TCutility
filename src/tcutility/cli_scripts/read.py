""" Module containing functions for reading and printing calculation results to the CL """
import argparse
from tcutility import results
from pprint import pprint


def create_subparser(parent_parser: argparse.ArgumentParser):
    desc = "Read results from a calculation."
    subparser = parent_parser.add_parser('read', help=desc, description=desc)
    subparser.add_argument("-s", "--status",
                           help="Shortcut to only print the status of the calculation.",
                           default=False,
                           action="store_true")
    subparser.add_argument("-p", "--properties",
                           help="Shortcut to only print calculated properties for the calculation.",
                           default=False,
                           action="store_true")
    subparser.add_argument("workdir",
                           type=str,
                           help="The calculation directory to read the results from.")
    subparser.add_argument("keys",
                           type=str,
                           nargs='*',
                           help="The keys to read from the results.")


def main(args: argparse.Namespace):
    res = results.read(args.workdir)

    # if status flag was set we print the status name
    if args.status:
        print(res.status.name)
        return

    # if properties flag was set we print all properties
    if args.properties:
        pprint(res.properties)
        return

    # print specific keys
    if len(args.keys) > 0:
        ret = {k: res.get_multi_key(k) for k in args.keys}
        # if only one key was given we just print the value
        if len(ret) == 1:
            print(list(ret.values())[0])
            return
        pprint(ret)
        return

    # if we did not give keys or set flags we just print everything
    pprint(res)
