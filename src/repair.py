import re
import os
import shutil
import networkx as nx
from typing import List, Callable, Dict
import functools
import itertools
import common
import utils
from souffle import parse, pprint, Literal, Program


def extract_facts_around_bug(bug_id: str, the_bug_fact: str, data_path: str) -> List[str]:
    function_pattern = re.compile(r'\<.*?\>')
    function_name = function_pattern.findall(the_bug_fact)[0] # The first is the function where the bug raised

    SPU_EDB_PATH = os.path.join(os.getcwd(), 'tmp', 'spurious_database', bug_id)

    # Remove the directory if it already exists
    if os.path.exists(SPU_EDB_PATH):
        shutil.rmtree(SPU_EDB_PATH)

    # Create the directory
    os.makedirs(SPU_EDB_PATH)

    TARGET_FILENAME_LIST = ['VarPointsTo.csv']

    def line_in_target_function(line: str, ext: str) -> bool|None:
        if ext == '.facts':
            matches = function_pattern.findall(line)
            return matches and matches[0] == function_name
        elif ext == '.csv':
            return function_name in line
        else:
            raise ValueError(f'Unknown file extension {ext}.')

    def line_does_not_contain_tmpvar(line: str, filename: str) -> bool:
        if filename in TARGET_FILENAME_LIST:
            return common.SHIMPLE_TEMP_VAR_PREFIX not in line
        return True

    # Filter the lines in the input file
    def filter_lines(lines: List[str], f: Callable) -> List[str]:
        target_lines = set([line for line in lines if f(line)])
        return target_lines

    # Process the files in the data_path directory
    def process_file(filename: str) -> int:
        count_lines = 0
        full_path = os.path.join(data_path, filename)
        extension = os.path.splitext(filename)[1]
        with open(full_path, 'r') as fact_file:
            lines = fact_file.readlines()
            target_lines = filter_lines(lines, lambda line: line_in_target_function(line, extension))
            target_lines = filter_lines(target_lines, lambda line: line_does_not_contain_tmpvar(line, filename))
            if target_lines:  # If the target_lines is not empty then write the lines to the new file
                new_file_path = os.path.join(SPU_EDB_PATH, filename)
                with open(new_file_path, 'w') as new_fact_file:
                    new_fact_file.writelines(target_lines)
                    count_lines += len(target_lines)
        return count_lines


    cnt_line = sum(process_file(f) for f in os.listdir(data_path) if f.endswith('.facts') or f.endswith('.csv'))

    print(f'Extracted facts are stored at {SPU_EDB_PATH}.')
    print('{} facts in total.'.format(cnt_line))


def create_precedence_graph(dl_program_path: str, store_graph=True) -> nx.DiGraph:
    program_text = utils.read_file(dl_program_path)
    program = parse(program_text)

    # Create a precedence graph for the program
    precedence_graph =  nx.DiGraph()
    for rule in program.rules:
        if not rule.body:
            continue
        for body_literal in rule.body:
            if not isinstance(body_literal, Literal):
                continue
            precedence_graph.add_edge(body_literal.name, rule.head.name, label=common.POS_LIT_LABEL if body_literal.positive else common.NEG_LIT_LABEL) #FIXME: label is based on common.DEFAULT_GRAPH_ATTR_NAME

    if store_graph:
        utils.store_graph(precedence_graph, os.path.join(os.getcwd(), 'tmp','precedence_graph.png'))

    return precedence_graph


def partition_to_strata(dl_program_path: str) -> List[Dict[str, List[str]]]:
    # Create the precedence graph
    precedence_graph = create_precedence_graph(dl_program_path)

    def create_leq_graph(precedence_graph: nx.DiGraph):
        # Get constants from the common module
        intrinsic_preds = common.SOUFFLE_INTRINSIC_PREDS
        default_attr_name = common.DEFAULT_GRAPH_ATTR_NAME
        pos_lit_label = common.POS_LIT_LABEL

        # Extract the <= relations from the precedence graph
        leq_relations = [(n1, n2) for n1, n2, data in precedence_graph.edges(data=True)
                        if n1 not in intrinsic_preds and n2 not in intrinsic_preds
                        and data[default_attr_name] == pos_lit_label]

        # Extract the < relations from the precedence graph
        le_relations = [(n1, n2) for n1, n2, data in precedence_graph.edges(data=True)
                        if n1 not in intrinsic_preds and n2 not in intrinsic_preds
                        and data[default_attr_name] != pos_lit_label]

        leq_graph = nx.Graph(leq_relations)

        def remove_edge_if_exists(graph: nx.Graph, node1: str, node2: str):
            if graph.has_edge(node1, node2):
                graph.remove_edge(node1, node2)

        for n1, n2 in le_relations:
            n2_cc = nx.node_connected_component(leq_graph, n2)
            for n in set(precedence_graph.successors(n1)) & n2_cc:
                remove_edge_if_exists(leq_graph, n1, n)

        return leq_graph

    def get_stratum_info(precedence_graph, cc):
        schs = set(cc)
        schs = schs | set(itertools.chain.from_iterable(precedence_graph.predecessors(node) for node in cc)) - common.SOUFFLE_INTRINSIC_PREDS # filter out intrinsic preds
        edbs = set(n for n in schs if not precedence_graph.in_degree(n) or not (set(precedence_graph.predecessors(n)) & schs - {n})) - common.SOUFFLE_INTRINSIC_PREDS # filter out intrinsic preds
        return {common.DL_SCHS: schs, common.DL_EDBS: edbs}

    def compare(x, y):
        if (x[common.DL_SCHS] - x[common.DL_EDBS]) & y[common.DL_EDBS]: # stratum x is prior to stratum y
            return -1
        elif (y[common.DL_SCHS] - y[common.DL_EDBS]) & x[common.DL_EDBS]: # stratum y is prior to stratum x
            return 1
        else:
            return 0

    def process_stratum(stratum):
        program = parse(utils.read_file(dl_program_path))

        rules = [rule for rule in program.rules if rule.head.name in (stratum[common.DL_SCHS] - stratum[common.DL_EDBS])]
        declarations = {decl: val for decl, val in program.declarations.items() if decl in stratum[common.DL_SCHS]}
        outputs = [output for output in program.outputs if output in stratum[common.DL_SCHS]]
        inputs = [input for input in program.inputs if input in stratum[common.DL_SCHS]]

        return pprint(Program(declarations, inputs, outputs, rules))

    def store_stratum(idx, stratum):
        program_text = process_stratum(stratum)
        utils.store_file(program_text, os.path.join(os.getcwd(), 'tmp', f'stratum_{idx}.dl'))
        print(f'Stratum {idx} is stored at {os.path.join(os.getcwd(), "tmp", f"stratum_{idx}.dl")}')

    # Create leq graph (<= relations)
    leq_graph = create_leq_graph(precedence_graph)
    # Get strata info from the leq graph
    strata_list = list(map(lambda cc: get_stratum_info(precedence_graph, cc), nx.connected_components(leq_graph)))
    # sort strata from top to bottom
    sorted_strata = sorted(strata_list, key=functools.cmp_to_key(compare), reverse=True)
    for idx, stratum in enumerate(sorted_strata):
        store_stratum(len(sorted_strata) - idx, stratum)

    return sorted_strata


if __name__ == '__main__':

    the_bug_fact = '<org.jfree.chart.plot.XYPlot: org.jfree.data.Range getDataRange(org.jfree.chart.axis.ValueAxis)>	92	4493	<org.jfree.chart.plot.XYPlot: org.jfree.data.Range getDataRange(org.jfree.chart.axis.ValueAxis)>/r#_4473	Virtual Method Invocation'

    data_path = '/home/liuyu/info3600-bugchecker-benchmarks/digger/out/jfreechart-1.2.0-pre1/database'

    bug_id = 'chart4'

    # extract_facts_around_bug(bug_id, the_bug_fact, data_path)

    partition_to_strata('may-cfg.dl')
