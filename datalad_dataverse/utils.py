from __future__ import annotations

import re
from pathlib import Path

from pyDataverse.api import NativeApi
from unidecode import unidecode

from datalad_next.utils import update_specialremote_credential


__docformat__ = "numpy"


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


# We do not consider ``.`` to be safe in a dirname because
# dataverse will ignore it, if it is the first character in
# a directory name.
DATAVERSE_DIRNAME_SAFE = {
    chr(c) for c in range(128)
    if chr(c).isprintable()
    and (chr(c).isalnum() or chr(c) in ('.', '_', '-', ' '))
}

DATAVERSE_FILENAME_SAFE = {
    chr(c) for c in range(128)
    if chr(c).isprintable()
    and chr(c) not in ('/', ':', '*', '?', '"', '<', '>', '|', ';', '#')
}


TO_ENCODE = {
    '.': '_.',
    '_': '__'
}


TO_DECODE = {v: k for k, v in TO_ENCODE.items()}


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
        credential_name, cred = credman.obtain(
            name=credential_name,
            prompt=f'A dataverse API token is required for access',
            # give to make legacy credentials accessible
            type_hint='token',
        )
    if not cred:
        creds = credman.query(
            _sortby='last-used',
            realm=credential_realm,
        )
        if creds:
            credential_name, cred = creds[0]
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


def mangle_path(path: str | Path) -> Path:
    """Quote unsupported chars in all elements of a path

    Dataverse currently auto-removes a leading dot from directory names. It also
    only allows the characters ``_``, ``-``, ``.``, ``/``, and ``\`` in
    directory names. File names may not contain the following characters:
    ``/``, ``:``, ``*``,  ``?``,  ``"``,  ``<``,  ``>``,  ``|``, ``;``,  and
    ``#``.
    We therefore encode leading dots and all non-allowed characters in all
    elements of the path. We also replace leading dots in file names in order
    to simplify un-mangling. This allows us to handle un-mangling equally for
    directories and files.

    Parameters
    ----------
    path: str | Path
        the path that should be mangled

    Returns
    -------
    Path
        a path object with the un-mangled name
    """

    local_path = Path(path)

    # only directories are treated this way:
    if not local_path.is_dir():
        filename = _dataverse_filename_quote(local_path.name)
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
        dataverse_path = Path(_dataverse_dirname_quote(local_path.parts[0]))
        for pt in local_path.parts[1:]:
            dataverse_path /= _dataverse_dirname_quote(pt)

    # re-append file if necessary
    if filename:
        dataverse_path /= filename

    return dataverse_path


def unmangle_path(dataverse_path: str | Path) -> Path:
    """Revert dataverse specific path name mangling

    This method undoes the quoting performed by ``mangle_path()``.

    Parameters
    ----------
    dataverse_path: str | Path
        the path that should be un-mangled

    Returns
    -------
    Path
        a path object with the un-mangled name
    """
    dataverse_path = Path(dataverse_path)
    if dataverse_path == Path("."):
        # `path` either is '.' or a file in '.'.
        # Nothing to do: '.' has no representation on dataverse anyway.
        # Note also, that Path(".").parts is an empty tuple for some reason,
        # hence the code block below must be protected against this case.
        result_path = dataverse_path
    else:
        result_path = Path(_dataverse_unquote(dataverse_path.parts[0]))
        for pt in dataverse_path.parts[1:]:
            result_path /= _dataverse_unquote(pt)
    return result_path


def _encode_leading_dot(name: str) -> str:
    """ Encode a leading dot in the name in a revertable way

    Parameters
    ----------
    name: str
        the name in which a leading dot should be replaced

    Returns
    -------
    str:
        `name` without leading dots

    """
    return TO_ENCODE.get(name[0], name[0]) + name[1:]


def _dataverse_dirname_quote(dirname: str) -> str:
    """ Encode dirname to only contain valid dataverse directory name characters

    Directory names in dataverse can only contain alphanum and ``_``, ``-``,
    ``.``, `` ``, ``/``, and ``\``. All other characters are replaced by
    ``-<HEXCODE>`` where ``<HEXCODE>`` is a two digit hexadecimal.

    Because ``.``, i.e. dot, at the start of a directory name is ignored by
    dataverse, it is encoded as well to prevent name collisions, for example,
    between ``.datalad`` and ``datalad``.
    """
    ascii_dirname = unidecode(dirname) or f"_not_representable_{len(dirname)}"
    quoted_dirname = _dataverse_quote(ascii_dirname, DATAVERSE_DIRNAME_SAFE)
    return _encode_leading_dot(quoted_dirname)


def _dataverse_filename_quote(filename: str) -> str:
    """ Encode filename to only contain valid dataverse file name characters

    File names in dataverse must not contain the following characters:
    ``/``, ``:``, ``*``,  ``?``,  ``"``,  ``<``,  ``>``,  ``|``, ``;``,  and
    ``#``.

    In order to be able to use the same decoding for file names and directory
    names, we also encode leading dots in file names, although that is not
    strictly necessary with dataverse, because it would preserve the leading
    dots in file names.


    """
    ascii_filename = unidecode(filename) or f"_not_representable_{len(filename)}"
    quoted_filename = _dataverse_quote(ascii_filename, DATAVERSE_FILENAME_SAFE)
    return _encode_leading_dot(quoted_filename)


def _dataverse_quote(name: str,
                     safe: set[str],
                     esc: str = "-"
                     ) -> str:
    """ Encode name to only contain characters from the set ``safe``

    All characters that are not in the ``safe`` set and the escape character
    ``esc`` are replaced by ``<esc><HEXCODE>`` where ``<HEXCODE>`` is a
    two digit hexadecimal representation of the code of the character

    The escape character must be in the safe set and character codes must
    be in the interval 0 ... 127. We also assume the hexdigits are in the
    safe set.

    Parameters
    ----------
    name: str
        The name in which non-safe characters should be escaped
    safe: set[str]
        The set of safe characters, i.e. characters that don't need escaping
    esc
        The escape character.

    Returns
    -------
    str
        The name in which all non-safe characters are escaped
    """

    def verify_range(character: str) -> bool:
        if 0 <= ord(character) <= 127:
            return True
        raise ValueError(
            f"Out of range character '{character}'"
            f" (code: {ord(character)})"
        )

    assert esc in safe
    return "".join([
        f"{esc}{ord(c):02X}" if c not in safe or c == esc else c
        for c in name
        if verify_range(c)
    ])


def _dataverse_unquote(quoted_name: str,
                       esc: str = "-"
                       ) -> str:
    """ Revert leading dot encoding and non safe-character quoting

    Parameters
    ----------
    quoted_name: str
        the quoted string

    esc:
        the escape character that was used for quoting

    Returns
    -------
    str:
        the unquoted string

    Raises
    ------
    ValueError:
        see description of `_dataverse_unquote_escaped`
    """
    if len(quoted_name) >= 2 and quoted_name[:2] in TO_DECODE:
        quoted_name = TO_DECODE[quoted_name[:2]] + quoted_name[2:]
    return _dataverse_unquote_escaped(quoted_name, esc)


def _dataverse_unquote_escaped(quoted_name: str,
                               esc: str = "-"
                               ) -> str:
    """ Revert the quoting done in ``dataverse_quote()``

    Parameters
    ----------
    quoted_name: str
        the quoted string

    esc: str
        the escape character that was used for quoting

    Returns
    -------
    str:
        the unquoted string

    Raises
    ------
    ValueError:
        will raise a ValueError if an encoding is faulty, i.e. an escape
        character is not followed by two hex digits
    """

    """ Revert the quoting done in ``dataverse_quote()`` """
    try:
        unquoted_name = ""
        state = 0
        for index, character in enumerate(quoted_name):
            if state == 0:
                if character == esc:
                    state = 1
                    code = 0
                else:
                    unquoted_name += character
            elif state == 1:
                state = 2
                code = 16 * int(character, 16)
            else:
                state = 0
                code += int(character, 16)
                unquoted_name += chr(code)
    except Exception as e:
        raise ValueError("Dataverse quoting error in:" + quoted_name) from e

    if state != 0:
        raise ValueError("Dataverse quoting error in:" + quoted_name)

    return unquoted_name
