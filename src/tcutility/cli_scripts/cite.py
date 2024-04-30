""" Module containing functions for generating citations"""
import argparse
from tcutility import cite, data, spell_check
import os
import docx
from docx.shared import Pt
import htmldocx


class Docx:
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

        self.figure_number = 1

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.doc.save(self.file)

    def write_paragraph(self, text):
        self.html_parser.add_html_to_document(text, self.doc)

    def open(self):
    	os.system(f'open {self.file}')


def create_subparser(parent_parser: argparse.ArgumentParser):
    desc = "Generate citations for various things."
    subparser = parent_parser.add_parser('cite', help=desc, description=desc)
    subparser.add_argument("-s", "--style",
                           help="Set the citation style.",
                           type=str,
                           default="wiley",
                           choices=["wiley", "acs", "rsc"])
    subparser.add_argument("object",
                           type=str,
                           help="The objects to generate citations for. This can be functionals, basis-sets or programs.",
                           nargs='+')
    subparser.add_argument("-o", "--output",
    					   help="The output Word file to write the citations to.",
    					   type=str,
    					   default="citations.docx")


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
}


doi_order = []
def format_paragraph(title, dois):
	paragraph = title + '<br>'
	for doi in dois:
		if doi not in doi_order:
			doi_order.append(doi)

		paragraph += f'[{doi_order.index(doi)}] {cite.cite(doi)}<br>'
	return paragraph


def main(args: argparse.Namespace):
	objs = args.object
	if len(objs) == 1 and os.path.isfile(objs[0]):
		with open(objs[0]) as inp:
			objs = [line.strip() for line in inp.readlines()]

	with Docx(file=args.output, overwrite=True) as out:
		for obj in objs:
			paragraph = None
			print(obj)
			# try to format a functional
			try:
				xc_info = data.functionals.get(obj)
				paragraph = format_paragraph(f'XC-Functional: <b>{xc_info.name_html}</b>', xc_info.dois)
			except KeyError:
				pass

			# if its not a functional we look in the programs
			if obj.lower() in program_references:
				paragraph = format_paragraph(f'Program: <b>{obj}</b>', program_references[obj.lower()])

			# and the methodologies
			if obj.lower() in methodology_references:
				paragraph = format_paragraph(f'Method: <b>{obj}</b>', methodology_references[obj.lower()])

			if paragraph is None:
				available = list(program_references.keys()) + list(methodology_references.keys()) + list(data.functionals.functionals.keys())
				spell_check.make_suggestion(obj, available, caller_level=3, ignore_case=True)
				continue

			out.write_paragraph(paragraph)

	out.open()
