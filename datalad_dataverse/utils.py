from pathlib import Path
import re

from pyDataverse.api import NativeApi

from datalad_next.utils import update_specialremote_credential

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
    'Other',
]


def get_native_api(baseurl, token):
    """
    Returns
    -------
    NativeApi
      The pyDataverse API wrapper
    """
    return NativeApi(baseurl, token)


def get_api(url, credman, credential_name=None):
    """Get authenticated API access to a dataverse instance

    Parameters
    ----------
    url: str
      Base URL of the target dataverse deployment.
    credman: CredentialManager
      For querying credentials based on a given name, or an authentication
      realm determined from the specified URL
    credential_name: str, optional
      If given, the name will be used to identify a credential for API
      authentication. If that fails, or no name is given, an attempt to
      identify a credential based on the dataverse URL will be made.

    Returns
    -------
    NativeApi
      The pyDataverse API wrapper. The token used for authentication is
      available via the `.api_token` accessor.

    Raises
    ------
    LookupError
      When no credential could be determined, either by name or by realm.

    HTTPError
      If making a simple API version request using the determined credential
      fails, the exception from `requests.raise_for_status()` is passed
      through.
    """
    # TODO the below is almost literally taken from
    # the datalad-annex:: implementation in datalad-next
    # this could become a common helper
    credential_realm = url.rstrip('/') + '/dataverse'
    cred = None
    if credential_name:
        # we can ask blindly first, caller seems to know what to do
        cred = credman.get(
            name=credential_name,
            # give to make legacy credentials accessible
            _type_hint='token',
        )
    if not cred:
        creds = credman.query(
            _sortby='last-used',
            realm=credential_realm,
        )
        if creds:
            credential_name, cred = creds[0]
    if not cred:
        # credential query failed too, enable manual entry
        cred = credman.get(
            # this might still be None
            name=credential_name,
            _type_hint='token',
            _prompt=f'A dataverse API token is required for access',
            # inject anything we already know to make sure we store it
            # at the very end, and can use it for discovery next time
            realm=credential_realm,
        )
    if cred is None or 'secret' not in cred:
        raise LookupError('No suitable credential found')

    # connect to dataverse instance
    api = get_native_api(
        baseurl=url,
        token=cred['secret'],
    )
    # make one cheap request to ensure that the token is
    # in-principle working -- we won't be able to verify all necessary
    # permissions for all possible operations anyways
    api.get_info_version().raise_for_status()

    update_specialremote_credential(
        'dataverse',
        credman,
        credential_name,
        cred,
        credtype_hint='token',
        duplicate_hint=
        'Specify a credential name via the dlacredential= '
        'special remote parameter, and/or configure a credential '
        'with the datalad-credentials command{}'.format(
            f' with a `realm={cred["realm"]}` property'
            if 'realm' in cred else ''),
    )
    # store for reuse with data access API
    return api


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


def mangle_directory_names(path):
    """Replace leading dot in directory names of a path

    Dataverse currently auto-removes a leading dot from directory names.
    Thus, map `.` -> `_._`
    """
    LEADING_DOT_REPLACEMENT = "_._"

    local_path = Path(path)

    # only directories are treated this way:
    if not local_path.is_dir():
        filename = local_path.name
        local_path = local_path.parent
    else:
        filename = None

    if local_path == Path("."):
        # `path` either is '.' or a file in '.'.
        # Nothing to do: '.' has no representation on dataverse anyway.
        # Note also, that Path(".").parts is an empty tuple for some reason,
        # hence the code block below must be protected against this case.
        dataverse_path = local_path
    else:
        dataverse_path = \
            Path((LEADING_DOT_REPLACEMENT + local_path.parts[0][1:])
                 if local_path.parts[0].startswith('.')
                 else local_path.parts[0]
                 )
        for pt in local_path.parts[1:]:
            dataverse_path /= (LEADING_DOT_REPLACEMENT + pt[1:]) \
                if pt.startswith('.') else pt

    # re-append file if necessary
    if filename:
        dataverse_path /= filename

    return dataverse_path
