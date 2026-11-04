from wheeltags.failure import Failure
from wheeltags.options import Parsed, Spec
from wheeltags.streams import Io
from wheeltags.tags_view import matching, render_tags
from wheeltags.target import parse_target, target_tags
from wheeltags.text import show

USAGE = "wheeltags tags TARGET [--limit N] [--abi NAME] [--platform NAME]"
SPECS: list[Spec] = [Spec("--limit", True), Spec("--abi", True), Spec("--platform", True)]


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

    abi = parsed.values.get("--abi")
    if abi is not None and not (
        1 <= len(abi) <= 20
        and all(
            character.isascii() and (character.isalnum() or character == "_") for character in abi
        )
    ):
        raise Failure(f"invalid abi {show(abi)}")

    platform = parsed.values.get("--platform")
    if platform is not None and not (
        1 <= len(platform) <= 40
        and all(
            character.isascii() and (character.isalnum() or character == "_")
            for character in platform
        )
    ):
        raise Failure(f"invalid platform {show(platform)}")

    tags = target_tags(target)
    filtered = abi is not None or platform is not None
    status = 1 if filtered and not matching(tags, abi, platform) else 0
    return render_tags(tags, limit, abi, platform), status
