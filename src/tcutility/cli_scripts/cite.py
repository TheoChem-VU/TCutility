""" Module containing functions for generating citations"""
import argparse
from tcutility import cite, data, spell_check
import os
import docx
from docx.shared import Pt
import htmldocx


class Docx:
    '''
    Small class that handles writing to a docx file. This should and will be moved to its own module in TCutility soon.
    '''
    def __init__(self, file='test.docx', overwrite=False):
        self.file = file
        if not os.path.exists(file) or overwrite:
            self.doc = docx.Document()
        else:
            self.doc = docx.Document(file)

        self.doc.styles['Normal'].font.name = 'Times New Roman'
        self.doc.styles['Normal'].font.size = Pt(12)
        self.doc.styles['Normal'].paragraph_format.space_after = 0
        self.html_parser = htmldocx.HtmlToDocx()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.doc.save(self.file)

    def write_paragraph(self, text, alignment=WD_ALIGN_PARAGRAPH.LEFT):
        '''
        Write a piece of text as a pragraph to this Docx file.
        This function will parse any HTML that is given in the text.
        E.g. you can use the <b></b> tags to make a piece of text bold.
        '''
        self.html_parser.add_html_to_document(text, self.doc)
        self.doc.paragraphs[-1].alignment = alignment

    def open(self):
        '''
        Open this file in Word.
        '''
        os.system(f'open {self.file}')


def create_subparser(parent_parser: argparse.ArgumentParser):
    desc = "Generate citations for various things. Currently supports generating citations for functionals, basis-sets, programs, methodologies and DOIs."
    subparser = parent_parser.add_parser('cite', help=desc, description=desc)
    subparser.add_argument("-s", "--style",
                           help="set the citation style.",
                           type=str,
                           default="wiley",
                           choices=["wiley", "acs", "rsc"])
    subparser.add_argument("object",
                           type=str,
                           help="the objects to generate citations for. This can be functionals, basis-sets, programs, methodologies or DOIs.",
                           nargs='*')
    subparser.add_argument("-o", "--output",
                           help="the output Word file to write the citations to.",
                           type=str,
                           default="citations.docx")
    subparser.add_argument("-l", "--list",
                           help="list currently available citations.",
                           action='store_true',
                           default=False)


program_references = {
    'ams': [
        '10.1002/jcc.1056',
        '10.1007/s002140050353',
    ],
    'adf': [
        '10.1002/jcc.1056',
        '10.1007/s002140050353',
    ],
    'orca': [
        '10.1002/wcms.81',
        '10.1063/5.0004608',
        '10.1002/wcms.1606',
    ],
    'dftb': [],
    'xtb': [],
    'cosmo': [],
    'crest': [],
    'pyfrag': [],
    'pyorb': [],
    'cylview': [],
}

methodology_references = {
    'fmatsfo': [],
    'eda': [],
    'asm': [],
    'zora': [],
    'ksmo': [],
    'vdd': [],
    'hydrogen bonding': [],
    'halogen bonding': [],
    'chalcogen bonding': [],
    'pnictogen bondding': [],
    'zlm fit': [],
    'becke grid': [],
    'vibrational analysis': [],
    'irc': [],
    'd3': ['10.1063/1.3382344'],
    'd3bj': ['10.1002/jcc.21759'],
    'd4': ['10.1063/1.5090222'],
}


doi_order = []
def format_paragraph(dois, style):
    paragraphs = []
    for doi in dois:
        if doi not in doi_order:
            doi_order.append(doi)
        try:
            citation = cite.cite(doi, style=style, mode="plain")
        except Exception as exp:
            print('\t' + str(exp))
            return

        print(f'  [{doi}] {citation}')
        paragraph = f'[{doi_order.index(doi) + 1}] {cite.cite(doi, style=style, mode="html")}'
        paragraphs.append(paragraph)

    return paragraphs


def _print_rect_list(printables, spaces_before=0):
    '''
    This function prints a list of strings in a rectangle to the output.
    This is similar to what the ls program does in unix.
    '''
    n_shell_col = os.get_terminal_size().columns
    # we first have to determine the correct dimensions of our rectangle
    for ncol in range(1, n_shell_col):
        # the number of rows for the number of columns
        nrows = ceil(len(printables) / ncol)
        # we then get what the rectangle would be
        mat = [printables[i * ncol: (i+1) * ncol] for i in range(nrows)]
        # and determine for each column the width
        col_lens = [max([len(row[i]) for row in mat if i < len(row)] + [0]) for i in range(ncol)]
        # then calculate the length of each row based on the column lengths
        # we use a spacing of 2 spaces between each column
        row_len = spaces_before + sum(col_lens) + 2 * len(col_lens) - 2

        # if the rows are too big we exit the loop
        if row_len > n_shell_col:
            break

        # store the previous loops results
        prev_col_lens = col_lens
        prev_mat = mat

    # then print the strings with the right column widths
    for row in prev_mat:
        print(" " * spaces_before + "  ".join([x.ljust(col_len) for x, col_len in zip(row, prev_col_lens)]))


def main(args: argparse.Namespace):
    available_citations = list(program_references.keys()) + list(methodology_references.keys()) + list(data.functionals.functionals.keys())
    if args.list:
        print('OBJECTS WITH AVAILABLE REFERENCES:')
        print('    Programs')
        print('    ========')
        printables = [prog for prog, dois in program_references.items() if len(dois) > 0]
        _print_rect_list(printables, 4)
        print()

        print('    Methodology')
        print('    ===========')
        printables = [meth for meth, dois in methodology_references.items() if len(dois) > 0]
        _print_rect_list(printables, 4)
        print()

        print('    Functionals')
        print('    ===========')
        printables = [xc_info.path_safe_name for xc, xc_info in data.functionals.functionals.items() if len(xc_info.dois) > 0]
        _print_rect_list(printables, 4)
        print()

        return

    objs = args.objects
    if len(objs) == 1 and os.path.isfile(objs[0]):
        with open(objs[0]) as inp:
            objs = [line.strip() for line in inp.readlines()]

    with Docx(file=args.output, overwrite=True) as out:
        for obj in objs:
            paragraphs = None            # try to format a functional
            try:
                xc_info = data.functionals.get(obj)
                print('Functional', obj)
                paragraph_title = f'XC-Functional: <b>{xc_info.name_html}</b>'
                paragraphs = format_paragraph(xc_info.dois, style=args.style)

            except KeyError:
                pass

            # if its not a functional we look in the programs
            if obj.lower() in program_references:
                print('Program', obj)
                paragraph_title = f'Program: <b>{obj}</b>'
                paragraphs = format_paragraph(program_references[obj.lower()], style=args.style)

            # and the methodologies
            if obj.lower() in methodology_references:
                print('Methodology', obj)
                paragraph_title = f'Method: <b>{obj}</b>'
                paragraphs = format_paragraph(methodology_references[obj.lower()], style=args.style)

            # if we still dont have a paragraphs we check if it is a DOI
            if paragraphs is None and obj.startswith('10.'):
                print('DOI')
                paragraph_title = f'DOI: <b>{obj}</b>'
                paragraphs = format_paragraph([obj], style=args.style)

            if paragraphs is None:
                spell_check.make_suggestion(obj, available_citations, ignore_case=True)
                continue

            out.write_paragraph(paragraph_title)
            for paragraph in paragraphs:
                out.write_paragraph(paragraph, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY)
            out.write_paragraph(' ')

    out.open()
