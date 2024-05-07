from tcutility.cli_scripts import read, job_script, concatenate_irc, cite

# to add a script:
# 1. Add a create_subparser function and main function to your script.
# 2. Import the script.
# 3. Add it to the dictionary below {program_name: script-module}.
sub_programs = {
    "read": read,
    "optimize": job_script,
    "concat-irc": concatenate_irc,
    "cite": cite,
}


def create_parser():
    import argparse

    parser = argparse.ArgumentParser(prog="tc")
    # add the subparsers. dest ensures we can retrieve the subparser name later on
    subparsers = parser.add_subparsers(dest="subprogram", title="TCutility command-line scripts")

    # add the subparsers to the main parser
    for sub_program in sub_programs.values():
        sub_program.create_subparser(subparsers)

    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    # if the program was called without a subprogram we simply print the help message
    if args.subprogram is None:
        parser.print_help()
        return

    # call the main function of the subprogram that was called
    sub_programs[args.subprogram].main(args)


if __name__ == "__main__":
    main()
