import pytest

from wheeltags.failure import Failure
from wheeltags.tagsets import TagProblem, check_chars, check_fields, expand_tags, parse_tagset


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("py2.py3-none-any", (["py2", "py3"], ["none"], ["any"])),
        ("py9-whatever_1-any", (["py9"], ["whatever_1"], ["any"])),
        ("", ("WL004", "wrong number of fields", 1, "wrong number of fields at column 1")),
        (
            "py3-none",
            ("WL004", "wrong number of fields", 9, "wrong number of fields at column 9"),
        ),
        (
            "py3-none-any-x",
            ("WL004", "wrong number of fields", 14, "wrong number of fields at column 14"),
        ),
        (
            "py3..py2-none-any",
            ("WL008", 'invalid python tag ""', 5, 'invalid python tag "" at column 5'),
        ),
        (
            "py3-\t-any",
            ("WL002", 'unexpected character "?"', 5, 'unexpected character "?" at column 5'),
        ),
        (
            "py3-none.-any",
            ("WL009", 'invalid abi tag ""', 10, 'invalid abi tag "" at column 10'),
        ),
        (
            "py3-none-any.Win32",
            (
                "WL010",
                'invalid platform tag "Win32"',
                14,
                'invalid platform tag "Win32" at column 14',
            ),
        ),
    ],
)
def test_parse_tagset_examples(text, expected):
    try:
        actual = parse_tagset(text)
    except TagProblem as error:
        assert (error.code, error.problem, error.column, str(error)) == expected
    else:
        assert actual == expected


@pytest.mark.parametrize(
    ("pythons", "abis", "platforms", "expected"),
    [
        (
            ["cp311", "cp312"],
            ["abi3"],
            ["win32", "win_amd64"],
            [
                "cp311-abi3-win32",
                "cp311-abi3-win_amd64",
                "cp312-abi3-win32",
                "cp312-abi3-win_amd64",
            ],
        ),
        (
            ["py3", "py3", "py2"],
            ["none", "none"],
            ["any", "any"],
            ["py3-none-any", "py2-none-any"],
        ),
        (
            ["py3"],
            ["abi3", "none"],
            ["win32", "any"],
            ["py3-abi3-win32", "py3-abi3-any", "py3-none-win32", "py3-none-any"],
        ),
        ([], ["none"], ["any"], []),
    ],
)
def test_expand_tags_examples(pythons, abis, platforms, expected):
    assert expand_tags(pythons, abis, platforms) == expected


def test_tag_problem_contracts():
    assert issubclass(TagProblem, Failure)
    assert check_chars("py3-none-any") is None
    assert check_fields(["py3", "none", "any"], [1, 5, 10]) == (
        ["py3"],
        ["none"],
        ["any"],
    )

    with pytest.raises(TagProblem) as caught:
        check_fields(["py3", "none.", "any"], [10, 20, 30])

    error = caught.value
    assert (error.code, error.problem, error.column) == ("WL009", 'invalid abi tag ""', 25)
    assert str(error) == 'invalid abi tag "" at column 25'
