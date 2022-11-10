from collections import namedtuple
from typing import Union

# declarations: name -> argument types
# output: list of names
# rules: list of rules
Program = namedtuple('Program', ['declarations', 'inputs', 'outputs', 'rules'])
Rule = namedtuple('Rule', ['head', 'body'])
Literal = namedtuple('Literal', ['name', 'args', 'positive'])
Unification = namedtuple('Unification', ['left', 'right', 'positive'])
Variable = namedtuple('Variable', ['name'])
String = namedtuple('String', ['value'])
Number = namedtuple('Number', ['value'])
Term = Union[Variable, String, Number]