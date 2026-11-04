"""Tests for tags --platform."""

import pytest

from wheeltags.cli import run


class FakeIo:
    def __init__(self):
        self.out_calls = []
        self.err_calls = []

    def read_stdin(self):
        raise AssertionError("unexpected read")

    def read_file(self, path):
        raise AssertionError("unexpected read")

    def out(self, text):
        self.out_calls.append(text)

    def err(self, text):
        self.err_calls.append(text)


HEADER = "RANK  TAG\n"
ANY = (
    "11    cp34-none-any\n"
    "12    py34-none-any\n"
    "13    py3-none-any\n"
    "14    py33-none-any\n"
    "15    py32-none-any\n"
    "16    py31-none-any\n"
    "17    py30-none-any\n"
)


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["tags", "cp34:win32", "--platform", "any"], HEADER + ANY + "tags        7\n"),
        (
            ["tags", "cp34:win32", "--platform", "any", "--limit", "2"],
            HEADER + "11    cp34-none-any\n12    py34-none-any\ntags        7\nshown       2\n",
        ),
        (
            ["tags", "cp34:win32", "--platform=win32", "--abi", "abi3"],
            HEADER
            + "1     cp34-abi3-win32\n3     cp33-abi3-win32\n4     cp32-abi3-win32\ntags        3\n",
        ),
        (
            ["tags", "cp34:win32", "--abi", "none", "--platform", "any", "--limit", "1"],
            HEADER + "11    cp34-none-any\ntags        7\nshown       1\n",
        ),
        (
            ["tags", "cp34:win32", "--platform", "win32", "--limit", "2"],
            HEADER
            + "0     cp34-cp34-win32\n1     cp34-abi3-win32\ntags        11\nshown       2\n",
        ),
    ],
)
def test_platform_keeps_full_list_ranks(argv, expected):
    io = FakeIo()
    assert run(argv, io) == 0
    assert io.out_calls == [expected]
    assert io.err_calls == []


@pytest.mark.parametrize("name", ["win_amd64", "WIN32", "a" * 40])
def test_no_match_exits_one(name):
    io = FakeIo()
    assert run(["tags", "cp34:win32", "--platform", name], io) == 1
    assert io.out_calls == ["RANK  TAG\ntags        0\n"]
    assert io.err_calls == []


def test_abi_and_platform_without_common_tag_exit_one():
    io = FakeIo()
    assert run(["tags", "cp34:win32", "--abi", "abi3", "--platform", "any"], io) == 1
    assert io.out_calls == ["RANK  TAG\ntags        0\n"]


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (["tags", "cp34:win32", "--platform", ""], 'invalid platform ""'),
        (["tags", "cp34:win32", "--platform", "win-32"], 'invalid platform "win-32"'),
        (["tags", "cp34:win32", "--platform", "a" * 41], 'invalid platform "' + "a" * 41 + '"'),
        (["tags", "cp34:win32", "--platform", "\u00e9"], 'invalid platform "?"'),
        (["tags", "cp34:win32", "--platform"], "--platform needs a value"),
        (
            ["tags", "cp34:win32", "--platform", "any", "--platform", "win32"],
            "repeated option --platform",
        ),
        (["tags", "nope", "--platform", "bad name"], 'invalid target "nope"'),
        (["tags", "cp34:win32", "--platform", "bad name", "--limit", "0"], 'invalid limit "0"'),
        (
            ["tags", "cp34:win32", "--abi", "bad abi", "--platform", "bad name"],
            'invalid abi "bad abi"',
        ),
    ],
)
def test_errors_exit_two(argv, message):
    io = FakeIo()
    assert run(argv, io) == 2
    assert io.out_calls == []
    assert io.err_calls == [f"wheeltags: {message}\n"]
