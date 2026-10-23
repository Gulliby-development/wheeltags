from wheeltags.expand_rows import render
from wheeltags.failure import Failure
from wheeltags.options import Parsed, Spec
from wheeltags.streams import Io
from wheeltags.tagsets import TagProblem, expand_tags, parse_tagset
from wheeltags.text import show

USAGE = "wheeltags expand TAGSET"
SPECS: list[Spec] = []


def run_expand(args: list[str], parsed: Parsed, io: Io) -> tuple[str, int]:
    if not args:
        raise Failure("missing TAGSET")
    if len(args) > 1:
        raise Failure("too many arguments")

    tagset = args[0]
    try:
        pythons, abis, platforms = parse_tagset(tagset)
    except TagProblem as error:
        raise Failure(f"{show(tagset)}: {error.code} {error}") from error

    tags = expand_tags(pythons, abis, platforms)
    return render(tags), 0
