import itertools
import common
from typing import List, Dict, Set, Any


def remove_false_dict_values(d: Dict[Any, Any]) -> Dict[Any, Any]:
    return {k: v for k, v in d.items() if v}


def flatten_dict(d: Dict[Any, Set[Any]|List[Any]]) -> Dict[Any, Any]:
    return {k: list(itertools.chain(*v)) for k, v in d.items()}


def list_to_str(l: List[Any]) -> str:
    return common.LEFT_SQUARE_BRACKET + common.DELIMITER.join([str(x) for x in l]) + common.RIGHT_SQUARE_BRACKET