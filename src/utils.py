import itertools
import common
from souffle import Literal
from typing import List, Dict, Set, Any


def remove_false_dict_values(d: Dict[Any, Any]) -> Dict[Any, Any]:
    return {k: v for k, v in d.items() if v}


def flatten_dict(d: Dict[Any, Set[Any]|List[Any]]) -> Dict[Any, Any]:
    return {k: list(itertools.chain(*v)) for k, v in d.items()}


def list_to_str(l: List[Any]) -> str:
    return common.LEFT_SQUARE_BRACKET + common.DELIMITER.join([str(x) for x in l]) + common.RIGHT_SQUARE_BRACKET


def split_into_chunks(a: List[Any], n: int) -> List[List[Any]]:
    k, m = divmod(len(a), n)
    return list(a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))


def hash_literal(literal: Literal) -> int:
    return hash(literal.name) + hash(tuple(literal.args)) + hash(literal.positive)