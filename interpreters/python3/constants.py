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
    "\\": [0, 1],
    "|": [1, None],

    ">": [2, 2],
    "<": [1, 1],
}


class Types:
    # LT = literal - a literal string is an actual string wrapped in quotes
    # a literal number is just a number
    # a literal bool is `true` / `false`
    LT_NUMBER = "LT_NUM"
    LT_STRING = "LT_STR"

    LT_BOOL = "LT_BOOL"

    # KW = keyword - keywords are `num`, `str`, `bool`
    # they are the types of the variable
    KW_NUMBER = "KW_NUM"
    KW_STRING = "KW_STR"
    KW_BOOL = "KW_BOOL"

    VARIABLE = "SYMBOL"
    KEYWORDS = [KW_NUMBER, KW_STRING, KW_BOOL, LT_BOOL]

    # the reason both `KW_NUMBER` and `VARIABLE` are included is because, when the tokens are being converted to commands,
    # the type of a varible is unknown, so it can only be check to make sure it is a `SYMBOL` (VARIABLE)
    # when the program is actually executing is when we can check whether the variable is `KW_NUMBER`
    ANY_NUMBER = [LT_NUMBER, KW_NUMBER]
    ANY_STRING = [LT_STRING, KW_STRING]

    # technically an `LT_BOOL` is also a `KW_BOOL` because `true` / `false` are not wrapped in quotes but
    # they cant have the same name
    ANY_VAR = [KW_NUMBER, KW_STRING, KW_BOOL]

    ANY = [KW_NUMBER, KW_STRING, KW_BOOL, LT_NUMBER, LT_STRING, LT_BOOL]

    LITERAL_TO_VAR = {
        LT_STRING: KW_STRING,
        LT_NUMBER: KW_NUMBER,
        LT_BOOL: KW_BOOL,
    }


ARG_TYPES = {
    "$": [Types.VARIABLE, Types.KEYWORDS],

    "+": [Types.KW_NUMBER, Types.ANY_NUMBER],
    "=": [Types.KW_NUMBER, Types.ANY_NUMBER],
    "%": [Types.ANY_VAR, Types.ANY_VAR, Types.KW_NUMBER],
    ":": [Types.KW_STRING, Types.ANY_STRING],
    "&": [Types.KW_STRING, Types.ANY],
    "!": [Types.ANY_VAR],
    ".": [Types.KW_STRING],

    "@": [[Types.KW_STRING, Types.KW_NUMBER], Types.ANY_NUMBER, Types.ANY_NUMBER],

    "\"": [Types.ANY_VAR, Types.KW_STRING],
    "1`": [Types.ANY_VAR, Types.KW_NUMBER],

    "#": [Types.LT_NUMBER],
    "?": [Types.ANY_VAR, Types.LT_NUMBER, Types.LT_NUMBER],

    "/": [Types.VARIABLE],
    "\\": [Types.ANY_VAR],
    "|": [Types.VARIABLE, Types.ANY_VAR],

    ">": [Types.KEYWORDS, Types.ANY_VAR],
    "<": [Types.ANY_VAR],
}

DEFAULT_VALUES = {
    "num": 0,
    "str": "",
    "bool": Bool(False),
}

STRICT = False
