from wheeltags.text import line


def render(tags: list[str]) -> str:
    """Render expanded tags and their count as LF-terminated output."""
    rows = "".join(f"{tag}\n" for tag in tags)
    return f"{rows}{line('tags', str(len(tags)))}\n"
