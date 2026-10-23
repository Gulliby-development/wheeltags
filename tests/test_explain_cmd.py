# BEGIN acceptance rows: host-written from the audited spec table. Edit acceptance_actual, not this block.
import json as _acceptance_json

import pytest as _acceptance_pytest

_ACCEPTANCE_ROWS = _acceptance_json.loads(
    '[{"id":"AC-002:1","input":["pkg-2.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl","cp312:manylinux_2_28_x86_64"],"expected":["wheel       \\"pkg-2.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl\\"\\nname        pkg\\nversion     2.1\\nbuild       -\\ntarget      cp312:manylinux_2_28_x86_64\\ntags        2\\nverdict     compatible\\nbest        cp312-cp312-manylinux_2_17_x86_64 (rank 11 of 771)\\n",0]}]'
)


@_acceptance_pytest.mark.parametrize(
    "row", _ACCEPTANCE_ROWS, ids=[row["id"] for row in _ACCEPTANCE_ROWS]
)
def test_acceptance_row(row):
    assert acceptance_actual(row["input"]) == row["expected"]


# END acceptance rows


class FakeIo:
    def __init__(self):
        self.calls = []

    def read_stdin(self):
        self.calls.append("read_stdin")
        raise AssertionError("explain must not read standard input")

    def read_file(self, path):
        self.calls.append(("read_file", path))
        raise AssertionError("explain must not read files")

    def out(self, text):
        self.calls.append(("out", text))
        raise AssertionError("explain must not write standard output")

    def err(self, text):
        self.calls.append(("err", text))
        raise AssertionError("explain must not write standard error")


def acceptance_actual(input):
    from wheeltags.explain_cmd import SPECS, run_explain
    from wheeltags.options import parse_options

    parsed = parse_options(input, SPECS)
    io = FakeIo()
    output, status = run_explain(parsed.args, parsed, io)
    assert io.calls == []
    return [output, status]


def test_public_contract():
    import inspect

    from wheeltags.explain_cmd import SPECS, USAGE, run_explain
    from wheeltags.options import Parsed
    from wheeltags.streams import Io

    assert USAGE == "wheeltags explain FILE TARGET"
    assert SPECS == []
    assert type(SPECS) is list
    assert list(inspect.signature(run_explain).parameters) == ["args", "parsed", "io"]
    assert run_explain.__annotations__ == {
        "args": list[str],
        "parsed": Parsed,
        "io": Io,
        "return": tuple[str, int],
    }


@_acceptance_pytest.mark.parametrize(
    ("argv", "expected"),
    [
        ([], "missing FILE"),
        (["bad.whl"], "missing TARGET"),
        (["bad.whl", "nope", "extra"], "too many arguments"),
        (["--help"], 'unknown option "--help"'),
        (
            ["pkg-1.0.tar.gz", "cp312:win32"],
            '"pkg-1.0.tar.gz": WL003 unknown file type at column 1',
        ),
        (
            ["bad.whl", "nope"],
            '"bad.whl": WL004 wrong number of fields at column 4',
        ),
        (["-", "cp312:win32"], '"-": WL003 unknown file type at column 1'),
        (
            ["a😀-1.0-py3-none-any.whl", "nope"],
            '"a?-1.0-py3-none-any.whl": WL002 unexpected character "?" at column 2',
        ),
        (["pkg-1.0-py3-none-any.whl", "nope"], 'invalid target "nope"'),
        (["pkg-1.0-py3-none-any.whl", "cp31:win32"], 'invalid python "cp31"'),
        (["pkg-1.0-py3-none-any.whl", "cp312:"], 'invalid platform ""'),
    ],
)
def test_error_precedence(argv, expected):
    from wheeltags.failure import Failure

    with _acceptance_pytest.raises(Failure) as error:
        acceptance_actual(argv)
    assert str(error.value) == expected


@_acceptance_pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (
            ["pkg-1.0-py2.cp34-none-any.whl", "cp34:win32"],
            [0, "1.0", "-", "2", "compatible", "cp34-none-any (rank 11 of 18)"],
        ),
        (
            ["pkg-1.0-cp34-none.cp34-any.win32.whl", "cp34:win32"],
            [0, "1.0", "-", "4", "compatible", "cp34-cp34-win32 (rank 0 of 18)"],
        ),
        (
            ["pkg-1.0-0-py3.py3-none-any.any.whl", "cp34:win32"],
            [0, "1.0", "0", "1", "compatible", "py3-none-any (rank 13 of 18)"],
        ),
        (
            ["pkg-01.00-007-py3-none-any.whl", "cp34:win32"],
            [0, "01.00", "7", "1", "compatible", "py3-none-any (rank 13 of 18)"],
        ),
    ],
)
def test_expanded_matches_and_build_formatting(argv, expected):
    output, status = acceptance_actual(argv)
    rows = output.split("\n")
    actual = [status, rows[2][12:], rows[3][12:], rows[5][12:], rows[6][12:], rows[7][12:]]
    assert actual == expected
    assert rows[7].startswith("best        ")
    assert output.isascii()
    assert "\r" not in output
    assert not output.startswith("\ufeff")
    assert len(rows) == 9


@_acceptance_pytest.mark.parametrize(
    ("argv", "expected_reason"),
    [
        (
            ["pkg-1.0-py2.cp312-none-win32.whl", "cp312:win_amd64"],
            "python tag py2 is not supported",
        ),
        (
            ["pkg-2.1-cp311-cp311-win_amd64.whl", "cp312:win_amd64"],
            "cp311 with abi tag cp311 is not supported",
        ),
        (
            ["pkg-2.1-cp312-cp312-win32.whl", "cp312:win_amd64"],
            "platform tag win32 is not supported",
        ),
        (
            ["pkg-1.0-cp3-none-win32.whl", "cp34:win32"],
            "python tag cp3 is not supported",
        ),
        (
            ["pkg-1.0-cp34-abi.none-win_amd64.whl", "cp34:win32"],
            "cp34 with abi tag abi is not supported",
        ),
        (
            ["pkg-1.0-cp34-none-win_arm64.win_amd64.whl", "cp34:win32"],
            "platform tag win_arm64 is not supported",
        ),
    ],
)
def test_incompatible_reason_uses_first_components(argv, expected_reason):
    output, status = acceptance_actual(argv)
    rows = output.split("\n")
    assert status == 1
    assert rows[6] == "verdict     incompatible"
    assert rows[7] == f"reason      {expected_reason}"
    assert rows[7].startswith("reason      ")
    assert output.isascii()
    assert "\r" not in output
    assert not output.startswith("\ufeff")
    assert len(rows) == 9
