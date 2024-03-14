""" Module containing functions for quickly submitting (simple) jobs via the command line """
import argparse


def optimize():
    raise NotImplementedError

    # Create the parser
    parser = argparse.ArgumentParser(
        description="""
    """
    )

    # Add the arguments
    parser.add_argument("-x", "--xxx", type=str, help="xxx")

    # Parse the arguments
    # args = parser.parse_args()

    print("Succesfully sumbitted job")
