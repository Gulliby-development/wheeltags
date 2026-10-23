def _is_ascii_digits(text: str) -> bool:
    return bool(text) and all("0" <= character <= "9" for character in text)


def parse_version(text: str) -> tuple[int, int, int, int] | None:
    if not isinstance(text, str):
        return None

    components = text.split(".")
    if not 1 <= len(components) <= 4:
        return None
    if any(len(component) > 9 or not _is_ascii_digits(component) for component in components):
        return None

    numbers = tuple(int(component) for component in components)
    return numbers + (0,) * (4 - len(numbers))


def parse_build(text: str) -> int | None:
    if not isinstance(text, str) or len(text) > 9 or not _is_ascii_digits(text):
        return None
    return int(text)
