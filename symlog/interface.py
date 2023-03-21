import symlog.common as common
import symlog.souffle as souffle
from symlog.utils import read_file
import symlog.souffle as souffle
from symlog.transform_to_meta_program import transform_program

from typing import List, Optional, Union
import itertools
from dataclasses import dataclass


def type_check(type):
    if type not in [common.SOUFFLE_SYMBOL, common.SOUFFLE_NUMBER]:
        raise TypeError('Invalid type: %s' % type)

def sign_check(sign):
    if isinstance(sign, bool) == False:
        raise TypeError('Invalid sign: %s' % sign)

def convert_relations(facts_dict: dict) -> list:
    # Convert a dictionary of facts to a list of facts
    relations = list()
    for relation_name in facts_dict:
        for args in facts_dict[relation_name]:
            constants = [Constant(arg, common.SOUFFLE_SYMBOL) for arg in args]
            relations.append(Literal(relation_name, True, constants=constants))
    return relations

def inv_convert_relations(facts: Union[list, dict]) -> dict:
    # Convert a list of facts to a dictionary of facts
    if isinstance(facts, dict):
        return facts
    facts_dict = dict()
    for fact in facts:
        if fact.name not in facts_dict:
            facts_dict[fact.name] = list()
        args = [constant.value for constant in fact.constants]
        facts_dict[fact.name].append(args)
    return facts_dict


@dataclass
class Constant:
    value: Union[str, int, float]
    type: str


@dataclass
class SymConstant:
    type: str
    value: Optional[Union[str, int, float]] = None

    id_iter = itertools.count()

    def __post_init__(self):
        if self.value is None:
            if self.type == common.SOUFFLE_SYMBOL:
                self.value = f"{common.SYMBOLIC_CONSTANT_PREFIX}{next(self.id_iter)}"
            elif self.type == common.SOUFFLE_NUMBER:
                self.value = common.SYMLOG_NUM_POOL[next(self.id_iter)]
            else:
                raise NotImplementedError

    @classmethod
    def reset_id_iter(cls):
        cls.id_iter = itertools.count()


@dataclass
class Literal:
    name: str
    sign: bool
    constants: List[Union[Constant, SymConstant]]

    def __post_init__(self):
        try:
            sign_check(self.sign)
        except TypeError as e:
            print(e)


class Symlog:
    """ 
    The main class for Symlog.
    Args:
        program_path (str): The path to the Souffle program file.
        database_path (Optional[str]): The path to the Souffle database file, default is None.

    Attributes:
        program (souffle.Program): The Souffle program object.
        input_facts (Dict[str, List[Dict[str, Union[str, int, float]]]]): A dictionary of input facts for the Souffle program.

    Methods:
        transform(): Transforms the input facts for the Souffle program.
        run(): Runs the transformed Souffle program and returns the output.

    Raises:
        FileNotFoundError: If either the program_path or database_path does not exist.

    Notes:
        This class requires the Souffle library to be installed in the system.

    Example:
        >>> symlog = Symlog("path/to/souffle/program.dl", "path/to/souffle/database/facts")
        >>> symlog.run()
        {'relation1': [(value1, value2), (value3, value4)], 'relation2': [(value5), (value6, value7)]}
    """

    def __init__(self, program_path, database_path=None) -> None:
        self.program = souffle.parse(read_file(program_path))
        self.input_facts = convert_relations(souffle.load_relations(database_path)) if not database_path is None else list()
        # reset id iterator for symbolic constants
        SymConstant.reset_id_iter()

    def transform(self):
        self.input_facts = inv_convert_relations(self.input_facts)
        return transform_program(self.program, self.input_facts)

    def run(self):
        return souffle.run_program(self.transform(), self.input_facts)