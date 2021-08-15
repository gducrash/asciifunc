class Errors():
    STRICT = False

    @staticmethod
    def set_strict(value):
        Errors.STRICT = value


class SkipCommandError(Exception):
    # used to skip a command

    def __init__(self):
        super().__init__("")


class UndefinedError(Exception):
    # raised if a variable is undefined

    def __init__(self, var_name: str):
        self.message = f"`{var_name}` was used before definition."

        if(Errors.STRICT):
            super().__init__(self.message)
        else:
            raise SkipCommandError


class AlreadyDefinedError(Exception):
    # raised if a variable is already defined

    def __init__(self, var_name: str):
        self.message = f"`{var_name}` has already been defined."

        if(Errors.STRICT):
            super().__init__(self.message)
        else:
            raise SkipCommandError


class UknownTypeError(Exception):
    # raised for an uknown variable type

    def __init__(self, type: str):
        self.message = f"Uknown type `{type}`"

        if(Errors.STRICT):
            super().__init__(self.message)
        else:
            raise SkipCommandError


class InvalidVariableTypeError(Exception):
    # raised when trying to assign to a variable of a different type

    def __init__(self, curr_type: str, actual_type: str):
        self.message = f"Cannot assign type `{curr_type}` to variable of type `{actual_type}`."

        if(Errors.STRICT):
            super().__init__(self.message)
        else:
            raise SkipCommandError


class InvalidArgumentTypeError(Exception):
    # raised when trying to call a method with an argument of a different type

    def __init__(self, name: str, arg_num: int, actual_type, curr_type: str):
        self.message = f"Argument {arg_num} of `{name}` must be of type `{actual_type}`, not `{curr_type}`."

        if(Errors.STRICT):
            super().__init__(self.message)
        else:
            raise SkipCommandError


class ArgumentNumberError(Exception):
    # raised when there is too many / too little arguments in a method call

    def __init__(self, name: str, range: list[int], given_num: int):
        self.message = f"`{name}` takes between {range[0]} and {range[1]} arguments. {given_num} were given."

        if(Errors.STRICT):
            super().__init__(self.message)
        else:
            raise SkipCommandError


class ImportError(Exception):
    # raised if a variable is undefined

    def __init__(self, file_name: str):
        self.message = f"Unable to import file: `{file_name}`."

        if(Errors.STRICT):
            super().__init__(self.message)
        else:
            raise SkipCommandError
