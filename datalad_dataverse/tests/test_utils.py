import pytest

from ..utils import format_doi


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
