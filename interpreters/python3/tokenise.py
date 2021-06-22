from pathlib import Path
from base64 import b64encode

__all__ = ["tokenize", "write_tokenised_to_file"]

TOKENS = {
    "~": "IMPORT",

    "$": "DECL",
    "+": "ADD",
    "=": "SET_NUM",
    "%": "COMP",
    ":": "SET_STR",
    "!": "UPPER",
    ".": "LOWER",
    "@": "TRIM",

    "\"": "TO_STR",
    "1": "TO_NUM",

    "#": "INDEX",
    "?": "JMP",

    "/": "FUNC_START",
    "\\": "FUNC_END",
    "|": "FUNC_EXEC",

    ">": "INPUT",
    "<": "OUTPUT",
}

COMMANDS = TOKENS.keys()


class CONTEXTS:
    OUT = "out"
    IN = "in"
    STR = "str"


class Token():
    def __init__(self, type: str, value: str) -> None:

        self.type = type
        self.value = value

    def __str__(self) -> str:
        return f"Token({self.type}, {self.value})"

    def __repr__(self) -> str:
        return self.__str__()


def tokenise(file: Path) -> list[Token]:
    CONTEXT = CONTEXTS.OUT

    tokens = []

    var_name = ""
    string = ""

    def add_token(char: str, type: str) -> None:
        tokens.append(Token(
            type, char
        ))

    with open(file, "r") as f:
        # enum. over each line and character to allow for reporting syntax errors with the location
        for line in f:
            for char_index, char in enumerate(line):

                next = ["" if(char_index + 1 >= len(line))
                        else line[char_index + 1]][0]
                prev = line[char_index - 1]

                # ignore if the character is whitespace
                if(char.isspace()):
                    continue

                # checks if the character is a valid command. only adds it if it is followed by a bracket
                elif(char in COMMANDS and next == "(" and CONTEXT == CONTEXTS.OUT):
                    add_token(char, TOKENS[char])

                # check if its an opening bracket but also if the previous character was a command otherwise it will ignore it
                    # i.e `#()` is valid but `()` is not
                elif(char == "(" and prev in COMMANDS and CONTEXT == CONTEXTS.OUT):
                    CONTEXT = CONTEXTS.IN

                    add_token(char, "L_BRACK")

                elif(char == ")" and CONTEXT == CONTEXTS.IN):
                    CONTEXT = CONTEXTS.OUT

                    # when we are about to leave the context, if there was an argument left over add it and clear the name
                    if(var_name != ""):
                        add_token(var_name, "ARG")
                        var_name = ""

                    add_token(char, "R_BRACK")

                # both " and ' work to denote string so the character is checked against both
                elif(char == "\"" or char == "'"):
                    if(CONTEXT == CONTEXTS.STR):
                        CONTEXT = CONTEXTS.IN

                        add_token(string, "STR_VAL")
                        add_token(char, "STR_END")

                        string = ""
                    else:
                        CONTEXT = CONTEXTS.STR

                        add_token(char, "STR_START")

                # if we are in the middle of a string i.e. after the first ", concat all characters together
                elif(CONTEXT == CONTEXTS.STR):
                    string = string + char

                # this will add all the arguments of the funtion since the context is `in` after and open bracket
                elif(CONTEXT == CONTEXTS.IN):
                    if(char != ","):
                        # concat all the characters together into cohesive name
                        var_name = var_name + char
                    else:
                        add_token(var_name, "ARG")
                        add_token(char, "SEP")

                        # wipe the argument name once we hit a separator
                        var_name = ""
    return tokens


def write_tokenised_to_file(name: str, tokens: list[Token]) -> None:
    folder = Path("./__afcache")
    folder.mkdir(parents=True, exist_ok=True)

    data = ""
    with open(folder / Path(f"{name}_tok.aftok"), "wb") as f:

        data = "|".join(tokens)

        f.write(b64encode(data.encode()))
