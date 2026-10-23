import builtins
import sys
from dataclasses import FrozenInstanceError, fields
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from wheeltags.failure import Failure
from wheeltags.options import Parsed, Spec, parse_options
from wheeltags.streams import StdIo, read_text


def test_failure_and_dataclass_contracts():
    assert issubclass(Failure, Exception)
    assert str(Failure("problem")) == "problem"
    assert [field.name for field in fields(Spec)] == ["name", "takes"]
    assert [field.name for field in fields(Parsed)] == ["flags", "values", "args"]

    spec = Spec("--all", False)
    parsed = Parsed(frozenset({"--all"}), {"--limit": "3"}, ["file"])
    assert Spec.__dataclass_params__.frozen
    assert Parsed.__dataclass_params__.frozen
    assert isinstance(parsed.flags, frozenset)
    assert isinstance(parsed.values, dict)
    assert isinstance(parsed.args, list)

    with pytest.raises(FrozenInstanceError):
        spec.name = "--other"
    with pytest.raises(FrozenInstanceError):
        parsed.args = []


@pytest.mark.parametrize(
    ("argv", "expected_flags", "expected_values", "expected_args"),
    [
        ([], frozenset(), {}, []),
        (["x"], frozenset(), {}, ["x"]),
        (["-", "-5", "x"], frozenset(), {}, ["-", "-5", "x"]),
        (["--all"], frozenset({"--all"}), {}, []),
        (["--limit=2"], frozenset(), {"--limit": "2"}, []),
        (["--limit="], frozenset(), {"--limit": ""}, []),
        (["--limit=a=b"], frozenset(), {"--limit": "a=b"}, []),
        (["--limit", "--all"], frozenset(), {"--limit": "--all"}, []),
        (["--limit", "-5"], frozenset(), {"--limit": "-5"}, []),
        (
            ["x", "--all", "y", "--limit=2"],
            frozenset({"--all"}),
            {"--limit": "2"},
            ["x", "y"],
        ),
        (
            ["--all", "x", "--limit", "3", "y"],
            frozenset({"--all"}),
            {"--limit": "3"},
            ["x", "y"],
        ),
        (["--limit", "3", "--all"], frozenset({"--all"}), {"--limit": "3"}, []),
        (["--all", "--limit=3"], frozenset({"--all"}), {"--limit": "3"}, []),
        (["plain", "--limit=3", "tail"], frozenset(), {"--limit": "3"}, ["plain", "tail"]),
        (["--limit=0"], frozenset(), {"--limit": "0"}, []),
        (["--limit=0001"], frozenset(), {"--limit": "0001"}, []),
        (["--limit=-1"], frozenset(), {"--limit": "-1"}, []),
        (["--limit", "--"], frozenset(), {"--limit": "--"}, []),
        (["--limit", "--help"], frozenset(), {"--limit": "--help"}, []),
        (["--limit", "-x"], frozenset(), {"--limit": "-x"}, []),
        (["--limit", "--limit=3"], frozenset(), {"--limit": "--limit=3"}, []),
        (["-"], frozenset(), {}, ["-"]),
        (["before", "--all", "after"], frozenset({"--all"}), {}, ["before", "after"]),
        (
            ["--all", "--limit", "3", "last"],
            frozenset({"--all"}),
            {"--limit": "3"},
            ["last"],
        ),
        (["--limit=x=y=z"], frozenset(), {"--limit": "x=y=z"}, []),
        (["--limit=="], frozenset(), {"--limit": "="}, []),
        (
            ["a", "--all", "b", "--limit=4", "c"],
            frozenset({"--all"}),
            {"--limit": "4"},
            ["a", "b", "c"],
        ),
        (["-abc", "-="], frozenset(), {}, ["-abc", "-="]),
        (["--limit", "2", "--all", "3"], frozenset({"--all"}), {"--limit": "2"}, ["3"]),
        (["x", "x"], frozenset(), {}, ["x", "x"]),
        (["--limit", ""], frozenset(), {"--limit": ""}, []),
        (["--limit=é😀"], frozenset(), {"--limit": "é😀"}, []),
        (
            ["--all", "middle", "--limit=9", "end"],
            frozenset({"--all"}),
            {"--limit": "9"},
            ["middle", "end"],
        ),
        (["--limit=5", "a", "-5", "b"], frozenset(), {"--limit": "5"}, ["a", "-5", "b"]),
        (["--limit", "a=b"], frozenset(), {"--limit": "a=b"}, []),
    ],
)
def test_parse_options_success(argv, expected_flags, expected_values, expected_args):
    parsed = parse_options(argv, [Spec("--all", False), Spec("--limit", True)])
    assert parsed.flags == expected_flags
    assert parsed.values == expected_values
    assert parsed.args == expected_args


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["--"], 'unknown option "--"'),
        (["--help"], 'unknown option "--help"'),
        (["--abc"], 'unknown option "--abc"'),
        (["--abc=😀"], 'unknown option "--abc=?"'),
        (["--all=1"], "--all takes no value"),
        (["--all="], "--all takes no value"),
        (["--limit"], "--limit needs a value"),
        (["--all", "--all"], "repeated option --all"),
        (["--limit=2", "--limit=3"], "repeated option --limit"),
        (["--limit", "2", "--limit"], "--limit needs a value"),
        (["--all", "--all=1"], "--all takes no value"),
        (["--all", "--all="], "--all takes no value"),
        (["nope", "--limit", "--abc", "--all=1"], "--all takes no value"),
        (["--limit", "2", "--limit=3"], "repeated option --limit"),
        (["--limit=1", "--limit"], "--limit needs a value"),
        (["--all", "--unknown"], 'unknown option "--unknown"'),
        (["--unknown", "--all=1"], 'unknown option "--unknown"'),
        (["--", "--limit=1"], 'unknown option "--"'),
        (["--bad😀"], 'unknown option "--bad?"'),
        (["--é"], 'unknown option "--?"'),
        (["--limit=1", "--abc"], 'unknown option "--abc"'),
        (["plain", "--all=0"], "--all takes no value"),
        (["--all=0", "--unknown"], "--all takes no value"),
        (["--limit=1", "--limit=2", "--all=1"], "repeated option --limit"),
        (["--all", "--all", "--limit"], "repeated option --all"),
        (["--limit", "1", "--limit", "2", "--limit"], "repeated option --limit"),
        (["--limit", "1", "--limit=2", "--limit=3"], "repeated option --limit"),
        (["--limit=", "--limit="], "repeated option --limit"),
        (["--all=x=y"], "--all takes no value"),
        (["--all", "--all=x=y"], "--all takes no value"),
        (["--limit=1", "middle", "--limit"], "--limit needs a value"),
        (["--limit", "x", "--limit"], "--limit needs a value"),
        (["--not-an-option="], 'unknown option "--not-an-option="'),
        (["--not-an-option", "value"], 'unknown option "--not-an-option"'),
        (["--all=😀"], "--all takes no value"),
        (["--limit", "x", "--missing"], 'unknown option "--missing"'),
        (["--limit", "x", "--all=1"], "--all takes no value"),
        (["--all", "--limit"], "--limit needs a value"),
    ],
)
def test_parse_options_errors(argv, expected):
    with pytest.raises(Failure) as raised:
        parse_options(argv, [Spec("--all", False), Spec("--limit", True)])
    assert str(raised.value) == expected


@pytest.mark.parametrize(
    ("arg", "stdin_bytes", "file_bytes", "expected_display", "expected_text"),
    [
        ("-", b"abc\n", b"ignored", "<stdin>", "abc\n"),
        ("-", b"", b"ignored", "<stdin>", ""),
        ("-", b"\xef\xbb\xbfabc", b"ignored", "<stdin>", "abc"),
        ("-", b"\xef\xbb\xbf\xef\xbb\xbfa", b"ignored", "<stdin>", "\ufeffa"),
        ("-", b"a\xef\xbb\xbf", b"ignored", "<stdin>", "a\ufeff"),
        ("-", b"\xc3\xa9\xf0\x9f\x98\x80", b"ignored", "<stdin>", "é😀"),
        ("-", b"first\r\nsecond\n", b"ignored", "<stdin>", "first\r\nsecond\n"),
        ("-", b"a\x00b", b"ignored", "<stdin>", "a\x00b"),
        ("-", b"\xc2\x85\xe2\x80\xa8\x0b\x0c", b"ignored", "<stdin>", "\u0085\u2028\v\f"),
        ("-", b"line\r", b"ignored", "<stdin>", "line\r"),
        ("x.txt", b"ignored", b"\xef\xbb\xbfabc\r\n", '"x.txt"', "abc\r\n"),
        ("x.txt", b"ignored", b"\xef\xbb\xbf\xef\xbb\xbfa", '"x.txt"', "\ufeffa"),
        ("x.txt", b"ignored", b"a\xef\xbb\xbf", '"x.txt"', "a\ufeff"),
        ("x.txt", b"ignored", b"", '"x.txt"', ""),
        ("x.txt", b"ignored", b"\xc3\xa9\xf0\x9f\x98\x80", '"x.txt"', "é😀"),
        ("x.txt", b"ignored", b"first\r\nsecond\n", '"x.txt"', "first\r\nsecond\n"),
        ("folder\\x.txt", b"ignored", b"contents", '"folder\\x.txt"', "contents"),
        ("a b.txt", b"ignored", b"contents", '"a b.txt"', "contents"),
        ("bad\x00path", b"ignored", b"contents", '"bad?path"', "contents"),
        ("surrogate\ud800path", b"ignored", b"contents", '"surrogate?path"', "contents"),
        ("x.txt", b"ignored", b"a\x00b", '"x.txt"', "a\x00b"),
        ("x.txt", b"ignored", b"\xef\xbb\xbf", '"x.txt"', ""),
        ("x.txt", b"ignored", b"\n", '"x.txt"', "\n"),
        ("x.txt", b"ignored", b"\r\n", '"x.txt"', "\r\n"),
        ("x.txt", b"ignored", b"\xf0\x9f\x8c\x8d", '"x.txt"', "🌍"),
    ],
)
def test_read_text_success(arg, stdin_bytes, file_bytes, expected_display, expected_text):
    io = SimpleNamespace(
        read_stdin=Mock(return_value=stdin_bytes),
        read_file=Mock(return_value=file_bytes),
    )
    assert read_text(io, arg) == (expected_display, expected_text)
    if arg == "-":
        io.read_stdin.assert_called_once_with()
        io.read_file.assert_not_called()
    else:
        io.read_file.assert_called_once_with(arg)
        io.read_stdin.assert_not_called()


@pytest.mark.parametrize(
    ("arg", "read_error", "expected"),
    [
        ("-", OSError, "<stdin>: cannot read the file"),
        ("nowhere.txt", OSError, '"nowhere.txt": cannot read the file'),
        ("a\x00b", ValueError, '"a?b": cannot read the file'),
        ("bad\ud800path", UnicodeError, '"bad?path": cannot read the file'),
    ],
)
def test_read_text_read_failures(arg, read_error, expected):
    io = SimpleNamespace(
        read_stdin=Mock(side_effect=read_error),
        read_file=Mock(side_effect=read_error),
    )
    with pytest.raises(Failure) as raised:
        read_text(io, arg)
    assert str(raised.value) == expected
    if arg == "-":
        io.read_stdin.assert_called_once_with()
        io.read_file.assert_not_called()
    else:
        io.read_file.assert_called_once_with(arg)
        io.read_stdin.assert_not_called()


@pytest.mark.parametrize(
    ("arg", "invalid_bytes", "expected"),
    [
        ("-", b"a\xff\n", "<stdin>: input is not valid UTF-8"),
        ("x.txt", b"\xc0\xaf", '"x.txt": input is not valid UTF-8'),
        ("x.txt", b"\xe2\x82", '"x.txt": input is not valid UTF-8'),
        ("-", b"\x80", "<stdin>: input is not valid UTF-8"),
        ("x.txt", b"\xed\xa0\x80", '"x.txt": input is not valid UTF-8'),
        ("x.txt", b"\xf4\x90\x80\x80", '"x.txt": input is not valid UTF-8'),
        ("-", b"\xe2\x28\xa1", "<stdin>: input is not valid UTF-8"),
        ("x.txt", b"\xf0\x9f", '"x.txt": input is not valid UTF-8'),
        ("-", b"\xc3", "<stdin>: input is not valid UTF-8"),
        ("x.txt", b"\xff", '"x.txt": input is not valid UTF-8'),
    ],
)
def test_read_text_invalid_utf8(arg, invalid_bytes, expected):
    io = SimpleNamespace(
        read_stdin=Mock(return_value=invalid_bytes),
        read_file=Mock(return_value=invalid_bytes),
    )
    with pytest.raises(Failure) as raised:
        read_text(io, arg)
    assert str(raised.value) == expected
    if arg == "-":
        io.read_stdin.assert_called_once_with()
        io.read_file.assert_not_called()
    else:
        io.read_file.assert_called_once_with(arg)
        io.read_stdin.assert_not_called()


def test_stdio_binary_io_and_explicit_file(monkeypatch):
    stdin_buffer = BytesIO(b"input\r\n")
    stdout_buffer = BytesIO()
    stderr_buffer = BytesIO()
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(buffer=stdin_buffer))
    monkeypatch.setattr(sys, "stdout", SimpleNamespace(buffer=stdout_buffer))
    monkeypatch.setattr(sys, "stderr", SimpleNamespace(buffer=stderr_buffer))

    opened_file = BytesIO(b"file bytes")
    open_mock = Mock(return_value=opened_file)
    monkeypatch.setattr(builtins, "open", open_mock)

    io = StdIo()
    assert io.read_stdin() == b"input\r\n"
    assert io.read_file("x.txt") == b"file bytes"
    open_mock.assert_called_once_with("x.txt", "rb")
    assert opened_file.closed

    io.out("a\n")
    io.err("error\n")
    assert stdout_buffer.getvalue() == b"a\n"
    assert stderr_buffer.getvalue() == b"error\n"


def test_stdio_unreadable_file_propagates_oserror(monkeypatch):
    open_mock = Mock(side_effect=OSError("denied"))
    monkeypatch.setattr(builtins, "open", open_mock)
    with pytest.raises(OSError):
        StdIo().read_file("x.txt")
    open_mock.assert_called_once_with("x.txt", "rb")
