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


R1 = "1     cp34-abi3-win32\n"
R3 = "3     cp33-abi3-win32\n"
R4 = "4     cp32-abi3-win32\n"
HEADER = "RANK  TAG\n"


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["tags", "cp34:win32", "--abi", "abi3"], HEADER + R1 + R3 + R4 + "tags        3\n"),
        (
            ["tags", "cp34:win32", "--abi", "abi3", "--limit", "2"],
            HEADER + R1 + R3 + "tags        3\nshown       2\n",
        ),
        (
            ["tags", "cp34:win32", "--abi", "abi3", "--limit", "3"],
            HEADER + R1 + R3 + R4 + "tags        3\n",
        ),
        (
            ["tags", "cp34:win32", "--abi", "abi3", "--limit", "9999"],
            HEADER + R1 + R3 + R4 + "tags        3\n",
        ),
        (
            ["tags", "cp34:win32", "--abi=none", "--limit", "1"],
            HEADER + "2     cp34-none-win32\n" + "tags        14\nshown       1\n",
        ),
        (
            ["tags", "--limit=2", "cp312:win_amd64", "--abi=cp312"],
            HEADER + "0     cp312-cp312-win_amd64\n" + "tags        1\n",
        ),
        (
            ["tags", "cp312:win_amd64", "--abi", "abi3", "--limit", "4"],
            HEADER
            + "1     cp312-abi3-win_amd64\n"
            + "3     cp311-abi3-win_amd64\n"
            + "4     cp310-abi3-win_amd64\n"
            + "5     cp39-abi3-win_amd64\n"
            + "tags        11\nshown       4\n",
        ),
        (
            ["tags", "cp34:win32", "--abi", "cp34", "--limit", "1"],
            HEADER + "0     cp34-cp34-win32\n" + "tags        1\n",
        ),
    ],
)
def test_matches_keep_full_list_ranks(argv, expected):
    io = FakeIo()
    assert run(argv, io) == 0
    assert io.out_calls == [expected]
    assert io.err_calls == []


@pytest.mark.parametrize("name", ["cp312", "ABI3", "aaaaaaaaaaaaaaaaaaaa"])
def test_no_match_exits_one(name):
    io = FakeIo()
    assert run(["tags", "cp34:win32", "--abi", name], io) == 1
    assert io.out_calls == ["RANK  TAG\ntags        0\n"]
    assert io.err_calls == []


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (["tags", "cp34:win32", "--abi", ""], 'invalid abi ""'),
        (["tags", "cp34:win32", "--abi", "cp34-cp34"], 'invalid abi "cp34-cp34"'),
        (
            ["tags", "cp34:win32", "--abi", "aaaaaaaaaaaaaaaaaaaaa"],
            'invalid abi "aaaaaaaaaaaaaaaaaaaaa"',
        ),
        (["tags", "cp34:win32", "--abi", "\u00e9"], 'invalid abi "?"'),
        (["tags", "cp34:win32", "--abi"], "--abi needs a value"),
        (["tags", "cp34:win32", "--abi", "abi3", "--abi", "none"], "repeated option --abi"),
        (["tags", "nope", "--abi", "bad abi"], 'invalid target "nope"'),
        (["tags", "cp34:win32", "--abi", "bad abi", "--limit", "0"], 'invalid limit "0"'),
    ],
)
def test_errors_exit_two(argv, message):
    io = FakeIo()
    assert run(argv, io) == 2
    assert io.out_calls == []
    assert io.err_calls == [f"wheeltags: {message}\n"]
