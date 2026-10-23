from dataclasses import FrozenInstanceError, fields
from inspect import signature

import pytest

from wheeltags.names import FileName, parse_name
from wheeltags.tagsets import TagProblem


@pytest.mark.parametrize(
    ("text", "sdist_ok", "expected"),
    [
        (
            "Pkg_1.x-01.002-0000-py2.py3-none-any.whl",
            False,
            FileName(
                kind="wheel",
                text="Pkg_1.x-01.002-0000-py2.py3-none-any.whl",
                name="Pkg_1.x",
                version_text="01.002",
                version=(1, 2, 0, 0),
                build=0,
                pythons=["py2", "py3"],
                abis=["none"],
                platforms=["any"],
            ),
        ),
        (
            "pkg-2.1.0.tar.gz",
            True,
            FileName(
                kind="sdist",
                text="pkg-2.1.0.tar.gz",
                name="pkg",
                version_text="2.1.0",
                version=(2, 1, 0, 0),
                build=None,
                pythons=[],
                abis=[],
                platforms=[],
            ),
        ),
        (
            "pkg-2-py3-none-any.whl",
            True,
            FileName(
                kind="wheel",
                text="pkg-2-py3-none-any.whl",
                name="pkg",
                version_text="2",
                version=(2, 0, 0, 0),
                build=None,
                pythons=["py3"],
                abis=["none"],
                platforms=["any"],
            ),
        ),
    ],
)
def test_parse_name_records(text: str, sdist_ok: bool, expected: FileName) -> None:
    assert parse_name(text, sdist_ok) == expected


@pytest.mark.parametrize(
    ("text", "sdist_ok", "code", "problem", "column"),
    [
        ("", False, "WL003", "unknown file type", 1),
        ("a b.zip", False, "WL002", 'unexpected character " "', 2),
        (
            "café-1.0-py3-none-any.whl",
            False,
            "WL002",
            'unexpected character "?"',
            4,
        ),
        (
            "a😀-1.0-py3-none-any.whl",
            False,
            "WL002",
            'unexpected character "?"',
            2,
        ),
        (
            "pkg-1.0-py3-none-an😀.whl",
            False,
            "WL002",
            'unexpected character "?"',
            20,
        ),
        (
            "á-1-py3-none-any.whl",
            False,
            "WL002",
            'unexpected character "?"',
            2,
        ),
        ("pkg-1.0-py3-none.whl", False, "WL004", "wrong number of fields", 17),
        ("pkg-1.0-1-py3-none-any-x.whl", False, "WL004", "wrong number of fields", 24),
        ("-1.0-py3-none.whl", False, "WL004", "wrong number of fields", 14),
        ("-1.0-py3-none-any.whl", False, "WL005", 'invalid name ""', 1),
        ("_pkg-1-py3-none-any.whl", False, "WL005", 'invalid name "_pkg"', 1),
        ("pkg-1.x.tar.gz", True, "WL006", 'invalid version "1.x"', 5),
        ("pkg-1.0-b1-py3-none-any.whl", False, "WL007", 'invalid build "b1"', 9),
        (
            "pkg-1.0-py2.PY3-none-any.whl",
            False,
            "WL008",
            'invalid python tag "PY3"',
            13,
        ),
        (
            "pkg-1.0-py3-none.-any.whl",
            False,
            "WL009",
            'invalid abi tag ""',
            18,
        ),
        (
            "pkg-1.0-py3-none-any.Win32.whl",
            False,
            "WL010",
            'invalid platform tag "Win32"',
            22,
        ),
        ("pkg-1.0.tar.gz", False, "WL003", "unknown file type", 1),
        ("pkg.tar.gz", True, "WL004", "wrong number of fields", 4),
        ("pkg-1.0-2.tar.gz", True, "WL004", "wrong number of fields", 9),
    ],
)
def test_parse_name_diagnostics(
    text: str, sdist_ok: bool, code: str, problem: str, column: int
) -> None:
    with pytest.raises(TagProblem) as caught:
        parse_name(text, sdist_ok)

    assert caught.value.code == code
    assert caught.value.problem == problem
    assert caught.value.column == column
    assert str(caught.value) == f"{problem} at column {column}"


def test_file_name_public_contract() -> None:
    assert [item.name for item in fields(FileName)] == [
        "kind",
        "text",
        "name",
        "version_text",
        "version",
        "build",
        "pythons",
        "abis",
        "platforms",
    ]
    assert [item.type for item in fields(FileName)] == [
        str,
        str,
        str,
        str,
        tuple[int, int, int, int],
        int | None,
        list[str],
        list[str],
        list[str],
    ]
    parsed_signature = signature(parse_name)
    assert list(parsed_signature.parameters) == ["text", "sdist_ok"]
    assert parsed_signature.parameters["text"].annotation is str
    assert parsed_signature.parameters["sdist_ok"].annotation is bool
    assert parsed_signature.return_annotation is FileName
    assert FileName.__dataclass_params__.frozen


def test_file_name_rejects_field_reassignment() -> None:
    filename = FileName(
        kind="wheel",
        text="pkg-1-py3-none-any.whl",
        name="pkg",
        version_text="1",
        version=(1, 0, 0, 0),
        build=None,
        pythons=["py3"],
        abis=["none"],
        platforms=["any"],
    )

    with pytest.raises(FrozenInstanceError):
        filename.name = "other"
