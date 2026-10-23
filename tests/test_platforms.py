# BEGIN acceptance rows: host-written from the audited spec table. Edit acceptance_actual, not this block.
import json as _acceptance_json

import pytest as _acceptance_pytest

_ACCEPTANCE_ROWS = _acceptance_json.loads(
    '[{"id":"AC-001:1","input":"win32","expected":["win32"]},{"id":"AC-001:2","input":"win_amd64","expected":["win_amd64"]},{"id":"AC-001:3","input":"win_arm64","expected":["win_arm64"]},{"id":"AC-001:4","input":"linux_x86_64","expected":["linux_x86_64"]},{"id":"AC-001:5","input":"linux_i686","expected":["linux_i686"]},{"id":"AC-001:6","input":"linux_aarch64","expected":["linux_aarch64"]},{"id":"AC-001:7","input":"linux_armv7l","expected":["linux_armv7l"]},{"id":"AC-001:8","input":"linux_ppc64le","expected":["linux_ppc64le"]},{"id":"AC-001:9","input":"linux_s390x","expected":["linux_s390x"]},{"id":"AC-001:10","input":"manylinux_2_4_x86_64","expected":["linux_x86_64"]},{"id":"AC-001:11","input":"manylinux_2_5_x86_64","expected":["manylinux_2_5_x86_64","manylinux1_x86_64","linux_x86_64"]},{"id":"AC-001:12","input":"manylinux1_i686","expected":["manylinux_2_5_i686","manylinux1_i686","linux_i686"]},{"id":"AC-001:13","input":"manylinux_2_12_aarch64","expected":["linux_aarch64"]},{"id":"AC-001:14","input":"manylinux2014_aarch64","expected":["manylinux_2_17_aarch64","manylinux2014_aarch64","linux_aarch64"]},{"id":"AC-001:15","input":"musllinux_1_0_s390x","expected":["musllinux_1_0_s390x","linux_s390x"]},{"id":"AC-001:16","input":"musllinux_1_1_x86_64","expected":["musllinux_1_1_x86_64","musllinux_1_0_x86_64","linux_x86_64"]},{"id":"AC-001:17","input":"macosx_10_5_x86_64","expected":["macosx_10_5_x86_64","macosx_10_5_universal2","macosx_10_4_x86_64","macosx_10_4_universal2"]},{"id":"AC-001:18","input":"macosx_11_0_arm64","expected":["macosx_11_0_arm64","macosx_11_0_universal2","macosx_10_16_universal2","macosx_10_15_universal2","macosx_10_14_universal2","macosx_10_13_universal2","macosx_10_12_universal2","macosx_10_11_universal2","macosx_10_10_universal2","macosx_10_9_universal2","macosx_10_8_universal2","macosx_10_7_universal2","macosx_10_6_universal2","macosx_10_5_universal2","macosx_10_4_universal2"]},{"id":"AC-002:1","input":"","expected":null},{"id":"AC-002:2","input":"Win32","expected":null},{"id":"AC-002:3","input":"win32\\t","expected":null},{"id":"AC-002:4","input":"linux_arm64","expected":null},{"id":"AC-002:5","input":"manylinux1_aarch64","expected":null},{"id":"AC-002:6","input":"manylinux2010_s390x","expected":null},{"id":"AC-002:7","input":"manylinux_2_07_x86_64","expected":null},{"id":"AC-002:8","input":"manylinux_2_100_x86_64","expected":null},{"id":"AC-002:9","input":"manylinux_2_١_x86_64","expected":null},{"id":"AC-002:10","input":"musllinux_1_00_i686","expected":null},{"id":"AC-002:11","input":"musllinux_2_1_x86_64","expected":null},{"id":"AC-002:12","input":"macosx_14_1_arm64","expected":null},{"id":"AC-002:13","input":"macosx_10_9_arm64","expected":null},{"id":"AC-002:14","input":"macosx_10_16_x86_64","expected":null},{"id":"AC-002:15","input":"macosx_10_3_x86_64","expected":null},{"id":"AC-002:16","input":"macosx_100_0_arm64","expected":null},{"id":"AC-002:17","input":"macosx_011_0_arm64","expected":null},{"id":"AC-002:18","input":"win32:x","expected":null}]'
)


@_acceptance_pytest.mark.parametrize(
    "row", _ACCEPTANCE_ROWS, ids=[row["id"] for row in _ACCEPTANCE_ROWS]
)
def test_acceptance_row(row):
    assert acceptance_actual(row["input"]) == row["expected"]


# END acceptance rows


def acceptance_actual(platform):
    from wheeltags.platforms import ladder

    return ladder(platform)


ladder = acceptance_actual


def test_linux_family_minima():
    assert ladder("manylinux_2_5_x86_64") == [
        "manylinux_2_5_x86_64",
        "manylinux1_x86_64",
        "linux_x86_64",
    ]
    assert ladder("manylinux_2_5_i686") == [
        "manylinux_2_5_i686",
        "manylinux1_i686",
        "linux_i686",
    ]
    assert ladder("manylinux_2_17_aarch64") == [
        "manylinux_2_17_aarch64",
        "manylinux2014_aarch64",
        "linux_aarch64",
    ]
    assert ladder("manylinux_2_17_armv7l") == [
        "manylinux_2_17_armv7l",
        "manylinux2014_armv7l",
        "linux_armv7l",
    ]
    assert ladder("manylinux_2_17_ppc64le") == [
        "manylinux_2_17_ppc64le",
        "manylinux2014_ppc64le",
        "linux_ppc64le",
    ]
    assert ladder("manylinux_2_17_s390x") == [
        "manylinux_2_17_s390x",
        "manylinux2014_s390x",
        "linux_s390x",
    ]


def test_numeric_boundaries_and_large_ladders():
    assert ladder("manylinux_2_0_x86_64") == ["linux_x86_64"]

    manylinux_99 = ladder("manylinux_2_99_x86_64")
    assert manylinux_99 is not None
    assert len(manylinux_99) == 99
    assert manylinux_99[0] == "manylinux_2_99_x86_64"
    assert manylinux_99[82:85] == [
        "manylinux_2_17_x86_64",
        "manylinux2014_x86_64",
        "manylinux_2_16_x86_64",
    ]
    assert manylinux_99[88:91] == [
        "manylinux_2_12_x86_64",
        "manylinux2010_x86_64",
        "manylinux_2_11_x86_64",
    ]
    assert manylinux_99[96:] == [
        "manylinux_2_5_x86_64",
        "manylinux1_x86_64",
        "linux_x86_64",
    ]

    musllinux_0 = ladder("musllinux_1_0_s390x")
    assert musllinux_0 == ["musllinux_1_0_s390x", "linux_s390x"]
    musllinux_99 = ladder("musllinux_1_99_i686")
    assert musllinux_99 is not None
    assert len(musllinux_99) == 101
    assert musllinux_99[0] == "musllinux_1_99_i686"
    assert musllinux_99[-2:] == ["musllinux_1_0_i686", "linux_i686"]


def test_manylinux_aliases_are_canonical_and_ordered():
    manylinux2014 = ladder("manylinux2014_x86_64")
    assert manylinux2014 is not None
    assert len(manylinux2014) == 17
    assert manylinux2014[:3] == [
        "manylinux_2_17_x86_64",
        "manylinux2014_x86_64",
        "manylinux_2_16_x86_64",
    ]
    assert manylinux2014[6:9] == [
        "manylinux_2_12_x86_64",
        "manylinux2010_x86_64",
        "manylinux_2_11_x86_64",
    ]
    assert manylinux2014[-3:] == [
        "manylinux_2_5_x86_64",
        "manylinux1_x86_64",
        "linux_x86_64",
    ]

    manylinux2010 = ladder("manylinux2010_i686")
    assert manylinux2010 == ladder("manylinux_2_12_i686")
    assert manylinux2010 is not None
    assert manylinux2010[:4] == [
        "manylinux_2_12_i686",
        "manylinux2010_i686",
        "manylinux_2_11_i686",
        "manylinux_2_10_i686",
    ]
    assert manylinux2010[-3:] == [
        "manylinux_2_5_i686",
        "manylinux1_i686",
        "linux_i686",
    ]
    assert ladder("manylinux1_x86_64") == ladder("manylinux_2_5_x86_64")


def test_macos_supported_boundaries_and_synthetic_version_order():
    assert ladder("macosx_10_4_x86_64") == [
        "macosx_10_4_x86_64",
        "macosx_10_4_universal2",
    ]

    macos_10_15 = ladder("macosx_10_15_x86_64")
    assert macos_10_15 is not None
    assert len(macos_10_15) == 24
    assert macos_10_15[:4] == [
        "macosx_10_15_x86_64",
        "macosx_10_15_universal2",
        "macosx_10_14_x86_64",
        "macosx_10_14_universal2",
    ]
    assert macos_10_15[-2:] == [
        "macosx_10_4_x86_64",
        "macosx_10_4_universal2",
    ]

    macos_99_x86 = ladder("macosx_99_0_x86_64")
    assert macos_99_x86 is not None
    assert len(macos_99_x86) == 204
    assert macos_99_x86[:2] == ["macosx_99_0_x86_64", "macosx_99_0_universal2"]
    assert macos_99_x86[178:180] == [
        "macosx_10_16_x86_64",
        "macosx_10_16_universal2",
    ]
    assert macos_99_x86[-2:] == [
        "macosx_10_4_x86_64",
        "macosx_10_4_universal2",
    ]

    macos_99_arm = ladder("macosx_99_0_arm64")
    assert macos_99_arm is not None
    assert len(macos_99_arm) == 191
    assert macos_99_arm[:2] == ["macosx_99_0_arm64", "macosx_99_0_universal2"]
    assert macos_99_arm[178:180] == [
        "macosx_10_16_universal2",
        "macosx_10_15_universal2",
    ]
    assert macos_99_arm[-1] == "macosx_10_4_universal2"
    assert ladder("macosx_11_0_x86_64")[:5] == [
        "macosx_11_0_x86_64",
        "macosx_11_0_universal2",
        "macosx_10_16_x86_64",
        "macosx_10_16_universal2",
        "macosx_10_15_x86_64",
    ]


def test_invalid_platform_grammar_boundaries():
    for platform in (
        "linux_x86_64_extra",
        "manylinux_2_100_x86_64",
        "manylinux_2_99_arm64",
        "manylinux_2_00_x86_64",
        "musllinux_1_100_x86_64",
        "macosx_100_0_x86_64",
        "macosx_99_1_arm64",
        "macosx_011_0_arm64",
        "win32:",
    ):
        assert ladder(platform) is None


def test_ladder_calls_are_repeatable():
    assert ladder("manylinux_2_18_ppc64le") == ladder("manylinux_2_18_ppc64le")
    assert ladder("macosx_14_0_arm64") == ladder("macosx_14_0_arm64")
