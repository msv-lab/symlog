import sys
import os

SYMBOLIC_CONSTANT_PREFIX = 'symlog_symbolic_'
BINDING_VARIABLE_PREFIX = 'symlog_binding_'
DOMAIN_PREDICATE_PREFIX = 'symlog_domain_'
HEAD_RECORD_ARG_PREFIX = '_symlog_head_record_'
BODY_RECORD_ARG_PREFIX = '_symlog_body_record_'
SYMBOLIC_SYMBOL_PLACEHOLDER = 'symlog_symbol_placeholder_'
SYMBOLIC_NUMBER_PLACEHOLDER = 'symlog_number_placeholder_'
SYMLOG_NUM_POOL_SIZE = 1001
SYMLOG_NUM_POOL = [-sys.maxsize + i for i in range(1, SYMLOG_NUM_POOL_SIZE)]


DEFAULT_SOUFFLE_TYPE = 'symbol'
SOUFFLE_SYMBOL = 'symbol'
SOUFFLE_NUMBER = 'number'
SOUFFLE_LOGICAL_OR = ' lor '
SOUFFLE_CONTAINS = 'contains'
SOUFFLE_SUBSTR = 'substr'
SOUFFLE_COMPILE_MODE = 'compile'
SOUFFLE_INTERPRET_MODE = 'interpret'
SOUFFLE_INTRINSIC_PREDS = {SOUFFLE_CONTAINS, SOUFFLE_SUBSTR}

DELIMITER = ', '
EQUAL = ' = '
NEGATION = '!'
NOT_EQUAL = ' != '
EQ_NONEQ = ' eq/neq '
LEFT_SQUARE_BRACKET = '['
RIGHT_SQUARE_BRACKET = ']'

SHIMPLE_TEMP_VAR_PREFIX = '$stack'

DEFAULT_GRAPH_ATTR_NAME = 'label'

POS_LIT_LABEL = '+'
NEG_LIT_LABEL = '-'

DL_SCHS = 'schs'
DL_EDBS = 'edbs'
DL_NEG_EDBS = 'neg_edbs'
DL_UNDERSCORE = '_'

MARKED = 1
UNMARKED = 0

NEG_PREFIX = 'neg_'

POS_QUERY = 'pos_query'
NEG_QUERY = 'neg_query'

TMP_DIR = os.path.join(os.getcwd(), 'tmp')
