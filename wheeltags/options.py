from dataclasses import dataclass

from wheeltags.failure import Failure
from wheeltags.text import show


@dataclass(frozen=True)
class Spec:
    name: str
    takes: bool


@dataclass(frozen=True)
class Parsed:
    flags: frozenset[str]
    values: dict[str, str]
    args: list[str]


def parse_options(argv: list[str], specs: list[Spec]) -> Parsed:
    flags: set[str] = set()
    values: dict[str, str] = {}
    args: list[str] = []
    index = 0

    while index < len(argv):
        argument = argv[index]
        if not argument.startswith("--"):
            args.append(argument)
            index += 1
            continue

        name, separator, attached_value = argument.partition("=")
        spec = next((item for item in specs if item.name == name), None)
        if spec is None:
            raise Failure(f"unknown option {show(argument)}")
        if not spec.takes and separator:
            raise Failure(f"{name} takes no value")
        if spec.takes and not separator and index + 1 >= len(argv):
            raise Failure(f"{name} needs a value")
        if name in flags or name in values:
            raise Failure(f"repeated option {name}")

        if spec.takes:
            if separator:
                values[name] = attached_value
            else:
                index += 1
                values[name] = argv[index]
        else:
            flags.add(name)
        index += 1

    return Parsed(frozenset(flags), values, args)
