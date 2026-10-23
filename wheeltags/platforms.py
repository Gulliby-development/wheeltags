_ARCHES = ("x86_64", "i686", "aarch64", "armv7l", "ppc64le", "s390x")
_OLD_MANYLINUX_ARCHES = ("x86_64", "i686")


def _number(text: str) -> int | None:
    if not 1 <= len(text) <= 2:
        return None
    if any(character < "0" or character > "9" for character in text):
        return None
    if len(text) > 1 and text[0] == "0":
        return None
    return int(text)


def _manylinux_ladder(minor: int, arch: str) -> list[str]:
    minimum = 5 if arch in _OLD_MANYLINUX_ARCHES else 17
    if minor < minimum:
        return [f"linux_{arch}"]

    tags = []
    for version in range(minor, minimum - 1, -1):
        tags.append(f"manylinux_2_{version}_{arch}")
        if version == 17:
            tags.append(f"manylinux2014_{arch}")
        if version == 12 and arch in _OLD_MANYLINUX_ARCHES:
            tags.append(f"manylinux2010_{arch}")
        if version == 5 and arch in _OLD_MANYLINUX_ARCHES:
            tags.append(f"manylinux1_{arch}")
    tags.append(f"linux_{arch}")
    return tags


def _macos_ladder(major: int, minor: int, arch: str) -> list[str]:
    if major == 10:
        if arch != "x86_64" or not 4 <= minor <= 15:
            return []
        versions = [(10, version) for version in range(minor, 3, -1)]
    else:
        if not 11 <= major <= 99 or minor != 0 or arch not in ("x86_64", "arm64"):
            return []
        versions = [(version, 0) for version in range(major, 10, -1)]
        versions.extend((10, version) for version in range(16, 3, -1))

    tags = []
    for version_major, version_minor in versions:
        if arch == "x86_64":
            formats = ("x86_64", "universal2")
        elif version_major == 10:
            formats = ("universal2",)
        else:
            formats = ("arm64", "universal2")
        tags.extend(
            f"macosx_{version_major}_{version_minor}_{format_name}" for format_name in formats
        )
    return tags


def ladder(platform: str) -> list[str] | None:
    if platform in ("win32", "win_amd64", "win_arm64"):
        return [platform]

    prefix, separator, arch = platform.partition("_")
    if separator and prefix == "linux" and arch in _ARCHES:
        return [platform]

    prefix, separator, rest = platform.partition("manylinux_2_")
    if not prefix and separator:
        minor_text, separator, arch = rest.partition("_")
        minor = _number(minor_text)
        if separator and minor is not None and arch in _ARCHES:
            return _manylinux_ladder(minor, arch)

    prefix, separator, arch = platform.partition("_")
    if separator and prefix == "manylinux2014" and arch in _ARCHES:
        return _manylinux_ladder(17, arch)
    if separator and prefix == "manylinux2010" and arch in _OLD_MANYLINUX_ARCHES:
        return _manylinux_ladder(12, arch)
    if separator and prefix == "manylinux1" and arch in _OLD_MANYLINUX_ARCHES:
        return _manylinux_ladder(5, arch)

    prefix, separator, rest = platform.partition("musllinux_1_")
    if not prefix and separator:
        minor_text, separator, arch = rest.partition("_")
        minor = _number(minor_text)
        if separator and minor is not None and arch in _ARCHES:
            tags = [f"musllinux_1_{version}_{arch}" for version in range(minor, -1, -1)]
            tags.append(f"linux_{arch}")
            return tags

    prefix, separator, rest = platform.partition("macosx_")
    if not prefix and separator:
        major_text, separator, rest = rest.partition("_")
        minor_text, separator, arch = rest.partition("_")
        major = _number(major_text)
        minor = _number(minor_text)
        if separator and major is not None and minor is not None:
            tags = _macos_ladder(major, minor, arch)
            if tags:
                return tags

    return None
