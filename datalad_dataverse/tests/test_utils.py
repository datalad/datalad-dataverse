import unicodedata
import unicodedata
from itertools import product
from pathlib import PurePosixPath

import pytest

from ..utils import (
    _dataverse_dirname_quote,
    _dataverse_filename_quote,
    _dataverse_unquote,
    format_doi,
    mangle_path,
    unmangle_path
)


dog_cat = unicodedata.lookup('dog face') + unicodedata.lookup('cat face')


_test_paths = [
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
    "%%;;,_,?-&=",
    "?;#:eee=2.txt",
    "überfüllt",
    dog_cat
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


def test_path_mangling_identity():
    for p in _test_paths + ['?;#:eee=2.txt']:
        assert PurePosixPath(p) == unmangle_path(mangle_path(p))


def test_path_mangling_sub_dirs():
    for p, q, r in product(_test_paths, _test_paths, _test_paths):
        path = PurePosixPath(p) / q / r
        mangled_path = mangle_path(path)
        for part in mangled_path.parts[:-1]:
            assert part[0] != "."
        assert unmangle_path(mangled_path) == path


def test_file_quoting_identity():
    for p in ["x-/a-b", "._:*#?<>|;#", "x-/a"]:
        assert p == _dataverse_unquote(_dataverse_filename_quote(p))


def test_dir_quoting_leading_char():
    for p in [".a", "..a", "_a", "_.a", "__a", " a", "_ a", "-a", "- a", "-.a"]:
        q = _dataverse_dirname_quote(p)
        assert q[0] not in (".", "-", " ")
        assert p == _dataverse_unquote(q)


def test_unicode_quoting_leading_dot():
    for p in ["über", "\u20ac", "ööl-ins-feuäär", dog_cat]:
        q = _dataverse_dirname_quote(p)
        assert q[0] not in (".", "-", " ")
        assert p == _dataverse_unquote(q)
