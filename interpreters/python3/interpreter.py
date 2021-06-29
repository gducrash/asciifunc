from typing import Union
from pathlib import Path
import hashlib
import json
import gzip

from constants import ARG_NUM, ARG_TYPES, DEFAULT_VALUES, Types
from extended import Bool, SignedNum
# lots of errors :)
from errors import AlreadyDefinedError, ArgumentNumberError, InvalidArgumentTypeError, InvalidVariableTypeError, SkipCommandError, UknownTypeError, UndefinedError

__all__ = ["interpret"]


def add_vals(val1, val2):
    try:
        return val1 + val2
    except TypeError:
        # raise `SkipCommandError` to skip the command if the values are not ints
        raise SkipCommandError


class Variable():
    def __init__(self, name: str, type: str, value) -> None:
        self.name = name
        self.type = type
        self.value = value

    def set_value(self, value) -> None:
        types = {
            Types.KW_STRING: ["str"],
            Types.KW_NUMBER: ["float", "int", "SignedInt", "SignedFloat"],
            Types.KW_BOOL: ["bool", "Bool"]
        }

        if(value.__class__.__name__ not in types[self.type]):
            raise InvalidVariableTypeError(value.__class__.__name__, self.type)

        elif(value.__class__.__name__ in types[self.type]):
            self.value = value

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
        self.scope = ""

    def set_scope(self, scope: str) -> None:
        self.scope = scope

    def add_argument(self, type: str, value) -> None:
        self.arguments.append(Command.Argument(type, value))

    def get_arg_check_type(self, num: int):
        try:
            # check number of arguments first
            arg_num = ARG_NUM[self.name]
            curr_num = len(self.arguments)

            if(not curr_num >= arg_num[0] or (arg_num[1] is not None and not curr_num <= arg_num[1])):
                raise ArgumentNumberError(self.name, arg_num, curr_num)

            if(curr_num == 0):
                return

            arg = self.arguments[num]
            types = ARG_TYPES[self.name][num]

            # manually type check functions
            if(self.name in ["|", "/", "\\"]):
                if(arg.type != Types.VARIABLE):
                    raise InvalidArgumentTypeError(
                        self.name, 1, Types.VARIABLE, arg.type)

            # if it's a variable we cant check the type here, so we'll need to do it later
            if(arg.type not in types and arg.type != Types.VARIABLE):
                raise InvalidArgumentTypeError(
                    self.name, num + 1, types, arg.type)

            return arg

        except IndexError:
            raise SkipCommandError

    def get_argument_checked(self, num: int) -> Union[Argument, Variable]:
        try:
            arg = self.get_arg_check_type(num)

            types = ARG_TYPES[self.name][num]

            if(arg.type == Types.VARIABLE):

                # check if variable exists in the stack
                if(not STACK.is_stack_variable(arg.value)):
                    raise UndefinedError(arg.value)

                var = STACK.get_stack_variable(arg.value, True)

                # check the actual type of the variable
                if(var.type not in types):
                    raise InvalidArgumentTypeError(
                        self.name, num + 1, types, var.type)

                return var
            else:
                return arg

        except IndexError:
            # raise an error that we catch in the while loop to skip that iteration
            raise SkipCommandError

    def get_argument_raw(self, num: int) -> Union[Argument, None]:
        try:
            return self.get_arg_check_type(num)
        except IndexError:
            return None


class Function():
    def __init__(self, name, pointer, arguments) -> None:
        self.type = Types.VARIABLE
        self.arguments = arguments
        self.pos = pointer
        self.name = name


class Pointer():
    def __init__(self, pos: int) -> None:
        self.pos = pos

    def set_pos(self, pos: int) -> None:
        self.pos = pos

    def move_forward(self, amount: int) -> None:
        self.set_pos(self.pos + amount)

    def move_backward(self, amount: int) -> None:
        self.set_pos(self.pos - abs(amount))


class Stack():
    def __init__(self, name: str):
        self.name = name

        self.curr_scope = 0

        self.stack = [{
            "scope": self.name,
            "variables": [],
            "calls": [],
        }]

    def get_current_scope_name(self):
        return self.stack[self.curr_scope]["scope"]

    def push_new_call(self, name: str, pointer_pos: int, ret_var: Variable) -> None:
        self.stack[self.curr_scope]["calls"].append({
            "name": name,
            "pos": pointer_pos,
            "ret": ret_var,
        })

    def pop_call(self) -> Union[None, object]:
        try:
            # pop the call from the previous scope
            return self.stack[self.curr_scope - 1]["calls"].pop()
        except IndexError:
            return None

    def new_stack_scope(self, name: str) -> None:
        # push new scope to stack
        self.stack.append({
            "scope": name,
            "variables": [],
            "calls": [],
        })

        self.curr_scope = len(self.stack) - 1

    def remove_stack_scope(self, name: str) -> None:
        for index, s in enumerate(self.stack):
            if(s["scope"] == name):
                self.stack.pop(index)

        self.curr_scope = len(self.stack) - 1
        return

    def push_stack_variable(self, var: Union[Variable, Function]) -> None:
        # push to the current scope
        self.stack[self.curr_scope]["variables"].append(var)

    def get_variable(self, scope, name, _raise):
        vars = self.stack[scope]["variables"]

        for var in vars:
            if(var.name == name):
                return var

        # `_raise` determines whether to skip that command if the variable doesnt exist
        if(_raise):
            raise SkipCommandError

        return None

    # gets a variable from the current scope
    def get_stack_variable(self, name: str, _raise: bool = False) -> Variable:
        return self.get_variable(self.curr_scope, name, _raise)

    # gets a variable from the parent scope
    def get_parent_stack_variable(self, name: str, _raise: bool = False) -> Variable:
        return self.get_variable(self.curr_scope - 1, name, _raise)

    def is_stack_variable(self, name: str) -> bool:
        return bool(self.get_stack_variable(name))


# `STACK.new_stack_scope` will create a new local stack
# use quotes in the name since variables can't have quotes in their names so the scope could not possibly be
# overridden
STACK = Stack("\"global\"")


class Interpreter():
    def __init__(self, tokens: list) -> None:
        self.commands: list[Command] = self.interp(tokens)

    def interp(self, tokens: list) -> list[Command]:
        commands = []

        # default is "global" (with quotes)
        scopes = [STACK.get_current_scope_name()]

        # converts the tokens to a list of commands
        for index, token in enumerate(tokens):
            if(token.type == "EOF"):
                break

            elif(token.type == "COMMAND"):
                command = Command(token.value)

                # as soon as we hit a command, loop over the rest of the tokens (until a right bracket) and add all arguments
                for t in tokens[index:]:
                    if(t.type == "R_BRACK"):
                        command.set_scope(scopes[0])

                        # once a right bracket was hit, we need to check if the command is defining a function
                        # if so, the following commands will need to have a different scope
                        # each command having a scope allows for us to stop the user from goto-ing in and out of the function
                        # without calling / returning
                        if(command.name == "/"):
                            if(command.arguments[0].type == Types.VARIABLE):
                                scopes.insert(0, command.arguments[0].value)
                            else:
                                scopes.insert(0, None)

                        elif(command.name == "\\"):
                            scopes.pop(0)

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

                    elif(t.type == Types.LT_STRING):
                        command.add_argument(Types.LT_STRING, t.value)
                commands.append(command)
        return commands

    def exec(self) -> None:
        pointer = Pointer(0)

        # to allow for better recursion, we DONT check if a variable is already defines
        # if the function is recursive
        # this allows you to define variables in a function, without needed to pass them as arguments,
        # while also calling the function recursively
        is_recursive = False

        while(pointer.pos < len(self.commands)):
            command: Command = self.commands[pointer.pos]

            pointer.move_forward(1)

            # skip the command if its scope is not the current scope
            if(STACK.get_current_scope_name() != command.scope):
                continue

            name = command.name

            # if strict mode is off, argument types and the number of arguments are not checked therefore there is no guarantee that
            # any of these command will have all the arguments required. to fix this we could check whether all the commands / command values
            # are `None` however this is messy and creates a lot of dupolicated code.
            # instead, if the value requested does not exist, the `get_argument_value` will raise a `SkipCommand` error. this will be
            # caught by this try catch, and will just skip that command which is the desired behaviour.
            # it only catches `SkipCommand` so that any other exceptions will pass through
            try:
                if(name == "$"):
                    if(is_recursive):
                        raise SkipCommandError

                    var = command.get_argument_raw(0)
                    type = command.get_argument_raw(1)

                    # should be the only time we have to check whether something is `None`, since the variable might not exist
                    if(var is None or type is None):
                        raise SkipCommandError

                    try:
                        DEFAULT_VALUES[type.value]
                    except KeyError:
                        raise UknownTypeError(type.value)

                    value = DEFAULT_VALUES[type.value]

                    if(not STACK.is_stack_variable(var.value)):
                        STACK.push_stack_variable(
                            Variable(var.value, type.type, value))
                    else:
                        raise AlreadyDefinedError(var.value)

                elif(name == "="):
                    var1 = command.get_argument_checked(0)
                    var2 = command.get_argument_checked(1)

                    var1.set_value(var2.value)

                elif(name == "+"):
                    var1 = command.get_argument_checked(0)
                    var2 = command.get_argument_checked(1)

                    var1.set_value(
                        add_vals(var1.value, var2.value))

                elif(name == "%"):
                    var1 = command.get_argument_checked(0)
                    var2 = command.get_argument_checked(1)
                    var3 = command.get_argument_checked(2)

                    if(var1.value == var2.value):
                        var3.set_value(0)
                    elif(var1.value > var2.value):
                        var3.set_value(1)
                    else:
                        var3.set_value(-1)

                elif(name == ":"):
                    var1 = command.get_argument_checked(0)
                    var2 = command.get_argument_checked(1)

                    var1.set_value(var2.value)

                elif(name == "&"):
                    var1 = command.get_argument_checked(0)
                    var2 = command.get_argument_checked(1)

                    var1.set_value(str(var1.value) + str(var2.value))

                elif(name == "!"):
                    var1 = command.get_argument_checked(0)

                    if(var1.type == Types.KW_STRING):
                        var1.set_value(var1.value.upper())
                    elif(var1.type == Types.KW_BOOL):
                        # the ~ is the bitwise NOT operator.
                        # it is used because in `Bool` we have overridden the `__invert__` method which is called when using
                        # that operator
                        var1.set_value(~var1.value)
                    elif(var1.type == Types.KW_NUMBER):
                        var1.set_value(var1.value * -1)

                elif(name == "."):
                    var1 = command.get_argument_checked(0)

                    var1.set_value(var1.value.lower())
                elif(name == "@"):
                    var1 = command.get_argument_checked(0)
                    var2 = command.get_argument_checked(1)
                    var3 = command.get_argument_checked(2)

                    if(var1.type == Types.KW_STRING):
                        var1.set_value(var1.value[var2.value:var3.value])
                    elif(var1.type == Types.KW_NUMBER):
                        var1.set_value(var1.value.clamp(
                            var2.value, var3.value))

                elif(name == "\""):
                    var1 = command.get_argument_checked(0)
                    var2 = command.get_argument_checked(1)

                    if(var1.type == Types.KW_NUMBER):
                        var2.set_value(var1.value.get_sign() + str(var1.value))
                    elif(var1.type == Types.KW_BOOL):
                        var2.set_value(str(var1.value))

                elif(name == "1"):
                    var1 = command.get_argument_checked(0)
                    var2 = command.get_argument_checked(1)

                    try:
                        var2.set_value(SignedNum(var1.value))
                    except ValueError:
                        var2.set_value(0)

                elif(name == "#"):
                    var1 = command.get_argument_checked(0)

                    if(var1.value.get_sign() == "+"):
                        pointer.move_forward(var1.value - 1)
                    elif(var1.value.get_sign() == "-"):
                        pointer.move_backward(abs(var1.value))

                    else:
                        pointer.set_pos(var1.value - 1)

                elif(name == "?"):
                    var1 = command.get_argument_checked(0)
                    var2 = command.get_argument_checked(1)

                    if(var1.value):
                        if(var2.value.get_sign() == "+"):
                            pointer.move_forward(var2.value - 1)
                        elif(var2.value.get_sign() == "-"):
                            pointer.move_backward(abs(var1.value))

                        else:
                            pointer.set_pos(var2.value - 1)

                    elif(len(command.arguments) == 3):
                        var3 = command.get_argument_checked(2)

                        if(var3.value.get_sign() == "+"):
                            pointer.move_forward(var3.value - 1)
                        elif(var3.value.get_sign() == "-"):
                            pointer.move_backward(abs(var3.value))

                        else:
                            pointer.set_pos(var3.value - 1)

                elif(name == "/"):
                    # the func name (argument 0) is a symbol (variable) but isnt actually a variable defined yet
                    # so we need to get it without checking if it exists
                    var1 = command.get_argument_raw(0)

                    if(STACK.is_stack_variable(var1.value)):
                        raise AlreadyDefinedError(var1.value)

                    arguments = []

                    if(len(command.arguments) > 1):
                        arguments = command.arguments[1:]

                    # pass down all arguments except the name
                    func = Function(var1.value, pointer.pos, arguments)

                    # create func and define in the current scope
                    STACK.push_stack_variable(func)

                elif(name == "\\"):
                    var1 = command.get_argument_raw(0)

                    ret_val = ""

                    # the `not in_func` just means ignore this if the function is being defined
                    # since ofc the variable will not exist
                    if(var1 is not None and not STACK.is_stack_variable(var1.value)):
                        raise UndefinedError(var1.value)

                    elif(var1 is not None):
                        # get the value of the return value
                        ret_val = STACK.get_stack_variable(var1.value).value

                    # remove the old function call
                    old_call = STACK.pop_call()

                    # ignore if the call stack is empty
                    if(old_call == None):
                        raise SkipCommandError

                    # remove function scope once it has returned
                    STACK.remove_stack_scope(old_call["name"])

                    if(old_call["ret"] is not None):
                        old_call["ret"].set_value(ret_val)

                    # take the place where the function was called, move the pointer to there
                    # to avoid calling it infinitely
                    pointer.set_pos(old_call["pos"])

                elif(name == "|"):
                    var1 = command.get_argument_raw(0)

                    # try and get the function in the current scope
                    func = STACK.get_stack_variable(var1.value)

                    if(func is None):
                        # to allow for recursive functions, see if the variable exists in the scope above
                        func = STACK.get_parent_stack_variable(var1.value)

                        if(func is None):
                            raise UndefinedError(var1.value)

                        else:
                            # if it does exist in the parent scope, also add it to the current scope
                            # bit bodgey but it works
                            STACK.push_stack_variable(
                                Function(func.name, func.pos, func.arguments))

                    ret_var = None

                    argument_values = []

                    if(len(command.arguments) > 1):

                        # try and get all the values of the arguments passed to the function
                        # and put them in the array
                        for arg in command.arguments[1:len(func.arguments)+1]:

                            if(arg.type == Types.VARIABLE):
                                val = STACK.get_stack_variable(arg.value)

                                if(val is None):
                                    raise UndefinedError(var1.value)

                                argument_values.append(
                                    {"type": val.type, "value": val.value})
                            else:
                                # constants are allowed as arguments to a function so their tyoe need to be converted
                                # from a literal to the respective keyword type
                                argument_values.append(
                                    {"type": Types.LITERAL_TO_VAR[arg.type], "value": arg.value})

                        # if the number of arguments in this command is 1 greater than the number of parameters in the function,
                        # consider the last argument to be the return value
                        if(len(command.arguments) + 1 < len(func.arguments)):
                            ret_var = command.get_argument_checked(-1)

                            if(ret_var.type != Types.VARIABLE):
                                raise InvalidArgumentTypeError(command.name, len(
                                    func.arguments), Types.VARIABLE, ret_var.type)

                    # add function call to history
                    STACK.push_new_call(func.name, pointer.pos, ret_var)

                    # avoid creating a new scope (and variables) on every call (if the function is recursive)
                    if(STACK.get_current_scope_name() != func.name):
                        is_recursive = False
                        # to execute the function, first create a new scope
                        STACK.new_stack_scope(func.name)

                        # once the function scope has been defined, all the parameters need to be defined as variables
                        # using the values we got from the arguments earlier
                        for index, arg in enumerate(func.arguments):
                            STACK.push_stack_variable(
                                Variable(arg.value, argument_values[index]["type"], argument_values[index]["value"]))

                    elif(STACK.get_current_scope_name() == func.name):
                        # if we are calling ourself from ourself, it is now recursive
                        is_recursive = True

                    # move the pointer to inside of the function
                    pointer.set_pos(func.pos)

                elif(name == ">"):
                    var1 = command.get_argument_checked(0)
                    var2 = command.get_argument_checked(1)

                    inp = input(">: ")

                    if(var1.type == Types.KW_NUMBER):
                        try:
                            inp = SignedNum(inp)
                        except ValueError:
                            raise SkipCommandError
                    elif(var1.type == Types.KW_BOOL):
                        if(inp == "true"):
                            inp = Bool(True)
                        elif(inp == "false"):
                            inp = Bool(False)
                        else:
                            raise SkipCommandError

                    var2.set_value(inp)

                elif(name == "<"):
                    var = command.get_argument_checked(0)

                    # unescapes the string
                    print(str(var.value).encode(
                        "utf-8").decode("unicode-escape"))

            # skip command
            except SkipCommandError:
                continue


def interpret(tokens: list) -> None:
    return Interpreter(tokens).exec()


arguments = [
    {"value": "x", "type": "KW_BOOL"},
    {"value": "adadsasd", "type": "KW_STR"},
    {"value": "iamvar", "type": "SYMBOL"},
    {"value": "testtest", "type": "LT_STRING"},
    {"value": "testtest", "type": "SYMBOL"},
    {"value": "testtest", "type": "KW_STR"},
    {"value": "testtest", "type": "KW_NUMBER"},
    {"value": "testtest", "type": "KW_STR"},
    {"value": "testtest", "type": "SYMBOL"},
    {"value": "testtest", "type": "KW_NUMBER"},
    {"value": "testtest", "type": "LT_NUMBER"},
    {"value": "testtest", "type": "LT_NUMBER"},
    {"value": "testtest", "type": "SYMBOL"},
    {"value": "testtest", "type": "KW_STR"},
    {"value": "testtest", "type": "KW_NUMBER"},
    {"value": "testtest", "type": "KW_STR"},
    {"value": "testtest", "type": "LT_STRING"},
    {"value": "testtest", "type": "SYMBOL"},
    {"value": "testtest", "type": "KW_NUMBER"},
    {"value": "testtest", "type": "KW_STR"},
]


def cache_imported_arguments(arguments, file):
    file = Path(file)

    raw_code = open(file, "r")

    raw_file_md5sum = hashlib.md5(raw_code.read().encode("utf-8")).hexdigest()
    xor = ord(raw_file_md5sum[0])

    raw_code.close()

    cache_folder = Path("./.afcache")
    cache_folder.mkdir(parents=True, exist_ok=True)

    with open(cache_folder / f"{file.name}-af.afc", "wb") as f:
        text = f"{raw_file_md5sum[0]}".encode()

        arguments.insert(0, raw_file_md5sum)

        for char in json.dumps(arguments, separators=(",", ":")):
            text += chr(ord(char) ^ xor).encode()

        f.write(gzip.compress(text))


def get_cached_import_arguments(file):
    file = Path(file)

    if(not file.exists()):
        raise ImportError(f"Could not find file `{file.name}`")

    cache_folder = Path("./.afcache")

    with open(cache_folder / f"{file.name}-af.afc", "rb") as f:
        text = gzip.decompress(f.read())

        xor = text[0]

        decoded = ""

        for char in text[1:]:
            decoded += chr(char ^ xor)

        decoded = json.loads(decoded)

        md5sum = decoded[0]

        raw_code = open(file, "r")
        raw_file_md5sum = hashlib.md5(
            raw_code.read().encode("utf-8")).hexdigest()

        if(md5sum == raw_file_md5sum):
            print("not changed!")
        else:
            print("changed!")


# cache_imported_arguments(arguments, "./example.js")

get_cached_import_arguments("./example.js")
