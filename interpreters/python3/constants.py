from extended import Bool

COMMANDS = ["~", "$", "+", "=", "%", ":", "&", "!", ".",
            "@", "\"", "1", "#", "?", "/", "\\", "|", ">", "<"]

# min | max
ARG_NUM = {
    "~": [1, 1],

    "$": [2, 2],
    "+": [2, 2],
    "=": [2, 2],
    "%": [3, 3],
    ":": [2, 2],
    "&": [2, 2],
    "$": [2, 2],
    "!": [1, 1],
    ".": [1, 1],
    "@": [3, 3],

    "\"": [2, 2],
    "1": [2, 2],

    "#": [1, 1],
    "?": [2, 3],

    "/": [1, None],  # `None` specifies unlimited arguments
    "\\": [1, 1],
    "|": [1, None],

    ">": [2, 3],
    "<": [1, 1],
}


class Types:
    LITERAL_NUMBER = "LT_NUM"
    LITERAL_STRING = "LT_STR"

    KW_NUMBER = "KW_NUM"
    KW_STRING = "KW_STR"
    KW_BOOL = "KW_BOOL"

    VARIABLE = "SYMBOL"
    KEYWORDS = [KW_NUMBER, KW_STRING, KW_BOOL]

    NUMBER = [LITERAL_NUMBER, KW_NUMBER, VARIABLE]
    STRING = [LITERAL_STRING, KW_STRING]
    BOOL = KW_BOOL

    ANY = [LITERAL_NUMBER, KW_NUMBER,
           LITERAL_STRING, KW_STRING, KW_BOOL, VARIABLE]


ARG_TYPES = {
    "<": [Types.ANY],

    "$": [Types.VARIABLE, Types.KEYWORDS],
    "+": [Types.NUMBER, Types.NUMBER],

    # finish me
    "!": ["SYMBOL"],
    ".": ["SYMBOL"],
    "=": ["SYMBOL", ["NUMBER", "SYMBOL"]],
    ":": ["SYMBOL", ["STRING", "SYMBOL"]],
    "&": ["SYMBOL", ["STRING", "BOOL", "NUMBER", "SYMBOL"]],


    "?": ["SYMBOL", "NUMBER", "NUMBER"],
    "%": ["SYMBOL", "SYMBOL", "SYMBOL"],
}

DEFAULT_VALUES = {
    "num": 0,
    "str": "",
    "bool": Bool(False),
}

STRICT = False
