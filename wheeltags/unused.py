from wheeltags.choose import Ranked
from wheeltags.listing import Entry
from wheeltags.text import show


def unused_wheels(
    entries: list[Entry], selections: list[tuple[str, list[Ranked]]]
) -> tuple[list[list[str]], int]:
    """Return unused wheel rows and the number of wheels in the listing."""
    winners: set[int] = set()
    first_compatible: dict[int, tuple[str, str]] = {}

    for target, candidates in selections:
        if not candidates:
            continue

        winner = candidates[0].entry
        if winner.name.kind == "wheel":
            winners.add(winner.line)

        for candidate in candidates:
            entry = candidate.entry
            if entry.name.kind == "wheel" and entry.line not in first_compatible:
                first_compatible[entry.line] = (target, winner.name.text)

    rows: list[list[str]] = []
    wheel_count = 0
    for entry in entries:
        if entry.name.kind != "wheel":
            continue

        wheel_count += 1
        if entry.line in winners:
            continue

        compatible = first_compatible.get(entry.line)
        if compatible is None:
            reason = "no compatible target"
        else:
            target, winner = compatible
            reason = f"beaten by {show(winner)} on {target}"

        rows.append([str(entry.line), show(entry.name.text), reason])

    return rows, wheel_count
