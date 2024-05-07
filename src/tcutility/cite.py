import requests
import json
from tcutility import spell_check, cache



# @cache.cache_file('dois')
@cache.cache
def _get_doi_data(doi: str) -> dict:
	'''
	Get information about an article using the crossref.org API.

	Args:
		doi: the DOI to get information about.
	'''
	print(f'http://api.crossref.org/works/{doi}')
	data = requests.get(f'http://api.crossref.org/works/{doi}').text
	if data == 'Resource not found.':
		raise ValueError(f'Could not find DOI {doi}.')
	data = json.loads(data)
	return data


# @cache.cache_file('journal_abbrvs')
@cache.cache
def _get_journal_abbreviation(journal: str) -> str:
	'''
	Get the journal name abbreviation using the abbreviso API.

	Args:
		journal: the name of the journal to get the abbreviation of.
	'''
	return requests.get(f"https://abbreviso.toolforge.org/a/{journal}").text


def cite(doi: str, style: str = 'wiley', mode='html') -> str:
	'''
	Format an article in a certain style.

	Args:
		doi: the article DOI to generate a citation for.
		style: the style formatting to use. Can be ``['wiley', 'acs', 'rsc']``.
		mode: the formatting mode. Can be ``['html', 'latex', 'plain']``.
	'''
	# check if the style was correctly given
	spell_check.check(style, ['wiley', 'acs', 'rsc'])
	spell_check.check(mode, ['html', 'latex', 'plain'])

	# get the information about the DOI
	data = _get_doi_data(doi)

	if data['message']['type'] == 'journal-article':
		citation = _format_article(data, style)

	if data['message']['type'] == 'book-chapter' or (data['message']['type'] == 'other' and 'ISBN' in data['message']):
		citation = _format_book_chapter(data, style)

	if mode == 'plain':
		citation = citation.replace('<i>', '')
		citation = citation.replace('</i>', '')
		citation = citation.replace('<b>', '')
		citation = citation.replace('</b>', '')

	if mode == 'latex':
		citation = citation.replace('<i>', r'\textit{')
		citation = citation.replace('</i>', '}')
		citation = citation.replace('<b>', r'\textbf{')
		citation = citation.replace('</b>', '}')

	return citation


def _format_article(data: dict, style: str) -> str:
	# grab usefull data
	journal = data['message']['container-title'][0]
	journal_abbreviation = _get_journal_abbreviation(journal)
	year = data['message']['issued']['date-parts'][0][0]
	volume = data['message']['volume']
	pages = data['message'].get('page')
	title = data['message']['title'][0]

	# Get the initials from the author given names
	# also store the family names
	initials = []
	last_names = []
	for author in data['message']['author']:
		# we get the capital letters from the first names
		# these will become the initials for this author
		firsts = [char + '.' for char in author['given'].title() if char.isupper()]
		firsts = " ".join(firsts)
		initials.append(firsts)
		last_names.append(author['family'].title())

	# format the citation correctly
	if style == 'wiley':
		names = [f'{first} {last}' for first, last in zip(initials, last_names)]
		citation = f'{", ".join(names)}, <i>{journal_abbreviation}</i> <b>{year}</b>, <i>{volume}</i>'
		if pages:
			citation += f', {pages}'
		citation += '.'

	elif style == 'acs':
		names = [f'{last}, {first}' for first, last in zip(initials, last_names)]
		citation = f'{"; ".join(names)} {title} <i>{journal_abbreviation}</i> <b>{year}</b>, <i>{volume}</i>'
		if pages:
			citation += f', {pages}'
		citation += f'. DOI: {doi}'

	elif style == 'rsc':
		names = [f'{first} {last}' for first, last in zip(initials, last_names)]
		citation = f'{", ".join(names)}, <i>{journal_abbreviation}</i> {year}, <b>{volume}</b>'
		if pages:
			citation += f', {pages}'
		citation += '.'

	return citation


def _format_book_chapter(data: dict, style: str) -> str:
	# grab usefull data
	publisher = data['message']['publisher']
	year = data['message']['published-print']['date-parts'][0][0]
	pages = data['message'].get('page')
	book_title = data['message']['container-title'][0]
	chapter_title = data['message']['title'][0]

	# Get the initials from the author given names
	# also store the family names
	initials = []
	last_names = []
	for author in data['message']['author']:
		# we get the capital letters from the first names
		# these will become the initials for this author
		firsts = [char + '.' for char in author['given'].title() if char.isupper()]
		firsts = " ".join(firsts)
		initials.append(firsts)
		last_names.append(author['family'].title())

	# format the citation correctly
	if style == 'wiley':
		names = [f'{last}, {first}' for first, last in zip(initials, last_names)]
		citation = f'{", ".join(names)}, ({year}). {chapter_title}. In: <i>{book_title}</i> <b>{year}</b>, {pages}.'

	elif style == 'acs':
		names = [f'{last}, {first}' for first, last in zip(initials, last_names)]
		citation = f'{"; ".join(names)} {title} <i>{journal_abbreviation}</i> <b>{year}</b>, <i>{volume}</i>'
		if pages:
			citation += f', {pages}'
		citation += f'. DOI: {doi}'

	elif style == 'rsc':
		names = [f'{first} {last}' for first, last in zip(initials, last_names)]
		citation = f'{", ".join(names)}, <i>{journal_abbreviation}</i> {year}, <b>{volume}</b>'
		if pages:
			citation += f', {pages}'
		citation += '.'

	return citation


