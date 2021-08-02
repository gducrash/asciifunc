
from dataclasses import dataclass, field
from typing import Union, Any
from pathlib import Path
import hashlib
import pickle
import gzip
import os

from tokenise import tokenise
from constants import ARG_NUM, ARG_TYPES, DEFAULT_VALUES, Types
from extended import Bool, SignedNum
# lots of errors :)
from errors import AlreadyDefinedError, ArgumentNumberError, InvalidArgumentTypeError, InvalidVariableTypeError, SkipCommandError, UknownTypeError, UndefinedError, ImportError

__all__ = ["interpret"]


# cd to the current working directory
os.chdir(os.path.dirname(os.path.realpath(__file__)))

CACHE_FOLDER = Path("./.afcache")
CACHE_FOLDER.mkdir(parents=True, exist_ok=True)


def insr_expl(arr, i, add):
    # inserts and explodes array into another array
    return [*arr[0:i], *add, *arr[i:len(arr)]]


def add_vals(val1, val2):
    try:
        return val1 + val2
    except TypeError:
        # raise `SkipCommandError` to skip the command if the values are not ints
        raise SkipCommandError


@dataclass
class Variable():
    name: str
    type: str
    value: Any

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


@dataclass
class Command():
    name: str
    arguments: list = field(default_factory=list)
    scope: str = field(default="")

    @dataclass
    class Argument():
        type: Any
        value: Union[str, SignedNum]

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


@dataclass
class Function():
    name: str
    pos: int
    arguments: list
    type: Any = Types.VARIABLE


@dataclass
class Pointer():
    pos: int
    offset: int = field(default=0)

    def set_pos(self, pos: int) -> None:
        self.pos = pos

    def add_offset(self, offset) -> None:
        self.offset += offset

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

        # get all the scopes up until ours because we dont need to search a scope "lower down" since we couldnt possibly
        # get a variable from there anyway
        # then reverse the scopes so that we start searching at out scope, and work our way up to the global scope
        for scope in self.stack[:self.curr_scope + 1][::-1]:
            for var in scope["variables"]:
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
        scope = self.stack[self.curr_scope]

        for var in scope["variables"]:
            if(var.name == name):
                return True

        return False

    # if a user goto's over an import, defines a function then goto's back to that import,
    # the function's `pos` value is going to be wrong so this function will go through every function
    # and if it comes afer the pointer position of the import, it will add the offset to its position
    def offset_funcs_after_import(self, import_pos, offset) -> None:
        scope = self.stack[self.curr_scope]

        for var in scope["variables"]:
            if(isinstance(var, Function)):
                if(var.pos > import_pos):
                    var.pos = var.pos + offset


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
                        command.add_argument(Types.VARIABLE, t.value)

                    elif(t.type in ["LT_NUM", "LT_NUM+", "LT_NUM-"]):
                        # the `replace` will either leave `+` or `-` or just `` if there is no sign
                        val = SignedNum(
                            t.value, t.type.replace("LT_NUM", ""))
                        command.add_argument(Types.LT_NUMBER, val)

                    elif(t.type == Types.LT_BOOL):
                        command.add_argument(Types.LT_BOOL, Bool(t.value))

                    elif(t.type in Types.KEYWORDS):
                        command.add_argument(t.type, t.value)

                    elif(t.type == Types.LT_STRING):
                        command.add_argument(Types.LT_STRING, t.value)
                commands.append(command)
        return commands

    def exec(self) -> None:
        pointer = Pointer(0)

        # to allow for better recursion, we DONT check if a variable is already defined
        # if the function is recursive
        # this allows you to define variables in a function, without needed to pass them as arguments,
        # while also calling the function recursively
        is_recursive = False

        while(pointer.pos < len(self.commands)):
            command: Command = self.commands[pointer.pos]

            pointer.move_forward(1)

            name = command.name

            # skip the command if its scope is not the current scope
            if(STACK.get_current_scope_name() != command.scope):
                continue

            # if strict mode is off, argument types and the number of arguments are not checked therefore there is no guarantee that
            # any of these command will have all the arguments required. to fix this we could check whether all the commands / command values
            # are `None` however this is messy and creates a lot of duplicated code.
            # instead, if the value requested does not exist, the `get_argument_value` will raise a `SkipCommand` error. this will be
            # caught by this try catch, and will just skip that command which is the desired behaviour.
            # it only catches `SkipCommand` so that any other exceptions will pass through
            try:
                if(name == "~"):
                    file = Path(command.get_argument_checked(0).value)

                    args = []

                    if(not file.exists()):
                        raise ImportError(file.name)

                    if(is_cache_up_to_date(file)):
                        args = get_cached_import_arguments(file)

                    else:
                        tokens = tokenise(file)

                        args = Interpreter(tokens).commands

                        # convert tokens to commands and cache them to the file
                        cache_imported_arguments(args, file)

                    self.commands = insr_expl(
                        self.commands, pointer.pos + 1, args)

                    # add an offset for goto commands later on in the file
                    pointer.add_offset(len(args))

                    # imports should all be at the top of the file so *nothing* is defined before an import but if
                    # a function is defined before an import, its pointer position will need to be updated accordingly
                    STACK.offset_funcs_after_import(
                        pointer.pos, pointer.offset)

                elif(name == "$"):
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

                    try:
                        if(var1.value == var2.value):
                            var3.set_value(SignedNum(0))
                        elif(var1.value > var2.value):
                            var3.set_value(SignedNum(1))
                        else:
                            var3.set_value(SignedNum(-1, "-"))
                    except TypeError:
                        var3.set_value(SignedNum(-1, "-"))

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
                        var2.set_value(str(var1.value))
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
                        pointer.move_backward(var1.value - 1)

                    else:
                        pointer.set_pos((var1.value - 1) + pointer.offset)

                elif(name == "?"):
                    var1 = command.get_argument_checked(0)
                    var2 = command.get_argument_checked(1)

                    if(var1.value):
                        if(var2.value.get_sign() == "+"):
                            pointer.move_forward(var2.value - 1)
                        elif(var2.value.get_sign() == "-"):
                            pointer.move_backward(var2.value - 1)

                        else:
                            pointer.set_pos((var2.value - 1) + pointer.offset)

                    elif(len(command.arguments) == 3):
                        var3 = command.get_argument_checked(2)

                        if(var3.value.get_sign() == "+"):
                            pointer.move_forward(var3.value - 1)
                        elif(var3.value.get_sign() == "-"):
                            pointer.move_backward(var3.value - 1)

                        else:
                            pointer.set_pos((var3.value - 1) + pointer.offset)

                elif(name == "/"):
                    # the func name (argument 0) is a symbol (variable) but isnt actually a variable defined yet
                    # so we need to get it without checking if it exists
                    var1 = command.get_argument_raw(0)

                    if(STACK.is_stack_variable(var1.value)):
                        raise AlreadyDefinedError(var1.value)

                    arguments = []

                    if(len(command.arguments) > 1):
                        arguments = command.arguments[1:]

                    # pass down all arguments except the type
                    func = Function(var1.value, pointer.pos, arguments)

                    # create func and define in the current scope
                    STACK.push_stack_variable(func)

                elif(name == "\\"):
                    var1 = command.get_argument_raw(0)

                    ret_val = ""

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
                        raise UndefinedError(var1.value)

                    ret_var = None

                    argument_values = []

                    if(len(command.arguments) > 1):

                        # try and get all the values of the arguments passed to the function
                        # and put them in the array
                        for arg in command.arguments[1:len(func.arguments) + 1]:

                            if(arg.type == Types.VARIABLE):
                                val = STACK.get_stack_variable(arg.value)

                                if(val is None):
                                    raise UndefinedError(arg.value)

                                argument_values.append(
                                    {"type": val.type, "value": val.value})
                            else:
                                # constants are allowed as arguments to a function so their type need to be converted
                                # from a literal to the respective keyword type
                                argument_values.append(
                                    {"type": Types.LITERAL_TO_VAR[arg.type], "value": arg.value})

                        # if the number of arguments in this command is greater than the number of parameters in the function + 1,
                        # consider the last argument to be the return value
                        if(len(command.arguments[1:]) > len(func.arguments)):
                            ret_var = command.get_argument_raw(-1)

                            if(not STACK.is_stack_variable(ret_var.value)):
                                raise UndefinedError(ret_var.value)

                            ret_var = STACK.get_stack_variable(ret_var.value)

                            if(ret_var.type not in Types.ANY_VAR):
                                raise InvalidArgumentTypeError(command.name, len(
                                    func.arguments), Types.ANY_VAR, ret_var.type)

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


def cache_imported_arguments(arguments, file):
    file = Path(file)
    name = file.name.replace(file.suffix, "")
    c_name = f"{name}-af.afc"

    raw_code = open(file, "r")
    raw_file_md5sum = hashlib.md5(raw_code.read().encode()).hexdigest()
    raw_code.close()

    # open gzip file and write hash and pickled data
    with gzip.open(CACHE_FOLDER / c_name, "wb") as f:
        f.write(raw_file_md5sum.encode() + pickle.dumps(arguments))


def is_cache_up_to_date(file):
    file = Path(file)
    name = file.name.replace(file.suffix, "")
    c_name = f"{name}-af.afc"

    if(not (CACHE_FOLDER / c_name).exists()):
        return False

    with gzip.open(CACHE_FOLDER / c_name, "rb") as f:
        # md5 hash always 32 characters long
        md5sum = f.read()[0:32].decode()

        raw_code = open(file, "r")
        raw_file_md5sum = hashlib.md5(raw_code.read().encode()).hexdigest()
        raw_code.close()

        # gets the stored md5 hash and the (new) hash of the file
        # if they are equal the file hasnt changed

        return md5sum == raw_file_md5sum


def get_cached_import_arguments(file):
    file = Path(file)
    name = file.name.replace(file.suffix, "")
    c_name = f"{name}-af.afc"

    with gzip.open(CACHE_FOLDER / c_name, "rb") as f:
        # skip the md5 hash (32 characters)
        return pickle.loads(f.read()[32:])
