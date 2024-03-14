def main():
    import argparse
    from tcutility.cli_scripts import job_script, concatenate_irc

    parser = argparse.ArgumentParser(prog='tc')
    # add the subparsers. dest ensures we can retrieve the subparser name later on
    subparsers = parser.add_subparsers(dest='subparser_name',
                                       title='TCutility command-line scripts')

    # to add a script:
    # 1. Add a create_subparser function and main function to your script.
    # 2. Import the script.
    # 3. Add it to the dictionary below {program_name: script-module}.
    sub_programs = {
        "optimize": job_script,
        "concat-irc": concatenate_irc,
    }

    # add the subparsers to the main parser
    for sub_program in sub_programs.values():
        sub_program.create_subparser(subparsers)

    args = parser.parse_args()

    # call the main function of the subprogram that was called
    sub_programs[args.subparser_name].main(args)


if __name__ == '__main__':
    main()
