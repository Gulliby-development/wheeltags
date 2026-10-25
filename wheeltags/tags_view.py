from wheeltags.text import line, table


def matching(tags: list[str], abi: str | None) -> list[tuple[int, str]]:
    """Return each tag with its rank in the full list, keeping only tags of the given abi."""
    ranked = list(enumerate(tags))
    if abi is None:
        return ranked
    return [(rank, tag) for rank, tag in ranked if tag.split("-")[1] == abi]


def render_tags(tags: list[str], limit: int | None, abi: str | None = None) -> str:
    ranked = matching(tags, abi)
    visible = ranked if limit is None else ranked[:limit]
    rows = [[str(rank), tag] for rank, tag in visible]
    output_lines = table(["RANK", "TAG"], rows)
    output_lines.append(line("tags", str(len(ranked))))
    if limit is not None and limit < len(ranked):
        output_lines.append(line("shown", str(limit)))
    return "\n".join(output_lines) + "\n"
