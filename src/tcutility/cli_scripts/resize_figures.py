""" Module containing CLI functionality for resizing pictures containing molecules """
import argparse
from tcutility import report
import os
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()


def create_subparser(parent_parser: argparse.ArgumentParser):
    desc = """Resize images containing molecules.

This CLI-program resizes images in a directory based on detected circles. It will ensure the selected circles are placed at the same location and are also resized to be the same size.
When starting the program it will show you for each image numbered detected atoms. 
Entering the desired number into the CLI will select it for resizing. If you do not enter a number, the figure will be ignored for further processing.
New images will be written to the folder postpended with _fixed.
    """
    subparser = parent_parser.add_parser('resize', help=desc, description=desc, formatter_class=argparse.RawTextHelpFormatter)
    subparser.add_argument("-f", "--folder",
                           type=str,
                           help="A folder containing images containing molecules which will be resized.",
                           default=None)
    subparser.add_argument("-p", "--padding",
                           help="""The amount of padding to add to the resized figures.
If given an integer we use pixel padding. E.g. -p 50 will add a padding of 50 pixels.
Add a %%-sign to use relative padding. E.g. -p 10%% will add a padding of 10%%.""",
                           default='10%')


def main(args: argparse.Namespace):
    circle_numbers = {}
    if args.folder is not None:
        img_paths = [os.path.join(args.folder, img_path) for img_path in os.listdir(args.folder)]
    else:
        img_paths = filedialog.askopenfilenames()

    for img_path in img_paths:
        report.figure_resizer._analyse_img(img_path, plot=True)
        circle = input(f'Select circle for {img_path}, leave empty to skip: ')
        if circle == '':
            continue

        circle_numbers[img_path] = int(circle)

    report.figure_resizer.resize(img_paths, circle_numbers, padding=args.padding)
