from wheeltags.failure import Failure
from wheeltags.text import show


class TagProblem(Failure):
    """A tag grammar error with its diagnostic code and code-point column."""

    def __init__(self, code: str, problem: str, column: int) -> None:
        self.code = code
        self.problem = problem
        self.column = column
        super().__init__(f"{problem} at column {column}")


def check_chars(text: str) -> None:
    """Reject the first character outside printable ASCII punctuation and letters."""
    for column, character in enumerate(text, start=1):
        if not ("!" <= character <= "~"):
            raise TagProblem("WL002", f"unexpected character {show(character)}", column)


def _valid_tag_part(part: str) -> bool:
    return bool(part) and all(
        "a" <= character <= "z" or "0" <= character <= "9" or character == "_" for character in part
    )


def check_fields(fields: list[str], columns: list[int]) -> tuple[list[str], list[str], list[str]]:
    """Validate python, ABI and platform fields and return their ordered parts."""
    tag_sets: list[list[str]] = []
    labels = ("python", "abi", "platform")
    codes = ("WL008", "WL009", "WL010")

    for field, column, label, code in zip(fields, columns, labels, codes, strict=True):
        parts = field.split(".")
        part_column = column
        for part in parts:
            if not _valid_tag_part(part):
                problem = f"invalid {label} tag {show(part)}"
                raise TagProblem(code, problem, part_column)
            part_column += len(part) + 1
        tag_sets.append(parts)

    return tag_sets[0], tag_sets[1], tag_sets[2]


def parse_tagset(text: str) -> tuple[list[str], list[str], list[str]]:
    """Parse a three-field python-ABI-platform tag set."""
    check_chars(text)
    fields = text.split("-")
    columns: list[int] = []
    column = 1
    for field in fields:
        columns.append(column)
        column += len(field) + 1

    if len(fields) < 3:
        raise TagProblem("WL004", "wrong number of fields", len(text) + 1)
    if len(fields) > 3:
        raise TagProblem("WL004", "wrong number of fields", columns[3])

    return check_fields(fields, columns)


def expand_tags(pythons: list[str], abis: list[str], platforms: list[str]) -> list[str]:
    """Expand tag fields in stable order, retaining each complete tag once."""
    expanded: list[str] = []
    seen: set[str] = set()

    for python in pythons:
        for abi in abis:
            for platform in platforms:
                tag = f"{python}-{abi}-{platform}"
                if tag not in seen:
                    seen.add(tag)
                    expanded.append(tag)

    return expanded
