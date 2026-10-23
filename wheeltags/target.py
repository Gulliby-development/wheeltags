from dataclasses import dataclass

from wheeltags.failure import Failure
from wheeltags.platforms import ladder
from wheeltags.text import show


@dataclass(frozen=True)
class Target:
    text: str
    python: str
    minor: int
    platform: str
    platforms: list[str]


def parse_target(text: str) -> Target:
    python, separator, platform = text.partition(":")
    if not separator:
        raise Failure(f"invalid target {show(text)}")

    if not python.startswith("cp3"):
        raise Failure(f"invalid python {show(python)}")
    minor_text = python[3:]
    if not 1 <= len(minor_text) <= 2:
        raise Failure(f"invalid python {show(python)}")
    if any(character < "0" or character > "9" for character in minor_text):
        raise Failure(f"invalid python {show(python)}")
    if len(minor_text) > 1 and minor_text[0] == "0":
        raise Failure(f"invalid python {show(python)}")

    minor = int(minor_text)
    if not 2 <= minor <= 99:
        raise Failure(f"invalid python {show(python)}")

    platforms = ladder(platform)
    if platforms is None:
        raise Failure(f"invalid platform {show(platform)}")

    return Target(text, python, minor, platform, platforms)


def target_tags(target: Target) -> list[str]:
    python_interpreters = [
        f"py3{target.minor}",
        "py3",
        *(f"py3{minor}" for minor in range(target.minor - 1, -1, -1)),
    ]
    stages = [
        [f"{target.python}-{target.python}-{platform}" for platform in target.platforms],
        [f"{target.python}-abi3-{platform}" for platform in target.platforms],
        [f"{target.python}-none-{platform}" for platform in target.platforms],
        [
            f"cp3{minor}-abi3-{platform}"
            for minor in range(target.minor - 1, 1, -1)
            for platform in target.platforms
        ],
        [
            f"{interpreter}-none-{platform}"
            for interpreter in python_interpreters
            for platform in target.platforms
        ],
        [f"{target.python}-none-any"],
        [f"{interpreter}-none-any" for interpreter in python_interpreters],
    ]

    tags = []
    seen = set()
    for stage in stages:
        for tag in stage:
            if tag not in seen:
                seen.add(tag)
                tags.append(tag)
    return tags
