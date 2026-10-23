from wheeltags.text import line, table


def render_tags(tags: list[str], limit: int | None) -> str:
    visible_tags = tags if limit is None else tags[:limit]
    rows = [[str(rank), tag] for rank, tag in enumerate(visible_tags)]
    output_lines = table(["RANK", "TAG"], rows)
    output_lines.append(line("tags", str(len(tags))))
    if limit is not None and limit < len(tags):
        output_lines.append(line("shown", str(limit)))
    return "\n".join(output_lines) + "\n"
