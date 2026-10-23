import sys

from wheeltags.cli import run
from wheeltags.streams import StdIo

if __name__ == "__main__":
    sys.exit(run(sys.argv[1:], StdIo()))
