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

# The special basic symbolic value
ALPHA = '^a^'
VAR = 't'
DOMAIN = 'domain_'

SYMBOLIC_CONSTANT_PREFIX = '_symlog_symbolic_'
BINDING_VARIABLE_PREFIX = '_symlog_binding_'
DOMAIN_PREDICATE_PREFIX = '_symlog_domain_'


