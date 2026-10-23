from wheeltags.choose import choose
from wheeltags.failure import Failure
from wheeltags.listing import load_listing
from wheeltags.options import Parsed, Spec
from wheeltags.pick_rows import render_pick
from wheeltags.streams import Io
from wheeltags.target import parse_target, target_tags

USAGE = "wheeltags pick LISTING TARGET... [--all]"
SPECS: list[Spec] = [Spec("--all", False)]


def run_pick(args: list[str], parsed: Parsed, io: Io) -> tuple[str, int]:
    """Select and render the best listing candidate for each requested target."""
    if not args:
        raise Failure("missing LISTING")
    if len(args) < 2:
        raise Failure("missing TARGET")

    listing = load_listing(io, args[0])
    groups = []
    for target_text in args[1:]:
        target = parse_target(target_text)
        groups.append((target.text, choose(listing.entries, target_tags(target))))

    return render_pick(groups, "--all" in parsed.flags)
