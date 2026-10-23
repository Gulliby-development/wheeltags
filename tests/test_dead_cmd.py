import pytest

from wheeltags.dead_cmd import SPECS, USAGE, run_dead
from wheeltags.failure import Failure
from wheeltags.options import parse_options


class FakeIo:
    def __init__(self, files: dict[str, bytes] | None = None, stdin_bytes: bytes = b""):
        self.files = {} if files is None else files
        self.stdin_bytes = stdin_bytes
        self.file_reads: list[str] = []
        self.stdin_reads = 0
        self.output_writes: list[str] = []
        self.error_writes: list[str] = []

    def read_stdin(self) -> bytes:
        self.stdin_reads += 1
        return self.stdin_bytes

    def read_file(self, path: str) -> bytes:
        self.file_reads.append(path)
        if path not in self.files:
            raise OSError
        return self.files[path]

    def out(self, text: str) -> None:
        self.output_writes.append(text)

    def err(self, text: str) -> None:
        self.error_writes.append(text)


def test_exports_and_success_return_without_writes():
    assert USAGE == "wheeltags dead LISTING TARGET..."
    assert SPECS == []

    args = ["release.txt", "cp312:win32"]
    io = FakeIo({"release.txt": b"pkg-1.0-cp312-cp312-win32.whl\n"})
    parsed = parse_options(args, SPECS)

    assert run_dead(args, parsed, io) == ("unused      0 of 1\n", 0)
    assert io.file_reads == ["release.txt"]
    assert io.stdin_reads == 0
    assert io.output_writes == []
    assert io.error_writes == []


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ([], "missing LISTING"),
        (["nowhere.txt"], "missing TARGET"),
    ],
)
def test_missing_arguments_do_not_read_or_write(args, expected):
    io = FakeIo()
    parsed = parse_options(args, SPECS)

    with pytest.raises(Failure) as raised:
        run_dead(args, parsed, io)

    assert str(raised.value) == expected
    assert io.file_reads == []
    assert io.stdin_reads == 0
    assert io.output_writes == []
    assert io.error_writes == []


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (["--all"], 'unknown option "--all"'),
        (["--help"], 'unknown option "--help"'),
    ],
)
def test_unknown_options_precede_command_validation(args, expected):
    io = FakeIo()

    with pytest.raises(Failure) as raised:
        parsed = parse_options(args, SPECS)
        run_dead(parsed.args, parsed, io)

    assert str(raised.value) == expected
    assert io.file_reads == []
    assert io.stdin_reads == 0
    assert io.output_writes == []
    assert io.error_writes == []


@pytest.mark.parametrize(
    ("args", "files", "stdin_bytes", "expected", "expected_file_reads", "expected_stdin_reads"),
    [
        (
            ["nowhere.txt", "nope"],
            {},
            b"",
            '"nowhere.txt": cannot read the file',
            ["nowhere.txt"],
            0,
        ),
        (
            ["none.txt", "nope"],
            {"none.txt": b"# nothing"},
            b"",
            '"none.txt": no entries',
            ["none.txt"],
            0,
        ),
        (
            ["bad.txt", "cp312:win32"],
            {"bad.txt": (b"# l\npkg-1.0-py3-none-any.whl\npkg-1.0-py3-none.whl\n")},
            b"",
            '"bad.txt": WL004 wrong number of fields at 3:17',
            ["bad.txt"],
            0,
        ),
        (
            ["bad.txt", "nope"],
            {"bad.txt": (b"# l\npkg-1.0-py3-none-any.whl\npkg-1.0-py3-none.whl\n")},
            b"",
            '"bad.txt": WL004 wrong number of fields at 3:17',
            ["bad.txt"],
            0,
        ),
        (
            ["-", "nope"],
            {},
            b"a\xff\n",
            "<stdin>: input is not valid UTF-8",
            [],
            1,
        ),
    ],
)
def test_listing_errors_precede_target_validation(
    args, files, stdin_bytes, expected, expected_file_reads, expected_stdin_reads
):
    io = FakeIo(files, stdin_bytes)
    parsed = parse_options(args, SPECS)

    with pytest.raises(Failure) as raised:
        run_dead(args, parsed, io)

    assert str(raised.value) == expected
    assert io.file_reads == expected_file_reads
    assert io.stdin_reads == expected_stdin_reads
    assert io.output_writes == []
    assert io.error_writes == []


def test_targets_are_validated_left_to_right_after_loading():
    args = ["x.txt", "cp312:win32", "nope1", "cp3:x"]
    io = FakeIo({"x.txt": b"pkg-1.0-py3-none-any.whl\n"})
    parsed = parse_options(args, SPECS)

    with pytest.raises(Failure) as raised:
        run_dead(args, parsed, io)

    assert str(raised.value) == 'invalid target "nope1"'
    assert io.file_reads == ["x.txt"]
    assert io.stdin_reads == 0
    assert io.output_writes == []
    assert io.error_writes == []


def test_supplied_dead_example_has_literal_output():
    listing = (
        "# pkg 2.1, built for the index\n"
        "pkg-2.1-cp312-cp312-win_amd64.whl\n"
        "pkg-2.1-1-cp312-cp312-win_amd64.whl\n"
        "pkg-2.1-cp311-cp311-win_amd64.whl\n"
        "pkg-2.1-cp39-abi3-win_amd64.whl\n"
        "pkg-2.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl\n"
        "pkg-2.1-py3-none-any.whl\n"
        "pkg-2.1.0.tar.gz\n"
        "pkg-2.0-cp312-cp312-win_amd64.whl\n"
    )
    args = ["dist.txt", "cp312:win_amd64", "cp312:macosx_14_0_arm64"]
    io = FakeIo({"dist.txt": listing.encode("ascii")})
    parsed = parse_options(args, SPECS)

    expected = (
        "LINE  FILE                                                                  REASON\n"
        '2     "pkg-2.1-cp312-cp312-win_amd64.whl"                                   '
        'beaten by "pkg-2.1-1-cp312-cp312-win_amd64.whl" on cp312:win_amd64\n'
        '4     "pkg-2.1-cp311-cp311-win_amd64.whl"                                   '
        "no compatible target\n"
        '5     "pkg-2.1-cp39-abi3-win_amd64.whl"                                     '
        'beaten by "pkg-2.1-1-cp312-cp312-win_amd64.whl" on cp312:win_amd64\n'
        '6     "pkg-2.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"  '
        "no compatible target\n"
        '9     "pkg-2.0-cp312-cp312-win_amd64.whl"                                   '
        'beaten by "pkg-2.1-1-cp312-cp312-win_amd64.whl" on cp312:win_amd64\n'
        "unused      5 of 7\n"
    )

    assert run_dead(args, parsed, io) == (expected, 1)
    assert io.file_reads == ["dist.txt"]
    assert io.stdin_reads == 0
    assert io.output_writes == []
    assert io.error_writes == []
    assert expected.endswith("\n")
    assert "\r" not in expected
    assert "\n\n" not in expected


@pytest.mark.parametrize(
    ("listing", "targets", "expected", "status"),
    [
        (
            "pkg-1.0-py3-none-any.whl\npkg-2.0.tar.gz\n",
            ["cp312:win32"],
            (
                "LINE  FILE                        REASON\n"
                '1     "pkg-1.0-py3-none-any.whl"  '
                'beaten by "pkg-2.0.tar.gz" on cp312:win32\n'
                "unused      1 of 1\n"
            ),
            1,
        ),
        (
            "pkg-1.0-py3-none-any.whl\npkg-1.0-cp312-cp312-win32.whl\n",
            ["cp312:win32", "cp312:win_amd64"],
            "unused      0 of 2\n",
            0,
        ),
        (
            "pkg-1.0-cp312-cp312-win32.whl\npkg-2.0-cp312-cp312-win32.whl\n",
            ["cp312:win_amd64", "cp312:win32", "cp313:win32"],
            (
                "LINE  FILE                             REASON\n"
                '1     "pkg-1.0-cp312-cp312-win32.whl"  '
                'beaten by "pkg-2.0-cp312-cp312-win32.whl" on cp312:win32\n'
                "unused      1 of 2\n"
            ),
            1,
        ),
        (
            "pkg-1.0-py3-none-any.whl\npkg-2.0-py3-none-any.whl\n",
            ["cp312:win32", "cp312:win_amd64"],
            (
                "LINE  FILE                        REASON\n"
                '1     "pkg-1.0-py3-none-any.whl"  '
                'beaten by "pkg-2.0-py3-none-any.whl" on cp312:win32\n'
                "unused      1 of 2\n"
            ),
            1,
        ),
        (
            "pkg-1.0-py3-none-any.whl\npkg-2.0-py3-none-any.whl\n",
            ["cp312:win_amd64", "cp312:win32"],
            (
                "LINE  FILE                        REASON\n"
                '1     "pkg-1.0-py3-none-any.whl"  '
                'beaten by "pkg-2.0-py3-none-any.whl" on cp312:win_amd64\n'
                "unused      1 of 2\n"
            ),
            1,
        ),
        (
            "pkg-1.0-cp311-cp311-win_amd64.whl\n",
            ["cp312:win32", "cp312:win32"],
            (
                "LINE  FILE                                 REASON\n"
                '1     "pkg-1.0-cp311-cp311-win_amd64.whl"  '
                "no compatible target\n"
                "unused      1 of 1\n"
            ),
            1,
        ),
    ],
)
def test_dead_selection_and_reason_ordering(listing, targets, expected, status):
    args = ["release.txt", *targets]
    io = FakeIo({"release.txt": listing.encode("ascii")})
    parsed = parse_options(args, SPECS)

    assert run_dead(args, parsed, io) == (expected, status)
    assert io.file_reads == ["release.txt"]
    assert io.stdin_reads == 0
    assert io.output_writes == []
    assert io.error_writes == []
    assert expected.endswith("\n")
    assert "\r" not in expected
    assert "\n\n" not in expected


@pytest.mark.parametrize(
    ("listing", "expected", "status"),
    [
        ("pkg-1.0-py3-none-any.whl\n", "unused      0 of 1\n", 0),
        ("pkg-1.0.tar.gz\npkg-2.0.tar.gz\n", "unused      0 of 0\n", 0),
        (
            "# c\n\npkg-1.0-cp311-cp311-win_amd64.whl\n",
            (
                "LINE  FILE               "
                "                  REASON\n"
                '3     "pkg-1.0-cp311-cp311-win_amd64.whl"  '
                "no compatible target\n"
                "unused      1 of 1\n"
            ),
            1,
        ),
    ],
)
def test_empty_and_incompatible_listing_outputs(listing, expected, status):
    args = ["release.txt", "cp312:win32"]
    io = FakeIo({"release.txt": listing.encode("ascii")})
    parsed = parse_options(args, SPECS)

    assert run_dead(args, parsed, io) == (expected, status)
    assert io.file_reads == ["release.txt"]
    assert io.stdin_reads == 0
    assert io.output_writes == []
    assert io.error_writes == []
    assert expected.endswith("\n")
    assert "\r" not in expected
    assert "\n\n" not in expected


def test_stdin_only_success_uses_existing_reader_without_writes():
    args = ["-", "cp312:win32"]
    io = FakeIo(stdin_bytes=b"pkg-1.0-py3-none-any.whl\n")
    parsed = parse_options(args, SPECS)

    expected = "unused      0 of 1\n"
    assert run_dead(args, parsed, io) == (expected, 0)
    assert io.file_reads == []
    assert io.stdin_reads == 1
    assert io.output_writes == []
    assert io.error_writes == []
    assert expected.endswith("\n")
    assert "\r" not in expected
    assert "\n\n" not in expected


def test_single_compatible_wheel_is_all_used():
    args = ["release.txt", "cp312:win32"]
    io = FakeIo({"release.txt": b"pkg-1.0-py3-none-any.whl\n"})
    parsed = parse_options(args, SPECS)

    assert run_dead(args, parsed, io) == ("unused      0 of 1\n", 0)
    assert io.file_reads == ["release.txt"]
    assert io.stdin_reads == 0
    assert io.output_writes == []
    assert io.error_writes == []


def test_sdist_only_listing_counts_no_wheels():
    args = ["release.txt", "cp312:win32"]
    io = FakeIo({"release.txt": b"pkg-1.0.tar.gz\npkg-2.0.tar.gz\n"})
    parsed = parse_options(args, SPECS)

    assert run_dead(args, parsed, io) == ("unused      0 of 0\n", 0)
    assert io.file_reads == ["release.txt"]
    assert io.stdin_reads == 0
    assert io.output_writes == []
    assert io.error_writes == []


def test_skipped_lines_keep_original_wheel_line_number():
    args = ["release.txt", "cp312:win32"]
    io = FakeIo({"release.txt": b"# c\n\npkg-1.0-cp311-cp311-win_amd64.whl\n"})
    parsed = parse_options(args, SPECS)

    assert run_dead(args, parsed, io) == (
        (
            "LINE  FILE               "
            "                  REASON\n"
            '3     "pkg-1.0-cp311-cp311-win_amd64.whl"  '
            "no compatible target\n"
            "unused      1 of 1\n"
        ),
        1,
    )
    assert io.file_reads == ["release.txt"]
    assert io.stdin_reads == 0
    assert io.output_writes == []
    assert io.error_writes == []
