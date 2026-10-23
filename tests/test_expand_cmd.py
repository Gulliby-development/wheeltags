import pytest

from wheeltags.expand_cmd import SPECS, USAGE, run_expand
from wheeltags.failure import Failure
from wheeltags.options import Parsed, parse_options


class FakeIo:
    def __init__(self):
        self.writes = []

    def read_stdin(self):
        raise AssertionError("expand must not read standard input")

    def read_file(self, path):
        raise AssertionError(f"expand must not read {path!r}")

    def out(self, text):
        self.writes.append(("out", text))

    def err(self, text):
        self.writes.append(("err", text))


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ([], "missing TAGSET"),
        (["invalid text", "extra"], "too many arguments"),
        (["-", "extra"], "too many arguments"),
    ],
)
def test_arity_is_checked_before_tagset_text(args, expected):
    io = FakeIo()

    with pytest.raises(Failure) as caught:
        run_expand(args, Parsed(frozenset(), {}, []), io)

    assert str(caught.value) == expected
    assert io.writes == []


def test_contract_and_unknown_option_precedence():
    assert USAGE == "wheeltags expand TAGSET"
    assert SPECS == []
    io = FakeIo()

    with pytest.raises(Failure) as caught:
        parse_options(["--unknown"], SPECS)

    assert str(caught.value) == 'unknown option "--unknown"'
    assert io.writes == []


@pytest.mark.parametrize(
    ("tagset", "expected"),
    [
        (
            "cp311.cp312-abi3-win32.win_amd64",
            (
                "cp311-abi3-win32\n"
                "cp311-abi3-win_amd64\n"
                "cp312-abi3-win32\n"
                "cp312-abi3-win_amd64\n"
                "tags        4\n"
            ),
        ),
        ("py3-none-any", "py3-none-any\ntags        1\n"),
        ("py3.py3-none.none-any.any.any", "py3-none-any\ntags        1\n"),
        (
            "py3-abi3.none-win32.any",
            "py3-abi3-win32\npy3-abi3-any\npy3-none-win32\npy3-none-any\ntags        4\n",
        ),
        (
            "py2.py3-abi3.none-manylinux_2_17_x86_64.win_amd64",
            (
                "py2-abi3-manylinux_2_17_x86_64\n"
                "py2-abi3-win_amd64\n"
                "py2-none-manylinux_2_17_x86_64\n"
                "py2-none-win_amd64\n"
                "py3-abi3-manylinux_2_17_x86_64\n"
                "py3-abi3-win_amd64\n"
                "py3-none-manylinux_2_17_x86_64\n"
                "py3-none-win_amd64\n"
                "tags        8\n"
            ),
        ),
    ],
)
def test_expansion_output_examples(tagset, expected):
    io = FakeIo()

    actual = run_expand([tagset], Parsed(frozenset(), {}, [tagset]), io)

    assert actual == (expected, 0)
    assert io.writes == []


@pytest.mark.parametrize(
    ("tagset", "expected"),
    [
        ("", '"": WL004 wrong number of fields at column 1'),
        ("py3-none", '"py3-none": WL004 wrong number of fields at column 9'),
        (
            "py3-none-any-x",
            '"py3-none-any-x": WL004 wrong number of fields at column 14',
        ),
        (
            "py3..py2-none-any",
            '"py3..py2-none-any": WL008 invalid python tag "" at column 5',
        ),
        (
            "py3-none.-any",
            '"py3-none.-any": WL009 invalid abi tag "" at column 10',
        ),
        (
            "py3-none-any.Win32",
            '"py3-none-any.Win32": WL010 invalid platform tag "Win32" at column 14',
        ),
        (
            "py3-\t-any",
            '"py3-?-any": WL002 unexpected character "?" at column 5',
        ),
        (
            "py3-none-\x01",
            '"py3-none-?": WL002 unexpected character "?" at column 10',
        ),
        (
            "py3-none-😀",
            '"py3-none-?": WL002 unexpected character "?" at column 10',
        ),
        (
            "py3-none-e\u0301",
            '"py3-none-e?": WL002 unexpected character "?" at column 11',
        ),
        ("-", '"-": WL004 wrong number of fields at column 2'),
        ("x/y", '"x/y": WL004 wrong number of fields at column 4'),
    ],
)
def test_tagset_failures_are_prefixed_and_never_write(tagset, expected):
    io = FakeIo()

    with pytest.raises(Failure) as caught:
        run_expand([tagset], Parsed(frozenset(), {}, [tagset]), io)

    assert str(caught.value) == expected
    assert io.writes == []
