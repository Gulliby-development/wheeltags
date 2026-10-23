def best_match(wheel_tags: list[str], target_tags: list[str]) -> tuple[str, int] | None:
    """Return the wheel tag with the lowest target rank, if any tag matches."""
    ranks = {tag: rank for rank, tag in enumerate(target_tags)}
    best: tuple[str, int] | None = None

    for tag in wheel_tags:
        rank = ranks.get(tag)
        if rank is not None and (best is None or rank < best[1]):
            best = (tag, rank)

    return best


def incompatible_reason(
    pythons: list[str],
    abis: list[str],
    platforms: list[str],
    target_tags: list[str],
) -> str:
    """Explain incompatibility from only the first component in each wheel tag set."""
    python = pythons[0]
    abi = abis[0]
    platform = platforms[0]

    target_pairs = set()
    for tag in target_tags:
        target_python, _, remainder = tag.partition("-")
        target_abi, _, _ = remainder.partition("-")
        target_pairs.add((target_python, target_abi))

    target_pythons = {target_python for target_python, _ in target_pairs}
    if python not in target_pythons:
        return f"python tag {python} is not supported"
    if (python, abi) not in target_pairs:
        return f"{python} with abi tag {abi} is not supported"
    return f"platform tag {platform} is not supported"
