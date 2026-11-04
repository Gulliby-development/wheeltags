from wheeltags.text import line, table


def matching(
    tags: list[str], abi: str | None, platform: str | None = None
) -> list[tuple[int, str]]:
    """Return each tag with its rank in the full list, keeping only tags of the given abi and platform."""
    ranked = list(enumerate(tags))
    if abi is not None:
        ranked = [(rank, tag) for rank, tag in ranked if tag.split("-")[1] == abi]
    if platform is not None:
        ranked = [(rank, tag) for rank, tag in ranked if tag.split("-")[2] == platform]
    return ranked


def render_tags(
    tags: list[str], limit: int | None, abi: str | None = None, platform: str | None = None
) -> str:
    ranked = matching(tags, abi, platform)
    visible = ranked if limit is None else ranked[:limit]
    rows = [[str(rank), tag] for rank, tag in visible]
    output_lines = table(["RANK", "TAG"], rows)
    output_lines.append(line("tags", str(len(ranked))))
    if limit is not None and limit < len(ranked):
        output_lines.append(line("shown", str(limit)))
    return "\n".join(output_lines) + "\n"
