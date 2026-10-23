from dataclasses import dataclass

from wheeltags.tagsets import TagProblem, check_chars, check_fields
from wheeltags.text import show
from wheeltags.version import parse_build, parse_version


@dataclass(frozen=True)
class FileName:
    kind: str
    text: str
    name: str
    version_text: str
    version: tuple[int, int, int, int]
    build: int | None
    pythons: list[str]
    abis: list[str]
    platforms: list[str]


def _field_columns(fields: list[str]) -> list[int]:
    columns: list[int] = []
    column = 1
    for field in fields:
        columns.append(column)
        column += len(field) + 1
    return columns


def _valid_name(name: str) -> bool:
    if not name or not ("a" <= name[0] <= "z" or "A" <= name[0] <= "Z" or "0" <= name[0] <= "9"):
        return False
    return all(
        "a" <= character <= "z"
        or "A" <= character <= "Z"
        or "0" <= character <= "9"
        or character in "_."
        for character in name[1:]
    )


def parse_name(text: str, sdist_ok: bool) -> FileName:
    """Parse a wheel or, when allowed, source archive filename."""
    check_chars(text)

    if text.endswith(".whl"):
        kind = "wheel"
        stem = text[:-4]
    elif sdist_ok and text.endswith(".tar.gz"):
        kind = "sdist"
        stem = text[:-7]
    else:
        raise TagProblem("WL003", "unknown file type", 1)

    fields = stem.split("-")
    columns = _field_columns(fields)

    if kind == "sdist":
        if len(fields) < 2:
            raise TagProblem("WL004", "wrong number of fields", len(stem) + 1)
        if len(fields) > 2:
            raise TagProblem("WL004", "wrong number of fields", columns[2])
        name, version_text = fields

        if not _valid_name(name):
            raise TagProblem("WL005", f"invalid name {show(name)}", columns[0])
        version = parse_version(version_text)
        if version is None:
            raise TagProblem("WL006", f"invalid version {show(version_text)}", columns[1])
        return FileName(
            kind="sdist",
            text=text,
            name=name,
            version_text=version_text,
            version=version,
            build=None,
            pythons=[],
            abis=[],
            platforms=[],
        )

    if len(fields) < 5:
        raise TagProblem("WL004", "wrong number of fields", len(stem) + 1)
    if len(fields) > 6:
        raise TagProblem("WL004", "wrong number of fields", columns[6])

    if len(fields) == 5:
        name, version_text, python_field, abi_field, platform_field = fields
        build_text = None
        tag_columns = columns[2:]
    else:
        name, version_text, build_text, python_field, abi_field, platform_field = fields
        tag_columns = columns[3:]

    if not _valid_name(name):
        raise TagProblem("WL005", f"invalid name {show(name)}", columns[0])

    version = parse_version(version_text)
    if version is None:
        raise TagProblem("WL006", f"invalid version {show(version_text)}", columns[1])

    build = None
    if build_text is not None:
        build = parse_build(build_text)
        if build is None:
            raise TagProblem("WL007", f"invalid build {show(build_text)}", columns[2])

    pythons, abis, platforms = check_fields([python_field, abi_field, platform_field], tag_columns)
    return FileName(
        kind="wheel",
        text=text,
        name=name,
        version_text=version_text,
        version=version,
        build=build,
        pythons=pythons,
        abis=abis,
        platforms=platforms,
    )
