import pytest

from wheeltags.version import parse_build, parse_version


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2", (2, 0, 0, 0)),
        ("2.10", (2, 10, 0, 0)),
        ("1.0.0.1", (1, 0, 0, 1)),
        ("01.002", (1, 2, 0, 0)),
        ("999999999", (999999999, 0, 0, 0)),
        ("", None),
        ("1..2", None),
        ("1.2.3.4.5", None),
        ("1000000000", None),
        ("١", None),
        ("+1", None),
        ("1.", None),
    ],
)
def test_parse_version(text: str, expected: tuple[int, int, int, int] | None) -> None:
    assert parse_version(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("0", 0),
        ("0001", 1),
        ("999999999", 999999999),
        ("1000000000", None),
        ("", None),
        ("b1", None),
        ("-1", None),
        ("١", None),
    ],
)
def test_parse_build(text: str, expected: int | None) -> None:
    assert parse_build(text) == expected
