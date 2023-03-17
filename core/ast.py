import core.common as common
from typing import List
import itertools

def type_check(type):
    if type not in [common.SOUFFLE_SYMBOL, common.SOUFFLE_NUMBER]:
        raise TypeError('Invalid type: %s' % type)

def sign_check(sign):
    if isinstance(sign, bool) == False:
        raise TypeError('Invalid sign: %s' % sign)


class Constant:
    """Represents a constant value in Souffle program.

    Args:
        value (Union[str, int, float]): The value of the constant.
        type (str): The type of the constant.

    Raises:
        TypeError: If the type of the constant is not valid.

    Attributes:
        value (Union[str, int, float]): The value of the constant.
        type (str): The type of the constant.
    """

    def __init__(self, value: str|int|float, type: str) -> None:
        self.value = value
        self.type = type        
        try:
            type_check(self.type)
        except TypeError as e:
            print(e)


class SymConstant:
    """Represents a symbolic constant in Souffle program.

    Args:
        type (str): The type of the constant.
        value (Optional[Union[str, int, float]]): The value of the constant, default is None.

    Raises:
        NotImplementedError: If the given type is not implemented.

    Attributes:
        type (str): The type of the constant.
        value (Union[str, int, float]): The value of the constant.

    Class Attributes:
        id_iter (itertools.count): An iterator that generates unique identifiers for new instances of SymConstant.

    Class Methods:
        reset_id_iter(): Resets the id_iter to its initial value.
    """

    id_iter = itertools.count()
    
    def __init__(self, type, value=None) -> None:
        self.type = type
        if value == None:
            if type == common.SOUFFLE_SYMBOL:
                self.value = f"{common.SYMBOLIC_CONSTANT_PREFIX}{next(self.id_iter)}"
            elif type == common.SOUFFLE_NUMBER:
                self.value = common.SYMLOG_NUM_POOL[next(self.id_iter)]
            else:
                raise NotImplementedError
        else:
            self.value = value
    
    @classmethod
    def reset_id_iter(cls):
        cls.id_iter = itertools.count()


class Literal:
    """Represents a literal in a Souffle rule.

    Args:
        name (str): The name of the literal.
        sign (bool): The sign of the literal.
        constants (List[Union[Constant, SymConstant]]): The list of constants in the literal.

    Raises:
        TypeError: If the sign of the literal is not a boolean.

    Attributes:
        name (str): The name of the literal.
        sign (bool): The sign of the literal.
        constants (List[Union[Constant, SymConstant]]): The list of constants in
        the literal.
    """

    def __init__(self, name: str, sign: bool, constants: List[Constant|SymConstant]) -> None:
        self.name = name
        self.sign = sign
        self.constants = constants
        try:
            sign_check(self.sign)
        except TypeError as e:
            print(e)