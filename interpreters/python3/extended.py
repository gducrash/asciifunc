from typing import Union


def get_flipped_sign(num, sign):
    if(num >= 0 and sign):
        return "+"
    elif(num < 0 and sign):
        return "-"

    return ""


class SignedFloat(float):

    def __new__(self, num: float, sign: str = ""):
        return float.__new__(self, num)

    def __init__(self, num: float, sign: str = "") -> None:
        self.num = float(num)
        self.sign = sign

    def get_sign(self) -> str:
        return self.sign

    def clamp(self, _min: int, _max: int):
        num = max(_min, min(self.num, _max))
        return SignedFloat(num, get_flipped_sign(num, self.sign))

    def __mul__(self, other):
        num = super(SignedFloat, self).__mul__(other)
        return SignedFloat(num, get_flipped_sign(num, self.sign))

    __rmul__ = __mul__

    def __add__(self, other) -> int:
        num = super(SignedFloat, self).__add__(other)
        return SignedFloat(num, get_flipped_sign(num, self.sign))

    __radd__ = __add__

    def __sub__(self, other) -> int:
        if(self.sign == "-"):
            return super(SignedFloat, self).__add__(other)
        else:
            num = super(SignedFloat, self).__sub__(other)
            return SignedFloat(num, get_flipped_sign(num, self.sign))

    __rsub__ = __sub__


class SignedInt(int):

    def __new__(self, num: int, sign: str = ""):
        return int.__new__(self, num)

    def __init__(self, num: int, sign: str = "") -> None:
        self.num = int(num)
        self.sign = sign

    def get_sign(self) -> str:
        return self.sign

    def clamp(self, _min: int, _max: int):
        num = max(_min, min(self.num, _max))
        return SignedInt(num, get_flipped_sign(num, self.sign))

    def __mul__(self, other):
        num = super(SignedInt, self).__mul__(other)
        return SignedInt(num, get_flipped_sign(num, self.sign))

    __rmul__ = __mul__

    def __add__(self, other) -> int:
        num = super(SignedInt, self).__add__(other)
        return SignedInt(num, get_flipped_sign(num, self.sign))

    __radd__ = __add__

    def __sub__(self, other) -> int:
        if(self.sign == "-"):
            return super(SignedInt, self).__add__(other)
        else:
            num = super(SignedInt, self).__sub__(other)
            return SignedInt(num, get_flipped_sign(num, self.sign))

    __rsub__ = __sub__


class SignedNum():
    # factory class for the different signed numbers

    def __new__(self, num: Union[float, int, str], sign: str = ""):
        if(isinstance(num, str)):
            num = float(num)

        if(isinstance(num, float)):
            if(num.is_integer()):
                return SignedInt(num, sign)
            else:
                return SignedFloat(num, sign)
        else:
            return SignedInt(num, sign)


class Bool(int):
    # custom bool class to allow for lowercase bools in strings

    def __new__(self, type: bool):
        return int.__new__(self, type)

    def __init__(self, type: bool) -> None:
        self.type = type

    def __invert__(self):
        return Bool(not self.type)

    def __bool__(self) -> bool:
        return bool(self.type)

    def __str__(self) -> str:
        return "true" if(self.type) else "false"
