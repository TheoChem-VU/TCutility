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
	'''
	# check if the style was correctly given
	spell_check.check(style, ['wiley', 'acs', 'rsc'])

	# get the information about the DOI
	data = _get_doi_data(doi)
	
	# grab usefull data
	journal = data['message']['container-title'][0]
	journal_abbreviation = _get_journal_abbreviation(journal)
	year = data['message']['issued']['date-parts'][0][0]
	volume = data['message']['volume']
	pages = data['message'].get('page')

	initials = []
	last_names = []
	for author in data['message']['author']:
		# we get the capital letters from the first names
		# these will become the initials for this author
		firsts = [char + '.' for char in author['given'].title() if char.isupper()]
		firsts = " ".join(firsts)
		initials.append(firsts)
		last_names.append(author['family'].title())

	# and format the citation correctly
	if style == 'wiley':
		names = [f'{first} {last}' for first, last in zip(initials, last_names)]
		citation = f'{", ".join(names)}, <i>{journal_abbreviation}</i> <b>{year}</b>, <i>{volume}</i>'
		if pages:
			citation += f', {pages}'
		citation += '.'

	elif style == 'acs':
		raise NotImplementedError()

	elif style == 'rsc':
		raise NotImplementedError()

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
