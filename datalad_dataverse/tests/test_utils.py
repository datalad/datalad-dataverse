from ..utils import format_doi


def test_format_doi():
    assert format_doi('some') == 'doi:some'
