from typing import Union

from constants import ARG_NUM, ARG_TYPES, DEFAULT_VALUES, KEY_TYPES, Types
from extended import SignedNum

__all__ = ["interpret"]

STRICT = False


def add_vals(val1, val2):
    try:
        return val1 + val2
    except TypeError:
        # raise `StopIteration` to skip the command if the values are not ints
        raise StopIteration()


class Variable():
    def __init__(self, name: str, type: str, value) -> None:
        self.name = name
        self.type = type
        self.value = value

    def set_value(self, value) -> None:
        types = {
            "str": ["str"],
            "num": ["float", "int", "SignedInt", "SignedFloat"],
            "bool": ["bool", "Bool"]
        }

        if(STRICT and value.__class__.__name__ not in types[self.type]):
            raise ValueError(
                f"Cannot assign type `{value.__class__.__name__}` to variable of type `{self.type}`")

        elif(value.__class__.__name__ in types[self.type]):
            self.value = value

        else:
            raise StopIteration()

    def get_type(self):
        types = {
            "num": Types.KW_NUMBER,
            "str": Types.KW_STRING,
            "bool": Types.KW_BOOL
        }
        return types[self.type]

    def set_type(self, type) -> None:
        self.type = type


class Command():

    class Argument():
        def __init__(self, type: str, value) -> None:
            self.value: Union[str, SignedNum] = value
            self.type = type

    def __init__(self, name: str) -> None:
        self.name = name
        self.arguments = []

    def validate_args(self) -> None:
        arg_num = ARG_NUM[self.name]
        curr_num = len(self.arguments)

        if(not curr_num >= arg_num[0]):
            if(STRICT):
                raise TypeError(
                    f"`{self.name}` takes at least {arg_num[0]} arguments. {curr_num} were given.")
            else:
                raise StopIteration()

        elif(arg_num[1] is not None and not curr_num <= arg_num[1]):
            if(STRICT):
                raise TypeError(
                    f"`{self.name}` takes at most {arg_num[1]} arguments. {curr_num} were given.")
            else:
                raise StopIteration()

        for index, arg in enumerate(self.arguments):
            type = ARG_TYPES[self.name][index]

            if(arg.type not in type and arg.type != type):
                if(STRICT):
                    raise TypeError(
                        f"Argument {index + 1} of `{self.name}` must be of type {type}, not {arg.type}.")
                else:
                    raise StopIteration()

    def add_argument(self, type: str, value) -> None:
        self.arguments.append(Command.Argument(type, value))

    def get_argument_checked(self, num: int) -> Union[Argument, Variable]:
        try:
            arg = self.arguments[num]

            types = ARG_TYPES[self.name][num]

            if(arg.type == Types.VARIABLE):

                # check if variable exists in the stack
                if(not GLOBAL.is_stack_variable(arg.value)):
                    if(STRICT):
                        raise NameError(
                            f"`{arg.value}` referenced before definition")
                    else:
                        raise StopIteration()

                # if it exists get it. `True` means it raises an error if it doesnt exist becuase
                # the check before can be skipped if `STRICT` is `False`
                var = GLOBAL.get_stack_variable(
                    arg.value, GLOBAL.get_stack_scope(arg.value), True)

                # check the actual type of the variable
                if(var.get_type() not in types):
                    if(STRICT):
                        raise TypeError(
                            f"Argument {num + 1} of `{self.name}` must be of type {types}, not {var.get_type()}.")
                    else:
                        raise StopIteration()

                return var

            else:

                if(arg not in types):
                    if(STRICT):
                        raise TypeError(
                            f"Argument {num + 1} of `{self.name}` must be of type {types}, not {arg.type}.")
                    else:
                        raise StopIteration()

                return arg

        except IndexError:
            # raise a random error that we catch in the while loop to skip that iteration
            raise StopIteration()

    def get_argument_raw(self, num: int) -> Union[Argument, None]:
        try:
            return self.arguments[num]
        except IndexError:
            return None


def check_and_get_var(name: str) -> Variable:
    if(STRICT and not GLOBAL.is_stack_variable(name)):
        raise NameError(
            f"`{name}` referenced before definition")

    return GLOBAL.get_stack_variable(
        name, GLOBAL.get_stack_scope(name))


class Function():
    def __init__(self, name) -> None:
        self.name = name


class Stack():
    def __init__(self, name: str):
        self.name = name

        self.stack = [{
            "scope": self.name,
            "variables": [],
            "calls": [],
        }]

    def new_stack_scope(self, name: str) -> None:
        # push new scope to stack
        self.stack.append({
            "scope": name,
            "variables": [],
            "calls": [],
        })

    def get_stack_scope(self, name: str) -> int:
        # get the index of the requested scope
        for index, stack in enumerate(self.stack):
            if(stack["scope"] == name):
                return index
        # if the stack doesnt exist just push globally to be safe
        return 0

    def push_stack_variable(self, var: Variable) -> None:
        # push to the last item in the stack i.e. the most local stack
        self.stack[-1]["variables"].append(var)

    def get_stack_variable(self, name: str, scope: int, _raise: bool = False) -> Variable:
        # get the specific variable from the specific scope
        vars = self.stack[scope]["variables"]

        for var in vars:
            if(var.name == name):
                return var

        # `_raise` determines whether to skip that command if the variable doesnt exist
        if(_raise):
            raise StopIteration()

        return None

    def is_stack_variable(self, name: str) -> bool:
        # start at the most local scope
        for scope in self.stack[::-1]:
            for var in scope["variables"]:
                if(var.name == name):
                    return True
        return False


# `GLOBAL.new_stack_scope` will create a new local stack
GLOBAL = Stack("__global")


class Interpreter():
    def __init__(self, tokens: list) -> None:
        self.commands: list[Command] = self.interp(tokens)

    def interp(self, tokens: list) -> list[Command]:
        commands = []

        # converts the tokens to a list of commands
        for index, token in enumerate(tokens):
            if(token.type == "EOF"):
                break

            elif(token.type == "COMMAND"):
                command = Command(token.value)

                # as soon as we hit a command, loop over the rest of the tokens (until a right bracket) and add all arguments
                for t in tokens[index:]:
                    if(t.type == "R_BRACK"):
                        break

                    if(t.type == "ARG"):
                        command.add_argument("SYMBOL", t.value)

                    elif(t.type in ["LT_NUM", "LT_NUM+", "LT_NUM-"]):
                        # the `replace` will either leave `+` or `-` or just `` if there is no sign
                        val = SignedNum(
                            t.value, t.type.replace("LT_NUM", ""))
                        command.add_argument("LT_NUM", val)

                    elif(t.type in Types.KEYWORDS):
                        command.add_argument(t.type, t.value)

                    elif(t.type == Types.LITERAL_STRING):
                        command.add_argument(Types.LITERAL_STRING, t.value)

                try:
                    command.validate_args()
                except StopIteration:
                    # skip the command if the arguments are invalid (and strict mode is off)
                    continue

                commands.append(command)

        return commands

    def exec(self) -> None:
        pointer = 0

        while(pointer < len(self.commands)):
            command: Command = self.commands[pointer]

            pointer += 1

            name = command.name

            # if strict mode is off, argument types and the number of arguments are not checked therefore there is no guarantee that
            # any of these command will have all the arguments required. to fix this we could check whether all the commands / command values
            # are `None` however this is messy and creates a lot of dupolicated code.
            # instead, if the value requested does not exist, the `get_argument_value` will raise a `StopIteration` error. this will be
            # caught by this try catch, and will just skip that command which is the desired behaviour.
            # it only catches `StopIteration` so that any other exceptions will pass through
            try:
                if(name == "$"):
                    var = command.get_argument_raw(0)
                    type = command.get_argument_raw(1)

                    # should be the only time we have to check whether something is `None`
                    if(var is None or type is None):
                        return

                    try:
                        DEFAULT_VALUES[type.value]
                    except KeyError:
                        if(STRICT):
                            raise TypeError(
                                f"Uknown type `{type.value}`")
                        else:
                            raise StopIteration()

                    value = DEFAULT_VALUES[type.value]

                    if(not GLOBAL.is_stack_variable(var.value)):
                        GLOBAL.push_stack_variable(
                            Variable(var.value, type.value, value))

                elif(name == "="):
                    var1 = command.get_argument_checked(0)
                    var2 = command.get_argument_checked(1)

                    if(var1.type != "num" or var2.type not in ["num", "NUMBER"]):
                        if(STRICT):
                            raise TypeError("Refactor needed")
                        else:
                            raise StopIteration()

                    var1.set_value(var2.value)

                elif(name == "+"):
                    var1 = command.get_argument_checked(0)
                    var2 = command.get_argument_checked(1)

                    # if(var1.type != "num" or var2.type not in ["num", "NUMBER"]):
                    #     if(STRICT):
                    #         raise TypeError("Refactor needed")
                    #     else:
                    #         raise StopIteration()

                    var1.set_value(
                        add_vals(var1.value, var2.value))

                elif(name == "%"):
                    var1 = command.get_argument_checked(0)
                    var2 = command.get_argument_checked(1)
                    var3 = command.get_argument_checked(2)

                    if(var1.type in KEY_TYPES or var2.type in KEY_TYPES or var3.type != "num"):
                        if(STRICT):
                            raise TypeError("Refactor needed")
                        else:
                            raise StopIteration()

                    if(var1.value == var2.value):
                        var3.set_value(0)
                    elif(var1.value > var2.value):
                        var3.set_value(1)
                    else:
                        var3.set_value(-1)

                elif(name == ":"):
                    var1 = command.get_argument_checked(0)
                    var2 = command.get_argument_checked(1)

                    # if(var1.type != "str" or var2.type not in ["str", "STRING"]):
                    #     if(STRICT):
                    #         raise TypeError("Refactor needed")
                    #     else:
                    #         raise StopIteration()

                    var1.set_value(var2.value)

                elif(name == "&"):
                    var1 = command.get_argument_checked(0)
                    var2 = command.get_argument_checked(1)

                    if(var1.type != "str" or var2.type not in ["str", "STRING"]):
                        if(STRICT):
                            raise TypeError("Refactor needed")
                        else:
                            raise StopIteration()

                    var1.set_value(str(var1.value) + str(var2.value))

                elif(name == "!"):
                    var1 = command.get_argument_checked(0)

                    if(var1.type == "str"):
                        var1.set_value(var1.value.upper())
                    elif(var1.type == "bool"):
                        # the ~ is the bitwise NOT operator.
                        # it is used because in `Bool` we have overridden the `__invert__` method which is called when using
                        # that operator
                        var1.set_value(~var1.value)
                    elif(var1.type == "num"):
                        var1.set_value(var1.value * -1)

                elif(name == "."):
                    var1 = command.get_argument_checked(0)

                    var1.set_value(var1.value.lower())
                elif(name == "@"):
                    pass
                elif(name == "\""):
                    pass
                elif(name == "1"):
                    pass
                elif(name == "#"):
                    # + and - index

                    pass
                elif(name == "?"):
                    var1 = command.get_argument_checked(0)
                    var2 = command.get_argument_checked(1)

                    if(var1.value):
                        if(var2.value.get_sign() == "+"):
                            pointer = pointer + var2.value
                        elif(var2.value.get_sign() == "-"):
                            pointer = pointer - var2.value

                        else:
                            pointer = var2.value

                    elif(len(command.arguments) == 3):
                        var3 = command.get_argument_checked(2)

                        if(var3.value.get_sign() == "+"):
                            pointer = pointer + var3.value
                        elif(var3.value.get_sign() == "-"):
                            pointer = pointer - var3.value

                        else:
                            pointer = var3.value

                elif(name == "/"):
                    pass
                elif(name == "\\"):
                    pass
                elif(name == "|"):
                    pass
                elif(name == ">"):
                    pass
                elif(name == "<"):
                    var = command.get_argument_checked(0)

                    # unescapes the string
                    print(str(var.value).encode(
                        "utf-8").decode("unicode-escape"))

            # skip command
            except StopIteration:
                pass


def interpret(tokens: list, strict: bool = False) -> None:
    global STRICT  # eh
    STRICT = strict

    return Interpreter(tokens).exec()
