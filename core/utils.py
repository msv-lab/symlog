import core.common as common
from core.souffle import String, Number, Variable
from core.ast import Constant
from core.ast import Literal as astLiteral
import itertools
from typing import List, Dict, Set, Any
import os


def flatten_dict(d: Dict[Any, Set[Any]|List[Any]]) -> Dict[Any, Any]:
    return {k: list(itertools.chain(*v)) for k, v in d.items()}


def read_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            content = f.read()
        return content
    else:
        raise ValueError(f"{file_path} does not exist.")


def is_arg_symbolic(arg) -> bool:
    # Returns True if the argument is a symbolic constant/number/binding variable
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
    # Returns True if list1 is a sublist of list2
    return all(item in list2 for item in list1)


def is_lists_intersect(list1, list2):
    # Returns True if list1 and list2 have at least one element in common
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


def convert_relations(facts_dict: dict) -> list:
    # Convert a dictionary of facts to a list of facts
    relations = list()
    for relation_name in facts_dict:
        for args in facts_dict[relation_name]:
            constants = [Constant(arg, common.SOUFFLE_SYMBOL) for arg in args]
            relations.append(astLiteral(relation_name, True, constants=constants))
    return relations


def inv_convert_relations(facts: list|dict) -> dict:
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