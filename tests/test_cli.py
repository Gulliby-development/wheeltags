import importlib
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from wheeltags import cli, streams
from wheeltags.cli import HELP, run


class FakeIo:
    def __init__(self, files=None, unreadable=None, stdin_bytes=b""):
        self.files = {} if files is None else files
        self.unreadable = set() if unreadable is None else unreadable
        self.stdin_bytes = stdin_bytes
        self.reads = []
        self.out_calls = []
        self.err_calls = []

    def read_stdin(self):
        self.reads.append("-")
        return self.stdin_bytes

    def read_file(self, path):
        self.reads.append(path)
        if path in self.unreadable:
            raise OSError("unreadable")
        return self.files[path]

    def out(self, text):
        self.out_calls.append(text)

    def err(self, text):
        self.err_calls.append(text)


# BEGIN acceptance rows: host-written from the audited spec table. Edit acceptance_actual, not this block.
import json as _acceptance_json

import pytest as _acceptance_pytest

_ACCEPTANCE_ROWS = _acceptance_json.loads(
    '[{"id":"AC-002:1","input":[],"expected":{"code":2,"err":["wheeltags: missing command (tags, explain, pick, dead or expand)\\n"],"out":[]}},{"id":"AC-002:2","input":["fold","x"],"expected":{"code":2,"err":["wheeltags: unknown command \\"fold\\"\\n"],"out":[]}},{"id":"AC-002:3","input":["--help","x"],"expected":{"code":2,"err":["wheeltags: unknown command \\"--help\\"\\n"],"out":[]}},{"id":"AC-002:4","input":[""],"expected":{"code":2,"err":["wheeltags: unknown command \\"\\"\\n"],"out":[]}},{"id":"AC-002:5","input":["f😀"],"expected":{"code":2,"err":["wheeltags: unknown command \\"f?\\"\\n"],"out":[]}},{"id":"AC-002:6","input":["tags","cp312:win32","--abc"],"expected":{"code":2,"err":["wheeltags: unknown option \\"--abc\\"\\n"],"out":[]}},{"id":"AC-002:7","input":["pick","dist.txt","cp312:win32","--all=1"],"expected":{"code":2,"err":["wheeltags: --all takes no value\\n"],"out":[]}},{"id":"AC-002:8","input":["tags","cp312:win32","--limit"],"expected":{"code":2,"err":["wheeltags: --limit needs a value\\n"],"out":[]}},{"id":"AC-002:9","input":["tags","cp312:win32","--limit","2","--limit","3"],"expected":{"code":2,"err":["wheeltags: repeated option --limit\\n"],"out":[]}},{"id":"AC-002:10","input":["tags","nope","--limit"],"expected":{"code":2,"err":["wheeltags: --limit needs a value\\n"],"out":[]}},{"id":"AC-002:11","input":["tags"],"expected":{"code":2,"err":["wheeltags: missing TARGET\\n"],"out":[]}},{"id":"AC-002:12","input":["explain","pkg-1.0-py3-none-any.whl"],"expected":{"code":2,"err":["wheeltags: missing TARGET\\n"],"out":[]}},{"id":"AC-002:13","input":["expand"],"expected":{"code":2,"err":["wheeltags: missing TAGSET\\n"],"out":[]}},{"id":"AC-002:14","input":["expand","py3-none-any","extra"],"expected":{"code":2,"err":["wheeltags: too many arguments\\n"],"out":[]}},{"id":"AC-002:15","input":["tags","cp3","--limit","0"],"expected":{"code":2,"err":["wheeltags: invalid target \\"cp3\\"\\n"],"out":[]}},{"id":"AC-002:16","input":["explain","bad.whl","nope"],"expected":{"code":2,"err":["wheeltags: \\"bad.whl\\": WL004 wrong number of fields at column 4\\n"],"out":[]}},{"id":"AC-002:17","input":["expand","py3-none"],"expected":{"code":2,"err":["wheeltags: \\"py3-none\\": WL004 wrong number of fields at column 9\\n"],"out":[]}},{"id":"AC-002:18","input":["expand","py3-none-any","--help"],"expected":{"code":2,"err":["wheeltags: unknown option \\"--help\\"\\n"],"out":[]}}]'
)


@_acceptance_pytest.mark.parametrize(
    "row", _ACCEPTANCE_ROWS, ids=[row["id"] for row in _ACCEPTANCE_ROWS]
)
def test_acceptance_row(row):
    assert acceptance_actual(row["input"]) == row["expected"]


# END acceptance rows


def acceptance_actual(argv: list[str]) -> dict[str, object]:
    io = FakeIo()
    code = run(argv, io)
    assert io.reads == []
    return {"code": code, "out": io.out_calls, "err": io.err_calls}


def test_help_is_emitted_once_without_reads():
    io = FakeIo()
    assert run(["--help"], io) == 0
    assert HELP == (
        "usage: wheeltags tags TARGET [--limit N]\n"
        "       wheeltags explain FILE TARGET\n"
        "       wheeltags pick LISTING TARGET... [--all]\n"
        "       wheeltags dead LISTING TARGET...\n"
        "       wheeltags expand TAGSET\n"
    )
    assert io.out_calls == [HELP]
    assert io.err_calls == []
    assert io.reads == []


def test_successful_command_integrations():
    io = FakeIo()
    assert run(["tags", "cp34:win32", "--limit", "3"], io) == 0
    assert io.out_calls == [
        (
            "RANK  TAG\n"
            "0     cp34-cp34-win32\n"
            "1     cp34-abi3-win32\n"
            "2     cp34-none-win32\n"
            "tags        18\n"
            "shown       3\n"
        )
    ]
    assert io.err_calls == []
    assert io.reads == []

    io = FakeIo()
    assert run(["expand", "cp311.cp312-abi3-win32.win_amd64"], io) == 0
    assert io.out_calls == [
        (
            "cp311-abi3-win32\n"
            "cp311-abi3-win_amd64\n"
            "cp312-abi3-win32\n"
            "cp312-abi3-win_amd64\n"
            "tags        4\n"
        )
    ]
    assert io.err_calls == []
    assert io.reads == []

    io = FakeIo()
    assert run(["explain", "pkg-2.1-cp311-cp311-win_amd64.whl", "cp312:win_amd64"], io) == 1
    assert io.out_calls == [
        (
            'wheel       "pkg-2.1-cp311-cp311-win_amd64.whl"\n'
            "name        pkg\n"
            "version     2.1\n"
            "build       -\n"
            "target      cp312:win_amd64\n"
            "tags        1\n"
            "verdict     incompatible\n"
            "reason      cp311 with abi tag cp311 is not supported\n"
        )
    ]
    assert io.err_calls == []
    assert io.reads == []

    io = FakeIo({"dist.txt": b"pkg-1.0.tar.gz\n"})
    assert run(["pick", "dist.txt", "cp312:win_amd64", "--all"], io) == 0
    assert io.out_calls == [
        (
            "TARGET           RANK   VERSION  FILE\n"
            'cp312:win_amd64  sdist  1.0      "pkg-1.0.tar.gz"\n'
            "covered     1 of 1\n"
        )
    ]
    assert io.err_calls == []
    assert io.reads == ["dist.txt"]

    io = FakeIo({"dist.txt": b"pkg-1.0.tar.gz\n"})
    assert run(["dead", "dist.txt", "cp312:win_amd64"], io) == 0
    assert io.out_calls == ["unused      0 of 0\n"]
    assert io.err_calls == []
    assert io.reads == ["dist.txt"]


def test_listing_failures_precede_target_validation():
    io = FakeIo(unreadable={"nowhere.txt"})
    assert run(["pick", "nowhere.txt", "nope"], io) == 2
    assert io.out_calls == []
    assert io.err_calls == ['wheeltags: "nowhere.txt": cannot read the file\n']
    assert io.reads == ["nowhere.txt"]

    io = FakeIo({"bad.txt": b"# l\npkg-1.0-py3-none-any.whl\npkg-1.0-py3-none.whl\n"})
    assert run(["dead", "bad.txt", "nope"], io) == 2
    assert io.out_calls == []
    assert io.err_calls == ['wheeltags: "bad.txt": WL004 wrong number of fields at 3:17\n']
    assert io.reads == ["bad.txt"]


def test_importing_executable_does_not_call_run_or_construct_stdio(monkeypatch):
    run_mock = Mock()
    stdio_mock = Mock()
    with monkeypatch.context() as patch:
        patch.setattr(cli, "run", run_mock)
        patch.setattr(streams, "StdIo", stdio_mock)
        entrypoint = importlib.import_module("wheeltags.__main__")
        importlib.reload(entrypoint)
        assert run_mock.call_count == 0
        assert stdio_mock.call_count == 0
    importlib.reload(entrypoint)


def test_cli_does_not_catch_non_failure_exceptions(monkeypatch):
    runner = Mock(side_effect=RuntimeError("unexpected"))
    monkeypatch.setitem(cli.RUNNERS, "tags", runner)
    io = FakeIo()
    with pytest.raises(RuntimeError, match="unexpected"):
        run(["tags", "cp312:win32"], io)
    assert io.out_calls == []
    assert io.err_calls == []
    assert io.reads == []


def test_malformed_stdin_is_reported_by_executable():
    result = subprocess.run(
        [sys.executable, "-m", "wheeltags", "pick", "-", "cp312:win_amd64"],
        input=b"a\xff\n",
        check=False,
        capture_output=True,
        timeout=60,
        cwd=Path(__file__).resolve().parent.parent,
    )
    assert result.returncode == 2
    assert result.stdout == b""
    assert result.stderr == b"wheeltags: <stdin>: input is not valid UTF-8\n"
