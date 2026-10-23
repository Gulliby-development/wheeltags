from wheeltags.choose import Ranked
from wheeltags.text import line, show, table


def render_pick(groups: list[tuple[str, list[Ranked]]], all_candidates: bool) -> tuple[str, int]:
    """Render selected candidates for ordered target occurrences."""
    rows: list[list[str]] = []
    covered = 0

    for target_text, candidates in groups:
        if not candidates:
            rows.append([target_text, "-", "-", "-"])
            continue

        covered += 1
        selected = candidates if all_candidates else candidates[:1]
        for candidate in selected:
            rank = "sdist" if candidate.rank is None else str(candidate.rank)
            rows.append(
                [
                    target_text,
                    rank,
                    candidate.entry.name.version_text,
                    show(candidate.entry.name.text),
                ]
            )

    output_lines = table(["TARGET", "RANK", "VERSION", "FILE"], rows)
    output_lines.append(line("covered", f"{covered} of {len(groups)}"))
    status = 0 if covered == len(groups) else 1
    return "\n".join(output_lines) + "\n", status
