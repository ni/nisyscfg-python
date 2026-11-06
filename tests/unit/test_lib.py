from nisyscfg._lib import c_string_decode


def test_c_string_decode_preserves_null_and_empty_values() -> None:
    assert c_string_decode(None) is None
    assert c_string_decode(b"") == ""
    assert c_string_decode("") == ""
