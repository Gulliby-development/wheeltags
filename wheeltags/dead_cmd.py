from wheeltags.choose import choose
from wheeltags.failure import Failure
from wheeltags.listing import load_listing
from wheeltags.options import Parsed, Spec
from wheeltags.streams import Io
from wheeltags.target import Target, parse_target, target_tags
from wheeltags.text import line, table
from wheeltags.unused import unused_wheels

USAGE = "wheeltags dead LISTING TARGET..."
SPECS: list[Spec] = []


def run_dead(args: list[str], parsed: Parsed, io: Io) -> tuple[str, int]:
    """Return a report for wheels no requested target selects."""
    if not args:
        raise Failure("missing LISTING")
    if len(args) < 2:
        raise Failure("missing TARGET")

    loaded = load_listing(io, args[0])

    targets: list[Target] = []
    for target_text in args[1:]:
        targets.append(parse_target(target_text))

    selections = [(target.text, choose(loaded.entries, target_tags(target))) for target in targets]
    rows, wheel_count = unused_wheels(loaded.entries, selections)

    output_lines = table(["LINE", "FILE", "REASON"], rows) if rows else []
    unused_count = len(rows)
    output_lines.append(line("unused", f"{unused_count} of {wheel_count}"))
    output = "\n".join(output_lines) + "\n"
    return output, 0 if unused_count == 0 else 1
