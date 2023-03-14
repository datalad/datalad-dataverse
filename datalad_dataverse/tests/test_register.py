def test_register():
    import datalad.api as da
    assert hasattr(da, 'add_sibling_dataverse')
