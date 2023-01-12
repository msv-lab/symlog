import itertools
import common
from souffle import Literal
from typing import List, Dict, Set, Any
from souffle import String, Number, Variable
import os


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


def convert_dict_values_to_sets(my_dict):
    # Convert each value in the dictionary to a set and join the keys with a comma
    return {','.join([i.value for i in k]): set([i.value for i in v]) for k, v in my_dict.items()}


def read_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            content = f.read()
        return content
    else:
        raise ValueError(f"{file_path} does not exist.")


def is_arg_symbolic(arg: String|Number) -> bool:
    '''Returns True if the argument is a symbolic constant/number/binding variable.'''
    if isinstance(arg, String):
        return arg.value.startswith(common.SYMBOLIC_CONSTANT_PREFIX)
    elif isinstance(arg, Number):
        return arg.value in common.SYMLOG_NUM_POOL
    elif isinstance(arg, Variable):
        return arg.name.startswith(common.BINDING_VARIABLE_PREFIX)
    elif isinstance(arg, str) and not is_number(arg):
        return arg.startswith(common.SYMBOLIC_CONSTANT_PREFIX)
    elif isinstance(arg, str) and is_number(arg):
        return int(arg) in common.SYMLOG_NUM_POOL
    else:
        return False

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def is_sublist(list1, list2) -> bool:
    '''Returns True if list1 is a sublist of list2.'''
    return all(item in list2 for item in list1)


def lists_intersect(list1, list2):
    '''Returns True if list1 and list2 have at least one element in common.'''
    return any(elem in list2 for elem in list1)


def store_graph(graph, file_path: str):
    import networkx as nx
    import matplotlib.pyplot as plt

    pos = nx.spring_layout(graph)
    nx.draw(graph, pos, with_labels=True, font_size=5)
    edge_labels = nx.get_edge_attributes(graph, common.DEFAULT_GRAPH_ATTR_NAME) 
    formatted_edge_labels = {(elem[0],elem[1]):edge_labels[elem] for elem in edge_labels} # use this to modify the tuple keyed dict if it has > 2 elements, else ignore
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=formatted_edge_labels,font_color='red')
    plt.savefig(file_path)


def write_file(content: str, file_path: str):
    with open(file_path, 'w') as f:
        f.write(content)


def rename_files(dir_path: str, old: str, new: str) -> None:
    for filename in os.listdir(dir_path):
        if old in filename:
            os.rename(os.path.join(dir_path, filename), os.path.join(dir_path, filename.replace(old, new)))


def remove_empty_files(dir_path: str) -> None:
    for f in os.listdir(dir_path):
        if os.path.getsize(os.path.join(dir_path, f)) == 0:
            os.remove(os.path.join(dir_path, f))

    