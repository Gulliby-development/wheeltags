from wheeltags.failure import Failure
from wheeltags.options import Parsed, Spec
from wheeltags.streams import Io
from wheeltags.tags_view import render_tags
from wheeltags.target import parse_target, target_tags
from wheeltags.text import show

USAGE = "wheeltags tags TARGET [--limit N]"
SPECS: list[Spec] = [Spec("--limit", True)]


def run_tags(args: list[str], parsed: Parsed, io: Io) -> tuple[str, int]:
    if not args:
        raise Failure("missing TARGET")
    if len(args) > 1:
        raise Failure("too many arguments")

    target = parse_target(args[0])

    limit_text = parsed.values.get("--limit")
    limit = None
    if limit_text is not None:
        if not 1 <= len(limit_text) <= 4:
            raise Failure(f"invalid limit {show(limit_text)}")
        if limit_text[0] == "0" or any(
            character < "0" or character > "9" for character in limit_text
        ):
            raise Failure(f"invalid limit {show(limit_text)}")
        limit = int(limit_text)

    return render_tags(target_tags(target), limit), 0
