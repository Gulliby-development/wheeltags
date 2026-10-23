from dataclasses import dataclass

from wheeltags.failure import Failure
from wheeltags.names import FileName, parse_name
from wheeltags.streams import Io, read_text
from wheeltags.tagsets import TagProblem
from wheeltags.text import show


@dataclass(frozen=True)
class Entry:
    line: int
    name: FileName


def _is_blank(character: str) -> bool:
    return character == " " or character == "\t"


def _is_control(character: str) -> bool:
    return "\x00" <= character <= "\x08" or "\x0b" <= character <= "\x1f" or character == "\x7f"


def parse_listing(text: str) -> list[Entry]:
    """Parse listing lines, retaining source line numbers and exact diagnostics."""
    if text == "":
        return []

    lines = text.split("\n")
    if text.endswith("\n"):
        lines.pop()

    entries: list[Entry] = []
    seen: set[str] = set()

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.removesuffix("\r")
        start = 0
        while start < len(line) and _is_blank(line[start]):
            start += 1

        if start == len(line) or line[start] == "#":
            continue

        for column, character in enumerate(line, start=1):
            if _is_control(character):
                raise Failure(
                    f"WL001 unexpected character {show(character)} at {line_number}:{column}"
                )

        end = len(line)
        while end > start and _is_blank(line[end - 1]):
            end -= 1
        name_text = line[start:end]

        try:
            name = parse_name(name_text, sdist_ok=True)
        except TagProblem as error:
            column = start + error.column
            raise Failure(f"{error.code} {error.problem} at {line_number}:{column}") from error

        if name_text in seen:
            raise Failure(f"WL011 repeated file {show(name_text)} at {line_number}:{start + 1}")

        seen.add(name_text)
        entries.append(Entry(line=line_number, name=name))

    return entries


@dataclass(frozen=True)
class Loaded:
    display: str
    entries: list[Entry]


def load_listing(io: Io, arg: str) -> Loaded:
    """Read, decode and parse one named listing source."""
    display, text = read_text(io, arg)
    try:
        entries = parse_listing(text)
    except Failure as error:
        raise Failure(f"{display}: {error}") from error

    if not entries:
        raise Failure(f"{display}: no entries")

    return Loaded(display=display, entries=entries)
