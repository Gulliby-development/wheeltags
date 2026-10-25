<p align="center"><img src="docs/logo.svg" width="96" alt="" /></p>

# wheeltags

[![CI](https://github.com/Gulliby-development/wheeltags/actions/workflows/ci.yml/badge.svg)](https://github.com/Gulliby-development/wheeltags/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## What it is

wheeltags is an offline command-line tool for Python wheel builders, release maintainers and installers who need to know which wheel an installer would choose for a machine, which tags it supports, and why another wheel is skipped. It parses wheel filenames and compatibility tags; it never opens a wheel, contacts a package index, or makes a network request.

The application supports Python 3.11 or newer and uses only the Python standard library. It works on Windows, macOS and Linux.

## Install

Clone the repository (`git clone https://github.com/Gulliby-development/wheeltags.git`, then `cd wheeltags`) and use Python 3.11 or newer. There is no application dependency to install. Run commands from the repository root, where the `wheeltags` package folder is located.

Use a Python 3.11 or newer interpreter from the repository root. The examples below invoke the package as a module; if the `python` command does not select Python 3.11 or newer on your system, substitute the appropriate interpreter command. The project does not declare a separate `wheeltags` console-script executable.

## Usage

The help text lists the five command forms:

```text
usage: wheeltags tags TARGET [--limit N] [--abi NAME]
       wheeltags explain FILE TARGET
       wheeltags pick LISTING TARGET... [--all]
       wheeltags dead LISTING TARGET...
       wheeltags expand TAGSET
```

A target has the form `PYTHON:PLATFORM`, for example `cp312:win_amd64`. The Python component is a CPython version such as `cp312`; the platform component identifies a supported Windows, Linux, manylinux, musllinux or macOS platform. Each command validates its target before using it.

For `pick` and `dead`, `LISTING` is a text file containing one distribution filename per line; pass `-` to read the listing from standard input. Save the example listing below as `dist.txt` before using the pick and dead examples; it is documentation, not a file created by this project. `FILE` for `explain` and `TAGSET` for `expand` are filename/tag-set text arguments, not paths that the commands open.

The `tags` command emits a target's compatible tags in best-first order. `--limit N` restricts the displayed rows to the first `N` tags while the summary still reports the full count. Run this command to print the complete tag list for `cp34:win32`:

```console
python -m wheeltags tags cp34:win32
```

```text
RANK  TAG
0     cp34-cp34-win32
1     cp34-abi3-win32
2     cp34-none-win32
3     cp33-abi3-win32
4     cp32-abi3-win32
5     py34-none-win32
6     py3-none-win32
7     py33-none-win32
8     py32-none-win32
9     py31-none-win32
10    py30-none-win32
11    cp34-none-any
12    py34-none-any
13    py3-none-any
14    py33-none-any
15    py32-none-any
16    py31-none-any
17    py30-none-any
tags        18
```

`--abi NAME` keeps only the tags whose ABI part (the middle one of the three parts of a tag) is exactly `NAME`. Each row keeps its rank in the full list, `tags` counts the tags that matched, and `--limit` applies after the filter. When no tag matches, the command prints the header and `tags        0` and exits 1. For example:

```console
python -m wheeltags tags cp34:win32 --abi abi3 --limit 2
```

```text
RANK  TAG
1     cp34-abi3-win32
3     cp33-abi3-win32
tags        3
shown       2
```

Use `explain` to inspect one wheel filename against one target. Its report includes the wheel's name, version, build, number of tags and verdict, followed by the best matching tag and rank or an incompatibility reason. It checks the `FILE` argument as text and does not open it. Here is a compatible-wheel example:

```console
python -m wheeltags explain pkg-2.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl cp312:manylinux_2_28_x86_64
```

```text
wheel       "pkg-2.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"
name        pkg
version     2.1
build       -
target      cp312:manylinux_2_28_x86_64
tags        2
verdict     compatible
best        cp312-cp312-manylinux_2_17_x86_64 (rank 11 of 771)
```

`pick` selects the best candidate in a release listing for each target, preserving target order and repeated targets. A wheel's tags determine its compatibility rank. Candidates are ordered by higher version first, wheels before source distributions, lower (better) tag rank, higher build number, then earlier listing line. An unbuilt wheel ranks below every numbered build, including build 0. Use `--all` to show every candidate for each target instead of only the winner. The following is a nine-line example listing. Save the contents as `dist.txt` in the repository root for the examples that refer to that name:

```text
# pkg 2.1, built for the index
pkg-2.1-cp312-cp312-win_amd64.whl
pkg-2.1-1-cp312-cp312-win_amd64.whl
pkg-2.1-cp311-cp311-win_amd64.whl
pkg-2.1-cp39-abi3-win_amd64.whl
pkg-2.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
pkg-2.1-py3-none-any.whl
pkg-2.1.0.tar.gz
pkg-2.0-cp312-cp312-win_amd64.whl
```

The five-target command is `wheeltags pick dist.txt cp312:win_amd64 cp311:win_amd64 cp310:win_amd64 cp312:manylinux_2_28_x86_64 cp313:macosx_14_0_arm64`. Run its complete module invocation from the repository root as follows:

```console
python -m wheeltags pick dist.txt cp312:win_amd64 cp311:win_amd64 cp310:win_amd64 cp312:manylinux_2_28_x86_64 cp313:macosx_14_0_arm64
```

```text
TARGET                       RANK  VERSION  FILE
cp312:win_amd64              0     2.1      "pkg-2.1-1-cp312-cp312-win_amd64.whl"
cp311:win_amd64              0     2.1      "pkg-2.1-cp311-cp311-win_amd64.whl"
cp310:win_amd64              3     2.1      "pkg-2.1-cp39-abi3-win_amd64.whl"
cp312:manylinux_2_28_x86_64  11    2.1      "pkg-2.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"
cp313:macosx_14_0_arm64      611   2.1      "pkg-2.1-py3-none-any.whl"
covered     5 of 5
```

For a target's full candidate list, add `--all`; this is the example output:

```console
python -m wheeltags pick dist.txt cp312:win_amd64 --all
```

```text
TARGET           RANK   VERSION  FILE
cp312:win_amd64  0      2.1      "pkg-2.1-1-cp312-cp312-win_amd64.whl"
cp312:win_amd64  0      2.1      "pkg-2.1-cp312-cp312-win_amd64.whl"
cp312:win_amd64  5      2.1      "pkg-2.1-cp39-abi3-win_amd64.whl"
cp312:win_amd64  29     2.1      "pkg-2.1-py3-none-any.whl"
cp312:win_amd64  sdist  2.1.0    "pkg-2.1.0.tar.gz"
cp312:win_amd64  0      2.0      "pkg-2.0-cp312-cp312-win_amd64.whl"
covered     1 of 1
```

`dead` reports wheels in a listing that no requested target would select. It omits source distributions, and for a compatible but unused wheel it identifies the winning file and first target. Here is the output for two targets:

```console
python -m wheeltags dead dist.txt cp312:win_amd64 cp312:macosx_14_0_arm64
```

```text
LINE  FILE                                                                  REASON
2     "pkg-2.1-cp312-cp312-win_amd64.whl"                                   beaten by "pkg-2.1-1-cp312-cp312-win_amd64.whl" on cp312:win_amd64
4     "pkg-2.1-cp311-cp311-win_amd64.whl"                                   no compatible target
5     "pkg-2.1-cp39-abi3-win_amd64.whl"                                     beaten by "pkg-2.1-1-cp312-cp312-win_amd64.whl" on cp312:win_amd64
6     "pkg-2.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"  no compatible target
9     "pkg-2.0-cp312-cp312-win_amd64.whl"                                   beaten by "pkg-2.1-1-cp312-cp312-win_amd64.whl" on cp312:win_amd64
unused      5 of 7
```

`expand` expands a tag set into its unique tags in order, with Python tags outermost and platform tags innermost. The `TAGSET` argument is text and is not opened as a file. Here is an example:

```console
python -m wheeltags expand cp311.cp312-abi3-win32.win_amd64
```

```text
cp311-abi3-win32
cp311-abi3-win_amd64
cp312-abi3-win32
cp312-abi3-win_amd64
tags        4
```

## Commands

These are the exact command forms shown by `wheeltags --help`:

```text
usage: wheeltags tags TARGET [--limit N] [--abi NAME]
       wheeltags explain FILE TARGET
       wheeltags pick LISTING TARGET... [--all]
       wheeltags dead LISTING TARGET...
       wheeltags expand TAGSET
```

- `tags TARGET [--limit N] [--abi NAME]` lists accepted tags, best first; `N` must be a decimal limit from 1 to 9999 without a leading zero. `NAME` is 1 to 20 ASCII letters, digits or underscores and keeps only the tags whose ABI part equals it.
- `explain FILE TARGET` checks the wheel name text and explains compatibility.
- `pick LISTING TARGET... [--all]` chooses release files for one or more targets. A target with no candidate is shown as uncovered.
- `dead LISTING TARGET...` finds wheels that are not the first candidate for any requested target.
- `expand TAGSET` lists tags expanded from `PYTHON-ABI-PLATFORM` sets.

## Exit codes

- `0`: the command completed successfully; for `explain` the wheel is compatible, for `pick` every target is covered, and for `dead` there are no unused wheels.
- `1`: a negative result: `tags --abi` matched no tag, `explain` found an incompatible wheel, `pick` could not cover every target, or `dead` found at least one unused wheel.
- `2`: an input, option or file error. The command writes no standard output and reports one diagnostic line to standard error.

## Development

The package has no runtime dependencies. With Python 3.11 or newer and the development tools `ruff` and `pytest` available in the environment, run these commands from the repository root:

```console
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

Replace the initial `python` with `py -3.11` on Windows when needed.

## License

MIT, see [LICENSE](LICENSE).

---

Built with BAKED
