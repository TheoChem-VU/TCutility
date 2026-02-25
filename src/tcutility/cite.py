import json
import os

from tcutility import environment, spell_check
from tcutility.cache import cache_file
import numpy as np

__all__ = ["cite", "_get_doi_data", "_get_doi_data_from_title", "_get_doi_data_from_query", "_get_publisher_city", "_get_journal_abbreviation"]


@environment.requires_optional_package("requests")
@cache_file('tcutility_citation')
def _get_doi_data(doi: str) -> dict:
    """
    Get information about an article using the crossref.org API.

    Args:
            doi: the DOI to get information about.
    """
    import requests

    data = requests.get(f"http://api.crossref.org/works/{doi}").text
    if data == "Resource not found.":
        raise ValueError(f"Could not find DOI {doi}.")
    data = json.loads(data)
    return data


@environment.requires_optional_package("requests")
@cache_file('tcutility_citation')
def _get_doi_data_from_title(title: str):
    import requests

    citedby = requests.get(f"http://api.crossref.org/works?query.title={title}").text
    citedby = json.loads(citedby)["message"]["items"]
    citedby = [row for row in citedby if row['type'] == 'journal-article']
    nearnesses = []
    for row in citedby:
        title = ''.join(row['title'])
        nearness = spell_check.wagner_fischer(title, title)
        nearness = nearness / len(title)
        nearnesses.append(nearness)

    if len(nearnesses) == 0:
        return

    nearest_idx = np.argmin(nearnesses)
    return citedby[nearest_idx]


@environment.requires_optional_package("requests")
@cache_file('tcutility_citation')
def _get_doi_data_from_query(**queries):
    import requests

    valid_queries = [
        "affiliation",
        "degree",
        "event-acronym",
        "bibliographic",
        "container-title",
        "publisher-name",
        "author",
        "event-theme",
        "standards-body-acronym",
        "chair",
        "event-location",
        "translator",
        "funder-name",
        "event-name",
        "publisher-location",
        "title",
        "standards-body-name",
        "contributor",
        "description",
        "editor",
        "event-sponsor"
        ]

    query_strings = []
    for query, value in queries.items():
        if value is None:
            continue

        query = query.replace('_', '-')

        if query not in valid_queries:
            raise ValueError(f'Query "{query}" is not a valid query!')
        if isinstance(value, str):
            query_strings.append(f'query.{query}={value.replace("&", "")}')
        else:
            for v in value:
                query_strings.append(f'query.{query}={v.replace("&", "")}')

    query_string = '&'.join(query_strings)
    citedby = requests.get(f"http://api.crossref.org/works?{query_string}").text
    # print(f"http://api.crossref.org/works?{query_string}")
    citedby = json.loads(citedby)["message"]["items"]
    citedby = [row for row in citedby if row['type'] == 'journal-article']
    nearnesses = []
    for row in citedby:
        title = ''.join(row['title'])
        nearness = spell_check.wagner_fischer(title, title)
        nearness = nearness / len(title)
        nearnesses.append(nearness)

    if len(nearnesses) == 0:
        return

    nearest_idx = np.argmin(nearnesses)
    return citedby[nearest_idx]

# data = _get_doi_data_from_query(title="AGMFNet: Attention-guided multi-scale feature fusion network for infrared small target detection",
#     author=("He", "Liu", "Yang", "Yuan"), publisher_name="Elsevier")
# print(data)

# exit()

@environment.requires_optional_package("requests")
@cache_file('tcutility_journal_abbrvs')
def _get_journal_abbreviation(journal: str) -> str:
    """
    Get the journal name abbreviation using the abbreviso API.

    Args:
            journal: the name of the journal to get the abbreviation of.
    """
    import requests

    return requests.get(f"https://abbreviso.toolforge.org/a/{journal}").text.replace('amp;', '&')


@cache_file('tcutility_publisher_city')
def _get_publisher_city(publisher: str) -> str:
    """
    Get the city of a publisher.
    """
    with open(os.path.join(os.path.split(__file__)[0], "data", "cite", "_publisher_cities.json")) as cities:
        cities = json.loads(cities.read())
    return cities.get(publisher)


@cache_file('tcutility_citation')
def cite(doi: str, style: str = "wiley", mode="html") -> str:
    """
    Format an article in a certain style.

    Args:
            doi: the article DOI to generate a citation for.
            style: the style formatting to use. Can be ``['wiley', 'acs', 'rsc']``.
            mode: the formatting mode. Can be ``['html', 'latex', 'plain']``.
    """
    # check if the style was correctly given
    spell_check.check(style, ["wiley", "acs", "rsc"])
    spell_check.check(mode, ["html", "latex", "plain"])

    # get the information about the DOI
    data = _get_doi_data(doi)
    citation = ""

    if data["message"]["type"] == "journal-article":
        citation = _format_article(data, style)

    if data["message"]["type"] == "book-chapter" or (data["message"]["type"] == "other" and "ISBN" in data["message"]):
        citation = _format_book_chapter(data, style)

    if mode == "plain":
        citation = citation.replace("<i>", "")
        citation = citation.replace("</i>", "")
        citation = citation.replace("<b>", "")
        citation = citation.replace("</b>", "")

    if mode == "latex":
        citation = citation.replace("<i>", r"\textit{")
        citation = citation.replace("</i>", "}")
        citation = citation.replace("<b>", r"\textbf{")
        citation = citation.replace("</b>", "}")

    return citation


def get_pages(data):
    try:
        pages = data["message"].get("page").replace("-", "–")
        return pages
    except AttributeError:
        pages = "???"

    url = data["message"]["URL"]
    if "ceur." in url:
        return "e" + url.split("ceur.")[-1]


def is_accepted(data):
    for assertion in data["message"].get("assertion", []):
        if assertion["name"] == "accepted":
            return True
    return False


def _format_article(data: dict, style: str) -> str:
    # grab usefull data
    journal = data["message"]["container-title"][0]
    journal_abbreviation = _get_journal_abbreviation(journal)
    year = data["message"]["issued"]["date-parts"][0][0]
    volume = data["message"].get("volume", "")
    pages = get_pages(data)
    title = data["message"]["title"][0]
    doi = data["message"]["DOI"]

    # accepted = is_accepted(data)  # not using this one yet
    citation = ""

    # Get the initials from the author given names
    # also store the family names
    initials = []
    last_names = []
    for author in data["message"]["author"]:
        # we get the capital letters from the first names
        # these will become the initials for this author
        firsts = [char + "." for char in author["given"].title() if char.isupper()]
        firsts = " ".join(firsts)
        initials.append(firsts)
        last_names.append(author["family"].title())

    # format the citation correctly
    if style == "wiley":
        names = [f"{first} {last}" for first, last in zip(initials, last_names)]
        citation = f"{', '.join(names)}, <i>{journal_abbreviation}</i> <b>{year}</b>, <i>{volume}</i>"
        if pages:
            citation += f", {pages}"
        citation += "."

    elif style == "acs":
        names = [f"{last}, {first}" for first, last in zip(initials, last_names)]
        citation = f"{'; '.join(names)} {title} <i>{journal_abbreviation}</i> <b>{year}</b>, <i>{volume}</i>"
        if pages:
            citation += f", {pages}"
        citation += f". DOI: {doi}"

    elif style == "rsc":
        names = [f"{first} {last}" for first, last in zip(initials, last_names)]
        citation = f"{', '.join(names)}, <i>{journal_abbreviation}</i> {year}, <b>{volume}</b>"
        if pages:
            citation += f", {pages}"
        citation += "."

    return citation


def _format_book_chapter(data: dict, style: str) -> str:
    # grab usefull data
    publisher = data["message"]["publisher"]
    year = data["message"]["published-print"]["date-parts"][0][0]
    pages = data["message"].get("page")
    book_title = data["message"]["container-title"][0]
    chapter_title = data["message"]["title"][0]
    city = _get_publisher_city(publisher)
    citation = ""

    original_book_data = None
    for isbn in data["message"]["isbn-type"]:
        if isbn["type"] == "electronic":
            original_book_data = _get_doi_data(f"{data['message']['prefix']}/{isbn['value']}")
            break

    # Get the initials from the author given names
    # also store the family names
    n_authors = len(data["message"]["author"])
    initials = []
    last_names = []
    for author in data["message"]["author"]:
        # we get the capital letters from the first names
        # these will become the initials for this author
        firsts = [char + "." for char in author["given"].title() if char.isupper()]
        firsts = " ".join(firsts)
        initials.append(firsts)
        last_names.append(author["family"].title())

    if original_book_data and "editor" in original_book_data["message"]:
        n_editors = len(original_book_data["message"]["editor"])
        editor_initials = []
        editor_last_names = []
        for author in original_book_data["message"]["editor"]:
            # we get the capital letters from the first names
            # these will become the initials for this author
            firsts = [char + "." for char in author["given"].title() if char.isupper()]
            firsts = " ".join(firsts)
            editor_initials.append(firsts)
            editor_last_names.append(author["family"].title())
    else:
        n_editors = 0
        editor_initials = []
        editor_last_names = []

    # format the citation correctly
    if style == "wiley":
        names = [f"{last}, {first}" for first, last in zip(initials, last_names)]
        editors = [f"{first} {last}" for first, last in zip(editor_initials, editor_last_names)]
        if n_authors == 1:
            names = names[0]

        if 1 < n_authors < 4:
            names = ", ".join(names[:-1]) + " and " + names[-1]

        if n_authors >= 4:
            names = ", ".join(names[:3]) + " et al."

        if n_editors == 1:
            editors = editors[0]

        if 1 < n_editors < 4:
            editors = ", ".join(editors[:-1]) + " and " + editors[-1]

        if n_editors >= 4:
            editors = ", ".join(editors[:3]) + " et al."

        citation = f"{names} ({year}). {chapter_title}. In: <i>{book_title}</i> (ed. {editors}), {pages}. {city}: {publisher}"

    elif style == "acs":
        raise NotImplementedError("No support for ACS style yet")

    elif style == "rsc":
        raise NotImplementedError("No support for RSC style yet")

    return citation
