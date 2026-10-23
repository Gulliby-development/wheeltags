from dataclasses import dataclass

from wheeltags.listing import Entry
from wheeltags.tagsets import expand_tags


@dataclass(frozen=True)
class Ranked:
    entry: Entry
    rank: int | None
    via: str | None


def choose(entries: list[Entry], tags: list[str]) -> list[Ranked]:
    """Return compatible wheels and source archives in installer preference order."""
    tag_ranks: dict[str, int] = {}
    for rank, tag in enumerate(tags):
        tag_ranks.setdefault(tag, rank)

    candidates: list[Ranked] = []
    for entry in entries:
        name = entry.name
        if name.kind == "sdist":
            candidates.append(Ranked(entry=entry, rank=None, via=None))
            continue

        best_rank: int | None = None
        best_tag: str | None = None
        for tag in expand_tags(name.pythons, name.abis, name.platforms):
            rank = tag_ranks.get(tag)
            if rank is not None and (best_rank is None or rank < best_rank):
                best_rank = rank
                best_tag = tag

        if best_rank is not None:
            candidates.append(Ranked(entry=entry, rank=best_rank, via=best_tag))

    def order(candidate: Ranked) -> tuple[tuple[int, int, int, int], int, int, int, int, int]:
        name = candidate.entry.name
        version = tuple(-part for part in name.version)
        kind = 0 if name.kind == "wheel" else 1
        rank = candidate.rank if candidate.rank is not None else 0
        build = name.build
        has_build = 0 if build is None else 1
        build_value = 0 if build is None else -build
        return version, kind, rank, -has_build, build_value, candidate.entry.line

    return sorted(candidates, key=order)
