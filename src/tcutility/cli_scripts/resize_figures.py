""" Module containing CLI functionality for resizing pictures containing molecules """
from tcutility import report
import os
import click


@click.command()
@click.argument('folder', type=click.Path(exists=True))
@click.option('-p', '--padding', default='10%', help="""The amount of padding to add to the resized figures.
If given an integer we use pixel padding. E.g. -p 50 will add a padding of 50 pixels.
Add a %%-sign to use relative padding. E.g. -p 10%% will add a padding of 10%%.""")
def resize(folder, padding):
    """Resize images containing molecules.

    This CLI-program resizes images in a directory based on detected circles. It will ensure the selected circles are placed at the same location and are also resized to be the same size.
    When starting the program it will show you for each image numbered detected atoms.
    Entering the desired number into the CLI will select it for resizing. If you do not enter a number, the figure will be ignored for further processing.
    New images will be written to the folder postpended with _fixed.
    """
    circle_numbers = {}
    for img_path in os.listdir(folder):
        report.figure_resizer.get_data(os.path.join(folder, img_path), plot=True)
        circle = input(f'Select circle for {img_path}, leave empty to skip: ')
        if circle == '':
            continue

        circle_numbers[img_path] = int(circle)

    report.figure_resizer.resize(folder, circle_numbers, padding=padding)
