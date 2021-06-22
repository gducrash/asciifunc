import argparse
from pathlib import Path

import pprint

from tokenise import tokenise

parser = argparse.ArgumentParser(description="Runs an asciifunc file.")

parser.add_argument("--file", "-f",
                    dest="file",
                    help="Path to the file.",
                    default=None)

args = parser.parse_args()

if(args.file is None or not Path(args.file).exists()):
    raise ValueError("File does not exist!")

pprint.pprint(tokenise(args.file))
