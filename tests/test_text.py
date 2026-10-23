import importlib

# fmt: off
# BEGIN acceptance rows: host-written from the audited spec table. Edit acceptance_actual, not this block.
import json as _acceptance_json

import pytest as _acceptance_pytest

_ACCEPTANCE_ROWS = _acceptance_json.loads("[{\"id\":\"AC-005:1\",\"input\":[1,\"tag\"],\"expected\":\"1 tag\"},{\"id\":\"AC-005:2\",\"input\":[0,\"tag\"],\"expected\":\"0 tags\"},{\"id\":\"AC-005:3\",\"input\":[2,\"tag\"],\"expected\":\"2 tags\"}]")


@_acceptance_pytest.mark.parametrize("row", _ACCEPTANCE_ROWS, ids=[row["id"] for row in _ACCEPTANCE_ROWS])
def test_acceptance_row(row):
    assert acceptance_actual(row["input"]) == row["expected"]
# END acceptance rows
# fmt: on

_text = importlib.import_module("wheeltags.text")
line = _text.line
plural = _text.plural
show = _text.show
table = _text.table


def acceptance_actual(input):
    return plural(input[0], input[1])


@_acceptance_pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", '""'),
        ("abc ~", '"abc ~"'),
        ("\t\u007f\u0001é😀", '"?????"'),
        ("e\u0301", '"e?"'),
        ("\u0661\u00a0\u0085\u2028\u000b\u000c", '"??????"'),
        ('a"b\\c', '"a"b\\c"'),
    ],
)
def test_show(text, expected):
    assert show(text) == expected


@_acceptance_pytest.mark.parametrize(
    ("key", "value", "expected"),
    [
        ("tags", "18", "tags        18"),
        ("abcdefghijk", "x", "abcdefghijk  x"),
        ("😀", "x", "😀           x"),
    ],
)
def test_line(key, value, expected):
    assert line(key, value) == expected


@_acceptance_pytest.mark.parametrize(
    ("header", "rows", "expected"),
    [
        (["A", "B"], [["long", "x"], ["z", "yy"]], ["A     B", "long  x", "z     yy"]),
        (["HEAD", "B"], [], ["HEAD  B"]),
        (["A", "B"], [["x", ""]], ["A  B", "x"]),
        (["A", "B"], [["😀", "x"], ["e\u0301", "y"]], ["A   B", "😀   x", "e\u0301  y"]),
    ],
)
def test_table(header, rows, expected):
    assert table(header, rows) == expected
