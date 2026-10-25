from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "literal",
    [
        "## Install",
        "## Usage",
        "## Commands",
        "## Exit codes",
        "## Development",
        (
            "usage: wheeltags tags TARGET [--limit N] [--abi NAME]\n"
            "       wheeltags explain FILE TARGET\n"
            "       wheeltags pick LISTING TARGET... [--all]\n"
            "       wheeltags dead LISTING TARGET...\n"
            "       wheeltags expand TAGSET"
        ),
        (
            "# pkg 2.1, built for the index\n"
            "pkg-2.1-cp312-cp312-win_amd64.whl\n"
            "pkg-2.1-1-cp312-cp312-win_amd64.whl\n"
            "pkg-2.1-cp311-cp311-win_amd64.whl\n"
            "pkg-2.1-cp39-abi3-win_amd64.whl\n"
            "pkg-2.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl\n"
            "pkg-2.1-py3-none-any.whl\n"
            "pkg-2.1.0.tar.gz\n"
            "pkg-2.0-cp312-cp312-win_amd64.whl"
        ),
        (
            "TARGET                       RANK  VERSION  FILE\n"
            'cp312:win_amd64              0     2.1      "pkg-2.1-1-cp312-cp312-win_amd64.whl"\n'
            'cp311:win_amd64              0     2.1      "pkg-2.1-cp311-cp311-win_amd64.whl"\n'
            'cp310:win_amd64              3     2.1      "pkg-2.1-cp39-abi3-win_amd64.whl"\n'
            'cp312:manylinux_2_28_x86_64  11    2.1      "pkg-2.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"\n'
            'cp313:macosx_14_0_arm64      611   2.1      "pkg-2.1-py3-none-any.whl"\n'
            "covered     5 of 5"
        ),
    ],
)
def test_required_documentation_is_present(literal: str) -> None:
    readme_path = Path(__file__).resolve().parent.parent / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    assert literal in readme
