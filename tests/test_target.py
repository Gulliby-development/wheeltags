# BEGIN acceptance rows: host-written from the audited spec table. Edit acceptance_actual, not this block.
import json as _acceptance_json

import pytest as _acceptance_pytest

_ACCEPTANCE_ROWS = _acceptance_json.loads(
    '[{"id":"AC-003:1","input":"cp32:win32","expected":{"minor":2,"platform":"win32","platforms":["win32"],"python":"cp32","text":"cp32:win32"}},{"id":"AC-003:2","input":"cp399:win_arm64","expected":{"minor":99,"platform":"win_arm64","platforms":["win_arm64"],"python":"cp399","text":"cp399:win_arm64"}},{"id":"AC-003:3","input":"cp312:manylinux2014_aarch64","expected":{"minor":12,"platform":"manylinux2014_aarch64","platforms":["manylinux_2_17_aarch64","manylinux2014_aarch64","linux_aarch64"],"python":"cp312","text":"cp312:manylinux2014_aarch64"}},{"id":"AC-003:4","input":"","expected":"invalid target \\"\\""},{"id":"AC-003:5","input":"cp312","expected":"invalid target \\"cp312\\""},{"id":"AC-003:6","input":":win32","expected":"invalid python \\"\\""},{"id":"AC-003:7","input":"cp31:win32","expected":"invalid python \\"cp31\\""},{"id":"AC-003:8","input":"cp302:win32","expected":"invalid python \\"cp302\\""},{"id":"AC-003:9","input":"cp3100:win32","expected":"invalid python \\"cp3100\\""},{"id":"AC-003:10","input":"cp3١2:win32","expected":"invalid python \\"cp3?2\\""},{"id":"AC-003:11","input":"cp3:x","expected":"invalid python \\"cp3\\""},{"id":"AC-003:12","input":"cp312:","expected":"invalid platform \\"\\""},{"id":"AC-003:13","input":"cp312:win32:x","expected":"invalid platform \\"win32:x\\""},{"id":"AC-003:14","input":"cp312:win😀","expected":"invalid platform \\"win?\\""},{"id":"AC-003:15","input":"cp312:win32\\t","expected":"invalid platform \\"win32?\\""}]'
)


@_acceptance_pytest.mark.parametrize(
    "row", _ACCEPTANCE_ROWS, ids=[row["id"] for row in _ACCEPTANCE_ROWS]
)
def test_acceptance_row(row):
    assert acceptance_actual(row["input"]) == row["expected"]


# END acceptance rows


def acceptance_actual(input_text):
    from wheeltags.failure import Failure
    from wheeltags.target import parse_target

    try:
        target = parse_target(input_text)
    except Failure as error:
        return str(error)
    return {
        "text": target.text,
        "python": target.python,
        "minor": target.minor,
        "platform": target.platform,
        "platforms": target.platforms,
    }


def test_complete_cp34_win32_tag_list():
    from wheeltags.target import parse_target, target_tags

    assert target_tags(parse_target("cp34:win32")) == [
        "cp34-cp34-win32",
        "cp34-abi3-win32",
        "cp34-none-win32",
        "cp33-abi3-win32",
        "cp32-abi3-win32",
        "py34-none-win32",
        "py3-none-win32",
        "py33-none-win32",
        "py32-none-win32",
        "py31-none-win32",
        "py30-none-win32",
        "cp34-none-any",
        "py34-none-any",
        "py3-none-any",
        "py33-none-any",
        "py32-none-any",
        "py31-none-any",
        "py30-none-any",
    ]


@_acceptance_pytest.mark.parametrize(
    ("target_text", "count", "ranked_tags"),
    [
        (
            "cp312:musllinux_1_1_x86_64",
            96,
            [
                (0, "cp312-cp312-musllinux_1_1_x86_64"),
                (1, "cp312-cp312-musllinux_1_0_x86_64"),
                (2, "cp312-cp312-linux_x86_64"),
            ],
        ),
        (
            "cp312:manylinux_2_28_x86_64",
            771,
            [(11, "cp312-cp312-manylinux_2_17_x86_64")],
        ),
        (
            "cp313:macosx_14_0_arm64",
            625,
            [(611, "py3-none-any")],
        ),
        (
            "cp312:win_amd64",
            42,
            [
                (5, "cp39-abi3-win_amd64"),
                (29, "py3-none-any"),
            ],
        ),
        (
            "cp312:manylinux2014_aarch64",
            96,
            [
                (0, "cp312-cp312-manylinux_2_17_aarch64"),
                (1, "cp312-cp312-manylinux2014_aarch64"),
                (2, "cp312-cp312-linux_aarch64"),
                (3, "cp312-abi3-manylinux_2_17_aarch64"),
            ],
        ),
    ],
)
def test_acceptance_tag_count_and_rank_anchors(target_text, count, ranked_tags):
    from wheeltags.target import parse_target, target_tags

    tags = target_tags(parse_target(target_text))
    assert len(tags) == count
    assert [(rank, tags[rank]) for rank, _ in ranked_tags] == ranked_tags


@_acceptance_pytest.mark.parametrize(
    ("target_text", "count", "ranked_tags"),
    [
        (
            "cp32:win32",
            12,
            [
                (0, "cp32-cp32-win32"),
                (1, "cp32-abi3-win32"),
                (2, "cp32-none-win32"),
                (3, "py32-none-win32"),
                (6, "py30-none-win32"),
                (7, "cp32-none-any"),
                (11, "py30-none-any"),
            ],
        ),
        (
            "cp399:win32",
            303,
            [
                (0, "cp399-cp399-win32"),
                (3, "cp398-abi3-win32"),
                (99, "cp32-abi3-win32"),
                (100, "py399-none-win32"),
                (101, "py3-none-win32"),
                (102, "py398-none-win32"),
                (200, "py30-none-win32"),
                (201, "cp399-none-any"),
                (202, "py399-none-any"),
                (302, "py30-none-any"),
            ],
        ),
    ],
)
def test_python_minor_boundary_counts_and_positions(target_text, count, ranked_tags):
    from wheeltags.target import parse_target, target_tags

    tags = target_tags(parse_target(target_text))
    assert len(tags) == count
    assert [(rank, tags[rank]) for rank, _ in ranked_tags] == ranked_tags


def test_manylinux2010_spelling_is_preserved():
    from wheeltags.target import parse_target

    target = parse_target("cp312:manylinux2010_x86_64")
    assert target.text == "cp312:manylinux2010_x86_64"
    assert target.python == "cp312"
    assert target.minor == 12
    assert target.platform == "manylinux2010_x86_64"
    assert target.platforms == [
        "manylinux_2_12_x86_64",
        "manylinux2010_x86_64",
        "manylinux_2_11_x86_64",
        "manylinux_2_10_x86_64",
        "manylinux_2_9_x86_64",
        "manylinux_2_8_x86_64",
        "manylinux_2_7_x86_64",
        "manylinux_2_6_x86_64",
        "manylinux_2_5_x86_64",
        "manylinux1_x86_64",
        "linux_x86_64",
    ]


def test_macos_stages_are_ordered_unique_and_repeatable():
    from wheeltags.target import parse_target, target_tags

    target = parse_target("cp34:macosx_10_5_x86_64")
    tags = target_tags(target)
    assert target.platforms == [
        "macosx_10_5_x86_64",
        "macosx_10_5_universal2",
        "macosx_10_4_x86_64",
        "macosx_10_4_universal2",
    ]
    assert len(tags) == 51
    assert len(tags) == len(set(tags))
    assert [(rank, tags[rank]) for rank in (0, 3, 4, 7, 8, 11, 12, 16, 20, 24, 40, 44, 45, 50)] == [
        (0, "cp34-cp34-macosx_10_5_x86_64"),
        (3, "cp34-cp34-macosx_10_4_universal2"),
        (4, "cp34-abi3-macosx_10_5_x86_64"),
        (7, "cp34-abi3-macosx_10_4_universal2"),
        (8, "cp34-none-macosx_10_5_x86_64"),
        (11, "cp34-none-macosx_10_4_universal2"),
        (12, "cp33-abi3-macosx_10_5_x86_64"),
        (16, "cp32-abi3-macosx_10_5_x86_64"),
        (20, "py34-none-macosx_10_5_x86_64"),
        (24, "py3-none-macosx_10_5_x86_64"),
        (40, "py30-none-macosx_10_5_x86_64"),
        (44, "cp34-none-any"),
        (45, "py34-none-any"),
        (50, "py30-none-any"),
    ]
    assert target_tags(target) == tags


def test_target_fields_are_frozen():
    from dataclasses import FrozenInstanceError

    from wheeltags.target import parse_target

    target = parse_target("cp312:win32")
    with _acceptance_pytest.raises(FrozenInstanceError):
        target.text = "cp399:win32"
