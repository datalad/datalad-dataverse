from itertools import product
from pathlib import Path

import pytest

from ..utils import (
    dataverse_filename_quote,
    dataverse_unquote,
    format_doi,
    mangle_directory_names,
    unmangle_directory_names
)


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
    "%%;;,_,?&=",
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


def test_dir_mangling_identity():
    for p in _test_paths:
        assert p == str(unmangle_directory_names(mangle_directory_names(p)))


def test_file_mangling_identity():
    for p in ["x/a", ".:*#?<>|;#"]:
        assert p == dataverse_unquote(dataverse_filename_quote(p))


def test_dir_mangling_sub_dirs():
    for p, q, r in product(_test_paths, _test_paths, _test_paths):
        path = Path(p) / q / r
        mangled_path = mangle_directory_names(path)
        for part in mangled_path.parts[:-1]:
            assert part[0] != "."
        assert str(unmangle_directory_names(mangled_path)) == str(path)
