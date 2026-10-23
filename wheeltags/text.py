def show(text: str) -> str:
    """Quote text, replacing every non-printable ASCII code point with a question mark."""
    printable = "".join(character if " " <= character <= "~" else "?" for character in text)
    return f'"{printable}"'


def line(key: str, value: str) -> str:
    """Format a key in a ten-character field followed by its value."""
    padding = " " * max(0, 10 - len(key))
    return f"{key}{padding}  {value}"


def table(header: list[str], rows: list[list[str]]) -> list[str]:
    """Render a left-aligned table with header-inclusive column widths."""
    all_rows = [header, *rows]
    widths = [max(len(row[column]) for row in all_rows) for column in range(len(header))]
    rendered = []

    for row in all_rows:
        cells = []
        for column, cell in enumerate(row):
            if column > 0:
                cells.append("  ")
            cells.append(cell)
            if column < len(row) - 1:
                cells.append(" " * (widths[column] - len(cell)))
        rendered.append("".join(cells).rstrip(" "))

    return rendered


def plural(n: int, word: str) -> str:
    """Return a count and its singular or plural word."""
    suffix = "" if n == 1 else "s"
    return f"{n} {word}{suffix}"
