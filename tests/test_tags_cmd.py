import pytest

from wheeltags.failure import Failure
from wheeltags.options import Parsed, Spec, parse_options
from wheeltags.tags_cmd import SPECS, USAGE, run_tags


class FakeIo:
    def read_stdin(self) -> bytes:
        raise AssertionError("tags must not read standard input")

    def read_file(self, path: str) -> bytes:
        raise AssertionError("tags must not read files")

    def out(self, text: str) -> None:
        raise AssertionError("tags must return output instead of writing it")

    def err(self, text: str) -> None:
        raise AssertionError("tags must return errors instead of writing them")


def acceptance_actual(input: list[str] | str) -> list[str | int] | str:
    io = FakeIo()
    try:
        if isinstance(input, str):
            parsed = Parsed(frozenset(), {"--limit": input}, ["cp34:win32"])
            output, code = run_tags(parsed.args, parsed, io)
        else:
            parsed = parse_options(input, SPECS)
            output, code = run_tags(parsed.args, parsed, io)
        return [output, code]
    except Failure as error:
        return str(error)


# BEGIN acceptance rows: host-written from the audited spec table. Edit acceptance_actual, not this block.
import json as _acceptance_json

import pytest as _acceptance_pytest

_ACCEPTANCE_ROWS = _acceptance_json.loads(
    '[{"id":"AC-002:1","input":["cp34:win32"],"expected":["RANK  TAG\\n0     cp34-cp34-win32\\n1     cp34-abi3-win32\\n2     cp34-none-win32\\n3     cp33-abi3-win32\\n4     cp32-abi3-win32\\n5     py34-none-win32\\n6     py3-none-win32\\n7     py33-none-win32\\n8     py32-none-win32\\n9     py31-none-win32\\n10    py30-none-win32\\n11    cp34-none-any\\n12    py34-none-any\\n13    py3-none-any\\n14    py33-none-any\\n15    py32-none-any\\n16    py31-none-any\\n17    py30-none-any\\ntags        18\\n",0]},{"id":"AC-002:2","input":["cp34:win32","--limit","3"],"expected":["RANK  TAG\\n0     cp34-cp34-win32\\n1     cp34-abi3-win32\\n2     cp34-none-win32\\ntags        18\\nshown       3\\n",0]},{"id":"AC-002:3","input":["cp34:win32","--limit=1"],"expected":["RANK  TAG\\n0     cp34-cp34-win32\\ntags        18\\nshown       1\\n",0]},{"id":"AC-002:4","input":["cp312:musllinux_1_1_x86_64","--limit","3"],"expected":["RANK  TAG\\n0     cp312-cp312-musllinux_1_1_x86_64\\n1     cp312-cp312-musllinux_1_0_x86_64\\n2     cp312-cp312-linux_x86_64\\ntags        96\\nshown       3\\n",0]},{"id":"AC-002:5","input":["cp312:manylinux2014_aarch64","--limit","4"],"expected":["RANK  TAG\\n0     cp312-cp312-manylinux_2_17_aarch64\\n1     cp312-cp312-manylinux2014_aarch64\\n2     cp312-cp312-linux_aarch64\\n3     cp312-abi3-manylinux_2_17_aarch64\\ntags        96\\nshown       4\\n",0]},{"id":"AC-004:1","input":[],"expected":"missing TARGET"},{"id":"AC-004:2","input":["nope","extra","--limit=0"],"expected":"too many arguments"},{"id":"AC-004:3","input":["--limit=0"],"expected":"missing TARGET"},{"id":"AC-004:4","input":["nope","--limit"],"expected":"--limit needs a value"},{"id":"AC-004:5","input":["cp312:win32","--abc"],"expected":"unknown option \\"--abc\\""},{"id":"AC-004:6","input":["cp312:win32","--limit","2","--limit","3"],"expected":"repeated option --limit"},{"id":"AC-004:7","input":["cp3","--limit","0"],"expected":"invalid target \\"cp3\\""},{"id":"AC-004:8","input":[""],"expected":"invalid target \\"\\""},{"id":"AC-004:9","input":[":win32","--limit=0"],"expected":"invalid python \\"\\""},{"id":"AC-004:10","input":["cp312:win32:x","--limit=0"],"expected":"invalid platform \\"win32:x\\""},{"id":"AC-004:11","input":["cp312:win😀"],"expected":"invalid platform \\"win?\\""},{"id":"AC-005:1","input":"","expected":"invalid limit \\"\\""},{"id":"AC-005:2","input":"0","expected":"invalid limit \\"0\\""},{"id":"AC-005:3","input":"01","expected":"invalid limit \\"01\\""},{"id":"AC-005:4","input":"10000","expected":"invalid limit \\"10000\\""},{"id":"AC-005:5","input":"-1","expected":"invalid limit \\"-1\\""},{"id":"AC-005:6","input":"+1","expected":"invalid limit \\"+1\\""},{"id":"AC-005:7","input":"1.0","expected":"invalid limit \\"1.0\\""},{"id":"AC-005:8","input":" 1","expected":"invalid limit \\" 1\\""},{"id":"AC-005:9","input":"1\\t","expected":"invalid limit \\"1?\\""},{"id":"AC-005:10","input":"١","expected":"invalid limit \\"?\\""}]'
)


@_acceptance_pytest.mark.parametrize(
    "row", _ACCEPTANCE_ROWS, ids=[row["id"] for row in _ACCEPTANCE_ROWS]
)
def test_acceptance_row(row):
    assert acceptance_actual(row["input"]) == row["expected"]


# END acceptance rows


_FULL_CP34_OUTPUT = (
    "RANK  TAG\n"
    "0     cp34-cp34-win32\n"
    "1     cp34-abi3-win32\n"
    "2     cp34-none-win32\n"
    "3     cp33-abi3-win32\n"
    "4     cp32-abi3-win32\n"
    "5     py34-none-win32\n"
    "6     py3-none-win32\n"
    "7     py33-none-win32\n"
    "8     py32-none-win32\n"
    "9     py31-none-win32\n"
    "10    py30-none-win32\n"
    "11    cp34-none-any\n"
    "12    py34-none-any\n"
    "13    py3-none-any\n"
    "14    py33-none-any\n"
    "15    py32-none-any\n"
    "16    py31-none-any\n"
    "17    py30-none-any\n"
    "tags        18\n"
)


def test_public_contract_and_returned_output() -> None:
    assert USAGE == "wheeltags tags TARGET [--limit N] [--abi NAME]"
    assert SPECS == [Spec("--limit", True), Spec("--abi", True)]

    parsed = Parsed(frozenset(), {}, ["cp34:win32"])
    output, code = run_tags(parsed.args, parsed, FakeIo())

    assert isinstance(output, str)
    assert code == 0


@pytest.mark.parametrize("limit", ["18", "19", "9999"])
def test_limits_at_or_above_tag_count_show_full_output(limit: str) -> None:
    parsed = Parsed(frozenset(), {"--limit": limit}, ["cp34:win32"])

    output, code = run_tags(parsed.args, parsed, FakeIo())

    assert [output, code] == [_FULL_CP34_OUTPUT, 0]


def test_target_failure_propagates_as_failure() -> None:
    parsed = Parsed(frozenset(), {}, ["cp3"])

    with pytest.raises(Failure) as caught:
        run_tags(parsed.args, parsed, FakeIo())

    assert str(caught.value) == 'invalid target "cp3"'
