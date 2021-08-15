from pathlib import Path
from dataclasses import dataclass

from constants import COMMANDS

__all__ = ["tokenize"]


class CONTEXTS:
    OUT = "out"
    IN = "in"
    STR = "str"


@dataclass(frozen=True, repr=False)
class Token():
    type: str
    value: str


def tokenise(file: Path) -> list[Token]:
    CONTEXT = CONTEXTS.OUT

    tokens = []

    var_name = ""
    string = ""

    def add_token(char: str, type: str) -> None:
        tokens.append(Token(
            type, char
        ))

    # is separate because it's used twice and is messy to check if it is a signed number
    def add_arg(val: str):
        try:
            # check if it is a number
            num = float(val)

            # now check if it had a sign
            if(val.find("+") > -1):
                # the + or - at the end denotes the sign
                add_token(num, "LT_NUM+")
            elif(val.find("-") > -1):
                add_token(num, "LT_NUM-")
            else:
                add_token(num, "LT_NUM")

        except ValueError:
            if(val == "bool"):
                add_token(val, "KW_BOOL")
            elif(val == "str"):
                add_token(val, "KW_STR")
            elif(val == "num"):
                add_token(val, "KW_NUM")
            elif(val in ["false", "true"]):
                add_token(val, "LT_BOOL")
            else:
                add_token(val, "ARG")

    with open(file, "r") as f:
        for line in f:
            for char_index, char in enumerate(line):

                next = "" if(char_index + 1 >= len(line)
                             ) else line[char_index + 1]
                prev = line[char_index - 1]

                # ignore if the character is whitespace dont ignore if it is in a string
                if(char.isspace() and CONTEXT != CONTEXTS.STR):
                    continue

                # checks if the character is a valid command. only adds it if it is followed by a bracket
                elif(char in COMMANDS and next == "(" and CONTEXT == CONTEXTS.OUT):
                    add_token(char, "COMMAND")

                # check if its an opening bracket but also if the previous character was a command otherwise it will ignore it
                    # i.e `#()` is valid but `()` is not
                elif(char == "(" and prev in COMMANDS and CONTEXT == CONTEXTS.OUT):
                    CONTEXT = CONTEXTS.IN

                    add_token(char, "L_BRACK")

                elif(char == ")" and CONTEXT == CONTEXTS.IN):
                    CONTEXT = CONTEXTS.OUT

                    # when we are about to leave the context, if there was an argument left over add it and clear the name
                    if(var_name != ""):
                        add_arg(var_name)
                        var_name = ""

                    add_token(char, "R_BRACK")

                elif(char == "\""):
                    if(CONTEXT == CONTEXTS.STR):
                        CONTEXT = CONTEXTS.IN

                        add_token(string, "LT_STR")
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
                        if(var_name != ""):
                            add_arg(var_name)

                        # wipe the argument name once we hit a separator
                        var_name = ""

    add_token("EOF", "EOF")

    return tokens
