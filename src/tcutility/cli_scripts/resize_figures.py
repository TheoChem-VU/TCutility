""" Module containing CLI functionality for resizing pictures containing molecules """
import argparse
from tcutility import report
import os


def create_subparser(parent_parser: argparse.ArgumentParser):
    desc = """Resize images containing molecules.

This CLI-program resizes images in a directory based on detected circles. It will ensure the selected circles are placed at the same location and are also resized to be the same size.
When starting the program it will show you for each image numbered detected atoms. 
Entering the desired number into the CLI will select it for resizing. If you do not enter a number, the figure will be ignored for further processing.
New images will be written to the folder postpended with _fixed.
    """
    subparser = parent_parser.add_parser('resize', help=desc, description=desc, formatter_class=argparse.RawTextHelpFormatter)
    subparser.add_argument("folder",
                           type=str,
                           nargs=1,
                           help="A folder containing images containing molecules which will be resized.")
    subparser.add_argument("-p", "--padding",
                           help="""The amount of padding to add to the resized figures.
If given an integer we use pixel padding. E.g. -p 50 will add a padding of 50 pixels.
Add a %%-sign to use relative padding. E.g. -p 10%% will add a padding of 10%%.""",
                           default='10%')


def main(args: argparse.Namespace):
    circle_numbers = {}
    for img_path in os.listdir(args.folder[0]):
        report.figure_resizer.get_data(os.path.join(args.folder[0], img_path), plot=True)
        circle = input(f'Select circle for {img_path}, leave empty to skip: ')
        if circle == '':
            continue

        circle_numbers[img_path] = int(circle)

    report.figure_resizer.resize(args.folder[0], circle_numbers, padding=args.padding)

    # print(args.folder)
