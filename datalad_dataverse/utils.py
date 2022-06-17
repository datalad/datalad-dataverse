import re

from pyDataverse.api import NativeApi

# This cannot currently be queried for via public API. See gh-27
DATASET_SUBJECTS = [
 'Agricultural Sciences',
 'Arts and Humanities',
 'Astronomy and Astrophysics',
 'Business and Management',
 'Chemistry',
 'Computer and Information Science',
 'Earth and Environmental Sciences',
 'Engineering',
 'Law',
 'Mathematical Sciences',
 'Medicine, Health and Life Sciences',
 'Physics',
 'Social Sciences',
 'Other']


def get_native_api(baseurl, token):
    """
    Returns
    -------
    NativeApi
      The pyDataverse API wrapper
    """
    return NativeApi(baseurl, token)


def format_doi(doi_in: str) -> str:
    """Converts unformatted DOI strings to the format expected by the dataverse API

    Compatible with DOIs starting with "doi:", as URL or raw
    (e.g., 10.5072/FK2/WQCBX1).

    Cannot be None or empty!

    Parameters
    ----------
    doi_in: str
        Unformatted doi string provided by user which is checked for None of empty values

    Returns
    -------
    str
      DOI string as needed for dataverse API, None if string is empty.


    Raises
    ------
    ValueError
      If doi_in is None or empty
    """
    if doi_in is None:
        raise ValueError('DOI input cannot be None!')
    if not isinstance(doi_in, str):
        raise TypeError('DOI input must be a string!')
    if len(doi_in) == 0:
        raise ValueError('DOI input cannot be empty!')
    dataverse_doi_pattern = r'^doi:'
    if re.match(pattern=dataverse_doi_pattern, string=doi_in):
        return doi_in

    url_doi_pattern = r'^https?:\/\/doi\.org\/'
    if re.match(url_doi_pattern, doi_in):
        return re.sub(pattern=url_doi_pattern, repl='doi:', string=doi_in)

    return f'doi:{doi_in}'
