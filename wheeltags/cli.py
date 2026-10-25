from wheeltags import dead_cmd, expand_cmd, explain_cmd, pick_cmd, tags_cmd
from wheeltags.failure import Failure
from wheeltags.options import Parsed, parse_options
from wheeltags.streams import Io
from wheeltags.text import show

HELP = (
    "usage: wheeltags tags TARGET [--limit N] [--abi NAME]\n"
    "       wheeltags explain FILE TARGET\n"
    "       wheeltags pick LISTING TARGET... [--all]\n"
    "       wheeltags dead LISTING TARGET...\n"
    "       wheeltags expand TAGSET\n"
)

RUNNERS = {
    "tags": tags_cmd.run_tags,
    "explain": explain_cmd.run_explain,
    "pick": pick_cmd.run_pick,
    "dead": dead_cmd.run_dead,
    "expand": expand_cmd.run_expand,
}


def run(argv: list[str], io: Io) -> int:
    try:
        if not argv:
            raise Failure("missing command (tags, explain, pick, dead or expand)")

        command = argv[0]
        if command == "--help" and len(argv) == 1:
            io.out(HELP)
            return 0

        runner = RUNNERS.get(command)
        if runner is None:
            raise Failure(f"unknown command {show(command)}")

        if command == "tags":
            specs = tags_cmd.SPECS
        elif command == "explain":
            specs = explain_cmd.SPECS
        elif command == "pick":
            specs = pick_cmd.SPECS
        elif command == "dead":
            specs = dead_cmd.SPECS
        elif command == "expand":
            specs = expand_cmd.SPECS

        parsed: Parsed = parse_options(argv[1:], specs)
        output, status = runner(parsed.args, parsed, io)
        io.out(output)
        return status
    except Failure as error:
        io.err(f"wheeltags: {error}\n")
        return 2
