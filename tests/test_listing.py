from dataclasses import FrozenInstanceError, fields
from inspect import signature
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from wheeltags.failure import Failure
from wheeltags.listing import Entry, Loaded, load_listing, parse_listing
from wheeltags.names import FileName
from wheeltags.streams import Io


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", []),
        (" \t\n# nothing\n", []),
        ("# café\x01\n\t pkg-1.0.tar.gz \r", [(2, "pkg-1.0.tar.gz")]),
        (
            "# l\n\npkg-1-py3-none-any.whl\r\npkg-2.tar.gz\n",
            [(3, "pkg-1-py3-none-any.whl"), (4, "pkg-2.tar.gz")],
        ),
        (
            "pkg-1.tar.gz\nPkg-1.tar.gz",
            [(1, "pkg-1.tar.gz"), (2, "Pkg-1.tar.gz")],
        ),
    ],
)
def test_listing_success_examples(text, expected):
    entries = parse_listing(text)
    assert [(entry.line, entry.name.text) for entry in entries] == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("\x01", 'WL001 unexpected character "?" at 1:1'),
        ("café\x01", 'WL001 unexpected character "?" at 1:5'),
        ("a😀\x01", 'WL001 unexpected character "?" at 1:3'),
        ("á\x01", 'WL001 unexpected character "?" at 1:3'),
        (
            "# c\n\npkg-1.0-py3-none-any.whl\r\r\n",
            'WL001 unexpected character "?" at 3:25',
        ),
        ("\tpkg\x01-1.0-py3-none-any.whl", 'WL001 unexpected character "?" at 1:5'),
        ("  pkg-1.0-py3 -none-any.whl", 'WL002 unexpected character " " at 1:14'),
        ("  \tcafé-1.0-py3-none-any.whl", 'WL002 unexpected character "?" at 1:7'),
        ("pkg-1.0-py3-none.whl   ", "WL004 wrong number of fields at 1:17"),
        ("# l\n\n\t-1.0-py3-none-any.whl", 'WL005 invalid name "" at 3:2'),
        ("\npkg-1.x.tar.gz", 'WL006 invalid version "1.x" at 2:5'),
        ("pkg-1.0-b1-py3-none-any.whl", 'WL007 invalid build "b1" at 1:9'),
        ("  pkg-1.0-py2.PY3-none-any.whl", 'WL008 invalid python tag "PY3" at 1:15'),
        ("pkg-1.0-py3-none-any.Win32.whl ", 'WL010 invalid platform tag "Win32" at 1:22'),
        (
            "pkg-1.0.tar.gz\n# x\npkg-1.0.tar.gz",
            'WL011 repeated file "pkg-1.0.tar.gz" at 3:1',
        ),
        (
            "pkg-1.tar.gz\n  pkg-1.tar.gz",
            'WL011 repeated file "pkg-1.tar.gz" at 2:3',
        ),
        ("pkg-1.tar.gz\x85", 'WL002 unexpected character "?" at 1:13'),
        ("pkg-1.tar.gz\u2028", 'WL002 unexpected character "?" at 1:13'),
        ("pkg-1.tar.gz\x0b", 'WL001 unexpected character "?" at 1:13'),
        ("pkg-1.tar.gz\x0c", 'WL001 unexpected character "?" at 1:13'),
        ("pkg-1.tar.gz\x7f", 'WL001 unexpected character "?" at 1:13'),
        ("pkg-1.tar.gz ", 'WL002 unexpected character "?" at 1:13'),
    ],
)
def test_listing_error_examples(text, expected):
    with pytest.raises(Failure) as error:
        parse_listing(text)
    assert str(error.value) == expected


def test_control_scan_precedes_name_validation_on_later_line():
    with pytest.raises(Failure) as error:
        parse_listing("# c\n\npkg-1.0-py3-none-any.whl\r\r\n")
    assert str(error.value) == 'WL001 unexpected character "?" at 3:25'


def test_empty_name_after_comment_and_blank_line_has_correct_column():
    with pytest.raises(Failure) as error:
        parse_listing("# l\n\n\t-1.0-py3-none-any.whl")
    assert str(error.value) == 'WL005 invalid name "" at 3:2'


@pytest.mark.parametrize(
    ("arg", "data", "file_error", "expected_entries", "expected_error"),
    [
        (
            "-",
            b"\xef\xbb\xbfpkg-1.tar.gz\n",
            False,
            [(1, "pkg-1.tar.gz")],
            None,
        ),
        ("x.txt", b"# nothing", False, [], '"x.txt": no entries'),
        (
            "bad.txt",
            b"# l\npkg-1.0-py3-none-any.whl\npkg-1.0-py3-none.whl",
            False,
            [],
            '"bad.txt": WL004 wrong number of fields at 3:17',
        ),
        ("missing.txt", b"", True, [], '"missing.txt": cannot read the file'),
        (
            "bad-utf8.txt",
            b"\x61\xff\x0a",
            False,
            [],
            '"bad-utf8.txt": input is not valid UTF-8',
        ),
    ],
)
def test_load_listing_reads_only_the_selected_in_memory_source(
    arg, data, file_error, expected_entries, expected_error
):
    read_stdin = Mock(return_value=data if arg == "-" else b"unused")
    read_file = Mock(return_value=data)
    if file_error:
        read_file.side_effect = OSError
    io = SimpleNamespace(read_stdin=read_stdin, read_file=read_file, out=Mock(), err=Mock())

    if expected_error is None:
        loaded = load_listing(io, arg)
        assert loaded.display == "<stdin>"
        assert [(entry.line, entry.name.text) for entry in loaded.entries] == expected_entries
    else:
        with pytest.raises(Failure) as error:
            load_listing(io, arg)
        assert str(error.value) == expected_error

    if arg == "-":
        read_stdin.assert_called_once_with()
        read_file.assert_not_called()
    else:
        read_file.assert_called_once_with(arg)
        read_stdin.assert_not_called()
    io.out.assert_not_called()
    io.err.assert_not_called()


def test_listing_records_and_public_signatures_are_frozen_and_exact():
    assert [field.name for field in fields(Entry)] == ["line", "name"]
    assert Entry.__annotations__ == {"line": int, "name": FileName}
    assert [field.name for field in fields(Loaded)] == ["display", "entries"]
    assert Loaded.__annotations__ == {"display": str, "entries": list[Entry]}

    parse_signature = signature(parse_listing)
    assert list(parse_signature.parameters) == ["text"]
    assert parse_signature.parameters["text"].annotation is str
    assert parse_signature.return_annotation == list[Entry]
    load_signature = signature(load_listing)
    assert list(load_signature.parameters) == ["io", "arg"]
    assert load_signature.parameters["io"].annotation is Io
    assert load_signature.parameters["arg"].annotation is str
    assert load_signature.return_annotation is Loaded

    entry = parse_listing("pkg-1.tar.gz")[0]
    loaded = Loaded(display='"memory.txt"', entries=[entry])
    with pytest.raises(FrozenInstanceError):
        entry.line = 2
    with pytest.raises(FrozenInstanceError):
        loaded.display = '"other.txt"'
