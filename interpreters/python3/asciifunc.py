import argparse
from pathlib import Path

from tokenise import tokenise
from interpreter import interpret

parser = argparse.ArgumentParser(description="Runs an asciifunc file.")

parser.add_argument("--file", "-f",
                    dest="file",
                    help="Path to the file.",
                    required=True,
                    default=None)

parser.add_argument("--strict", "-s",
                    dest="strict",
                    action="store_true",
                    help="Strict mode (raises errors).",
                    required=False,
                    default=False)

args = parser.parse_args()

if(args.file is None or not Path(args.file).exists()):
    raise ValueError("File does not exist!")

STRICT = args.strict

tok = tokenise(args.file)
interpret(tok, STRICT)
