import sys
from typing import Protocol

from wheeltags.failure import Failure
from wheeltags.text import show


class Io(Protocol):
    def read_stdin(self) -> bytes:
        """Read all bytes from standard input."""

    def read_file(self, path: str) -> bytes:
        """Read all bytes from one explicitly named file."""

    def out(self, text: str) -> None:
        """Write UTF-8 output bytes to standard output."""

    def err(self, text: str) -> None:
        """Write UTF-8 output bytes to standard error."""


class StdIo:
    def read_stdin(self) -> bytes:
        return sys.stdin.buffer.read()

    def read_file(self, path: str) -> bytes:
        with open(path, "rb") as file:
            return file.read()

    def out(self, text: str) -> None:
        sys.stdout.buffer.write(text.encode("utf-8"))

    def err(self, text: str) -> None:
        sys.stderr.buffer.write(text.encode("utf-8"))


def read_text(io: Io, arg: str) -> tuple[str, str]:
    display = "<stdin>" if arg == "-" else show(arg)

    try:
        data = io.read_stdin() if arg == "-" else io.read_file(arg)
    except (OSError, ValueError, UnicodeError) as error:
        raise Failure(f"{display}: cannot read the file") from error

    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise Failure(f"{display}: input is not valid UTF-8") from error

    return display, text.removeprefix("\ufeff")
