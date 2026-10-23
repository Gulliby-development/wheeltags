import pytest

from wheeltags.failure import Failure
from wheeltags.options import Spec, parse_options
from wheeltags.pick_cmd import SPECS, USAGE, run_pick

_DIST_BYTES = (
    b"# pkg 2.1, built for the index\n"
    b"pkg-2.1-cp312-cp312-win_amd64.whl\n"
    b"pkg-2.1-1-cp312-cp312-win_amd64.whl\n"
    b"pkg-2.1-cp311-cp311-win_amd64.whl\n"
    b"pkg-2.1-cp39-abi3-win_amd64.whl\n"
    b"pkg-2.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl\n"
    b"pkg-2.1-py3-none-any.whl\n"
    b"pkg-2.1.0.tar.gz\n"
    b"pkg-2.0-cp312-cp312-win_amd64.whl\n"
)


class FakeIo:
    def __init__(self, files=None, stdin_bytes=b""):
        self.files = {} if files is None else files
        self.stdin_bytes = stdin_bytes
        self.reads = []
        self.out_calls = []
        self.err_calls = []

    def read_stdin(self):
        self.reads.append(("stdin", None))
        return self.stdin_bytes

    def read_file(self, path):
        self.reads.append(("file", path))
        if path not in self.files:
            raise OSError("not found")
        return self.files[path]

    def out(self, text):
        self.out_calls.append(text)

    def err(self, text):
        self.err_calls.append(text)


def test_exports_and_missing_arguments_do_not_read():
    assert USAGE == "wheeltags pick LISTING TARGET... [--all]"
    assert SPECS == [Spec("--all", False)]

    io = FakeIo()
    parsed = parse_options([], SPECS)
    with pytest.raises(Failure, match="^missing LISTING$"):
        run_pick(parsed.args, parsed, io)
    assert io.reads == []

    parsed = parse_options(["dist.txt"], SPECS)
    with pytest.raises(Failure, match="^missing TARGET$"):
        run_pick(parsed.args, parsed, io)
    assert io.reads == []
    assert io.out_calls == []
    assert io.err_calls == []


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["--all=1"], "--all takes no value"),
        (["--all", "--all"], "repeated option --all"),
        (["--abc"], 'unknown option "--abc"'),
    ],
)
def test_option_errors_precede_command_argument_checks(argv, expected):
    io = FakeIo()
    with pytest.raises(Failure) as raised:
        parsed = parse_options(argv, SPECS)
        run_pick(parsed.args, parsed, io)
    assert str(raised.value) == expected
    assert io.reads == []
    assert io.out_calls == []
    assert io.err_calls == []


@pytest.mark.parametrize(
    ("files", "argv", "expected"),
    [
        (
            {},
            ["nowhere.txt", "nope"],
            '"nowhere.txt": cannot read the file',
        ),
        (
            {"none.txt": b"# nothing\n"},
            ["none.txt", "nope"],
            '"none.txt": no entries',
        ),
        (
            {"bad.txt": (b"# l\npkg-1.0-py3-none-any.whl\npkg-1.0-py3-none.whl")},
            ["bad.txt", "nope"],
            '"bad.txt": WL004 wrong number of fields at 3:17',
        ),
    ],
)
def test_listing_read_and_full_parse_precede_target_validation(files, argv, expected):
    io = FakeIo(files)
    parsed = parse_options(argv, SPECS)
    with pytest.raises(Failure) as raised:
        run_pick(parsed.args, parsed, io)
    assert str(raised.value) == expected
    assert io.reads == [("file", argv[0])]
    assert io.out_calls == []
    assert io.err_calls == []


def test_targets_are_validated_left_to_right_after_listing_parse():
    io = FakeIo({"dist.txt": _DIST_BYTES})
    parsed = parse_options(["dist.txt", "cp312:win32", "nope1", "cp3:x"], SPECS)
    with pytest.raises(Failure, match='^invalid target "nope1"$'):
        run_pick(parsed.args, parsed, io)
    assert io.reads == [("file", "dist.txt")]
    assert io.out_calls == []
    assert io.err_calls == []


def test_stdin_listing_is_decoded_by_load_listing_and_read_only_once():
    io = FakeIo(stdin_bytes=b"pkg-1.0.tar.gz\n")
    parsed = parse_options(["-", "cp312:win32"], SPECS)
    output, status = run_pick(parsed.args, parsed, io)
    assert (output, status) == (
        (
            "TARGET       RANK   VERSION  FILE\n"
            'cp312:win32  sdist  1.0      "pkg-1.0.tar.gz"\n'
            "covered     1 of 1\n"
        ),
        0,
    )
    assert io.reads == [("stdin", None)]
    assert io.out_calls == []
    assert io.err_calls == []


def test_invalid_stdin_bytes_fail_before_target_validation():
    io = FakeIo(stdin_bytes=b"a\xff\n")
    parsed = parse_options(["-", "nope"], SPECS)
    with pytest.raises(Failure, match="^<stdin>: input is not valid UTF-8$"):
        run_pick(parsed.args, parsed, io)
    assert io.reads == [("stdin", None)]
    assert io.out_calls == []
    assert io.err_calls == []


def test_five_target_example_default_rows_are_literal():
    io = FakeIo({"dist.txt": _DIST_BYTES})
    parsed = parse_options(
        [
            "dist.txt",
            "cp312:win_amd64",
            "cp311:win_amd64",
            "cp310:win_amd64",
            "cp312:manylinux_2_28_x86_64",
            "cp313:macosx_14_0_arm64",
        ],
        SPECS,
    )
    output, status = run_pick(parsed.args, parsed, io)
    assert output == (
        "TARGET                       RANK  VERSION  FILE\n"
        'cp312:win_amd64              0     2.1      "pkg-2.1-1-cp312-cp312-win_amd64.whl"\n'
        'cp311:win_amd64              0     2.1      "pkg-2.1-cp311-cp311-win_amd64.whl"\n'
        'cp310:win_amd64              3     2.1      "pkg-2.1-cp39-abi3-win_amd64.whl"\n'
        'cp312:manylinux_2_28_x86_64  11    2.1      "pkg-2.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"\n'
        'cp313:macosx_14_0_arm64      611   2.1      "pkg-2.1-py3-none-any.whl"\n'
        "covered     5 of 5\n"
    )
    assert status == 0
    assert io.reads == [("file", "dist.txt")]
    assert io.out_calls == []
    assert io.err_calls == []


def test_all_candidates_example_preserves_choose_order_and_sdist_rank():
    io = FakeIo({"dist.txt": _DIST_BYTES})
    parsed = parse_options(["dist.txt", "cp312:win_amd64", "--all"], SPECS)
    output, status = run_pick(parsed.args, parsed, io)
    assert output == (
        "TARGET           RANK   VERSION  FILE\n"
        'cp312:win_amd64  0      2.1      "pkg-2.1-1-cp312-cp312-win_amd64.whl"\n'
        'cp312:win_amd64  0      2.1      "pkg-2.1-cp312-cp312-win_amd64.whl"\n'
        'cp312:win_amd64  5      2.1      "pkg-2.1-cp39-abi3-win_amd64.whl"\n'
        'cp312:win_amd64  29     2.1      "pkg-2.1-py3-none-any.whl"\n'
        'cp312:win_amd64  sdist  2.1.0    "pkg-2.1.0.tar.gz"\n'
        'cp312:win_amd64  0      2.0      "pkg-2.0-cp312-cp312-win_amd64.whl"\n'
        "covered     1 of 1\n"
    )
    assert status == 0
    assert io.reads == [("file", "dist.txt")]
    assert io.out_calls == []
    assert io.err_calls == []


@pytest.mark.parametrize("all_candidates", [False, True])
def test_missing_candidate_has_dash_row_and_status_one(all_candidates):
    io = FakeIo({"dist.txt": b"pkg-1.0-cp311-cp311-win_amd64.whl\n"})
    argv = ["dist.txt", "cp312:win_amd64"]
    if all_candidates:
        argv.append("--all")
    parsed = parse_options(argv, SPECS)
    output, status = run_pick(parsed.args, parsed, io)
    assert output == (
        "TARGET           RANK  VERSION  FILE\n"
        "cp312:win_amd64  -     -        -\n"
        "covered     0 of 1\n"
    )
    assert status == 1
    assert io.reads == [("file", "dist.txt")]
    assert io.out_calls == []
    assert io.err_calls == []


@pytest.mark.parametrize("all_candidates", [False, True])
def test_repeated_target_occurrences_remain_separate_and_counted(all_candidates):
    io = FakeIo({"dist.txt": b"pkg-1.0-cp311-cp311-win_amd64.whl\n"})
    argv = ["dist.txt", "cp311:win_amd64", "cp312:win_amd64", "cp311:win_amd64"]
    if all_candidates:
        argv.append("--all")
    parsed = parse_options(argv, SPECS)
    output, status = run_pick(parsed.args, parsed, io)
    assert output == (
        "TARGET           RANK  VERSION  FILE\n"
        'cp311:win_amd64  0     1.0      "pkg-1.0-cp311-cp311-win_amd64.whl"\n'
        "cp312:win_amd64  -     -        -\n"
        'cp311:win_amd64  0     1.0      "pkg-1.0-cp311-cp311-win_amd64.whl"\n'
        "covered     2 of 3\n"
    )
    assert status == 1
    assert io.reads == [("file", "dist.txt")]
    assert io.out_calls == []
    assert io.err_calls == []


def test_sdists_can_be_selected_as_best_for_compatible_and_incompatible_wheels():
    io = FakeIo(
        {"dist.txt": (b"pkg-1.0-cp312-cp312-win_amd64.whl\npkg-2.0.tar.gz\npkg-1.0.tar.gz\n")}
    )
    parsed = parse_options(["dist.txt", "cp312:win_amd64", "cp312:win32"], SPECS)
    output, status = run_pick(parsed.args, parsed, io)
    assert output == (
        "TARGET           RANK   VERSION  FILE\n"
        'cp312:win_amd64  sdist  2.0      "pkg-2.0.tar.gz"\n'
        'cp312:win32      sdist  2.0      "pkg-2.0.tar.gz"\n'
        "covered     2 of 2\n"
    )
    assert status == 0
    assert io.reads == [("file", "dist.txt")]
    assert io.out_calls == []
    assert io.err_calls == []


def test_all_candidates_orders_sdist_and_wheel_by_version_then_kind():
    io = FakeIo(
        {"dist.txt": (b"pkg-1.0-cp312-cp312-win_amd64.whl\npkg-2.0.tar.gz\npkg-1.0.tar.gz\n")}
    )
    parsed = parse_options(["dist.txt", "cp312:win_amd64", "--all"], SPECS)
    output, status = run_pick(parsed.args, parsed, io)
    assert output == (
        "TARGET           RANK   VERSION  FILE\n"
        'cp312:win_amd64  sdist  2.0      "pkg-2.0.tar.gz"\n'
        'cp312:win_amd64  0      1.0      "pkg-1.0-cp312-cp312-win_amd64.whl"\n'
        'cp312:win_amd64  sdist  1.0      "pkg-1.0.tar.gz"\n'
        "covered     1 of 1\n"
    )
    assert status == 0
    assert io.reads == [("file", "dist.txt")]
    assert io.out_calls == []
    assert io.err_calls == []
