from itertools import product
from pathlib import Path
from unicodedata import lookup

import pytest
from unidecode import unidecode

from ..utils import (
    _dataverse_dirname_quote,
    _dataverse_filename_quote,
    _dataverse_unquote,
    format_doi,
    mangle_path,
    unmangle_path
)


_test_paths = [
    lookup("dog face") + lookup("cat face"),
    ".x",
    "_x",
    "..x",
    "._x",
    "__x",
    "_.x",
    ".dir/.x",
    "_dir/_x",
    "..dir/..x",
    "._dir/._x",
    "_.dir/_.x",
    "__dir/__x",
    ".dir/x",
    "_dir/x",
    "..dir/x",
    "._dir/x",
    "_.dir/x",
    "__dir/x",
    "ä",
    "%%;;,_,?-&=",
]


def test_format_doi():
    assert format_doi('some') == 'doi:some'
    assert format_doi('doi:10.5072/FK2/WQCBX1') == 'doi:10.5072/FK2/WQCBX1'
    assert format_doi('http://doi.org/10.5072/FK2/WQCBX1') == 'doi:10.5072/FK2/WQCBX1'
    assert format_doi('https://doi.org/10.5072/FK2/WQCBX1') == 'doi:10.5072/FK2/WQCBX1'
    with pytest.raises(ValueError):
        format_doi(None)
    with pytest.raises(ValueError):
        format_doi('')
    with pytest.raises(TypeError):
        format_doi(123)


def _check_simplified_match(path, mangled_path):
    result = [
        True
        if mangled_part.startswith('__not_representable')
        else str(unmangle_path(mangled_part)) == unidecode(part)
        for mangled_part, part in zip(mangled_path.parts, path.parts)
    ]
    assert all(result)


def test_path_mangling_identity():
    for p in _test_paths + ['?;#:eee=2.txt']:
        _check_simplified_match(Path(p), mangle_path(p))


def test_path_mangling_sub_dirs():
    for p, q, r in product(_test_paths, _test_paths, _test_paths):
        path = Path(p) / q / r
        mangled_path = mangle_path(path)
        _check_simplified_match(path, mangled_path)


def test_file_quoting_identity():
    for p in ["x-/a-b", "._:*#?<>|;#", "x-/a"]:
        assert p == _dataverse_unquote(_dataverse_filename_quote(p))


def test_dir_quoting_leading_dot():
    for p in [".a", "..a", "_a", "_.a", "__a"]:
        q = _dataverse_dirname_quote(p)
        assert q[0] != "."
        assert p == _dataverse_unquote(q)
