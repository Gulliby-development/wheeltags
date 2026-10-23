from wheeltags.failure import Failure
from wheeltags.names import parse_name
from wheeltags.options import Parsed, Spec
from wheeltags.streams import Io
from wheeltags.tagsets import TagProblem, expand_tags
from wheeltags.target import parse_target, target_tags
from wheeltags.text import line, show
from wheeltags.verdict import best_match, incompatible_reason

USAGE = "wheeltags explain FILE TARGET"
SPECS: list[Spec] = []


def run_explain(args: list[str], parsed: Parsed, io: Io) -> tuple[str, int]:
    """Explain whether a wheel filename is compatible with one target."""
    if not args:
        raise Failure("missing FILE")
    if len(args) == 1:
        raise Failure("missing TARGET")
    if len(args) > 2:
        raise Failure("too many arguments")

    file_text, target_text = args
    try:
        wheel = parse_name(file_text, sdist_ok=False)
    except TagProblem as error:
        raise Failure(f"{show(file_text)}: {error.code} {error}") from error

    target = parse_target(target_text)
    wheel_tags = expand_tags(wheel.pythons, wheel.abis, wheel.platforms)
    ranked_tags = target_tags(target)
    match = best_match(wheel_tags, ranked_tags)

    if match is None:
        verdict = "incompatible"
        result = line(
            "reason", incompatible_reason(wheel.pythons, wheel.abis, wheel.platforms, ranked_tags)
        )
        status = 1
    else:
        best_tag, rank = match
        verdict = "compatible"
        result = line("best", f"{best_tag} (rank {rank} of {len(ranked_tags)})")
        status = 0

    rows = [
        line("wheel", show(file_text)),
        line("name", wheel.name),
        line("version", wheel.version_text),
        line("build", "-" if wheel.build is None else str(wheel.build)),
        line("target", target.text),
        line("tags", str(len(wheel_tags))),
        line("verdict", verdict),
        result,
    ]
    return "".join(f"{row}\n" for row in rows), status
