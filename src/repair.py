import re
import os
import shutil
import networkx as nx
from typing import List, Callable, Dict, Generator, Set, Any, List, Tuple
import functools
import itertools
import argparse
from subprocess import run
import queue
import common
import utils
from souffle import Literal, Program, Rule, parse, pprint, run_program, load_relations
from transform_to_meta_program import transform_for_recording_facts, transform_input_facts, reset_for_recording_facts, transform_program, create_sym_facts, transform_fact_rules


PASS = 0
FAIL = 1


parser = argparse.ArgumentParser(description='Transform Datalog program to meta program.')
parser.add_argument('-p', '--program_path', required=True, help='path to the Datalog program')
parser.add_argument('-d', '--data_path', required=True, help='path to the input facts')


def extract_facts_around_bug(bug_id: str, the_bug_fact: str, data_path: str) -> str:
    function_pattern = re.compile(r'\<.*?\>')
    FUNC_NAME = function_pattern.findall(the_bug_fact)[0] # The first is the function where the bug raised
    CLASS_NAME = FUNC_NAME.replace('<', '').replace('>', '').split(':')[0]

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
            return (matches and matches[0] == FUNC_NAME) or (CLASS_NAME in line and len(line.split('\t'))==1) #FIXME: The second condition is a quick hack for the class name in Applcation.facts
        elif ext == '.csv':
            return FUNC_NAME in line
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
    return SPU_EDB_PATH


def add_neg_prefix(name: str) -> str:
    return f'{common.NEG_PREFIX}{name}'


def gen_facts_by_stratum(ori_program_path: str, strata: List[Dict[str, List[str]]], data_dir: str) -> str:
    '''Generate fatcs for each stratum.
    Args:
        p: The original Datalog program (cleaned for transformation)
        strata: The strata of the program
    Returns:
        The path to the directory containing the extracted facts'''
    
    if not os.path.exists(data_dir):
        raise ValueError(f'The directory {data_dir} storing original facts does not exist.')

    ori_program = parse(utils.read_file(ori_program_path))

    def record_neg_tuple_rule(rule: Rule) -> Rule:
        for lit in rule.body:
            if isinstance(lit, Literal) and not lit.positive:
                return Rule(Literal(add_neg_prefix(lit.name), lit.args, True), rule.body)
        return None

    # rules for storing complementary facts of negative literals
    rules = list(filter(lambda x: x, [record_neg_tuple_rule(rule) for rule in ori_program.rules]))

    # update declarations
    declarations = ori_program.declarations | {
        add_neg_prefix(decl): val
        for decl, val in ori_program.declarations.items() 
        if decl in itertools.chain(*[stratum[common.DL_NEG_EDBS] for stratum in strata])
    }

    # outputs of each stratum. Do not keep original outputs
    outputs = list(set(itertools.chain(*[stratum[common.DL_EDBS] for stratum in strata])) | set(add_neg_prefix(edb) for stratum in strata for edb in stratum[common.DL_NEG_EDBS]))

    # inputs are real edbs
    inputs = strata[0][common.DL_EDBS]

    updated_program = Program(declarations, inputs, outputs, ori_program.rules + rules)

    # write the program to a file
    updated_program_path = os.path.join(data_dir, 'program_w_oup.dl')
    utils.store_file(pprint(updated_program), updated_program_path)

    # preprocess the csv files to facts files
    utils.rename_files(data_dir, 'csv', 'facts')
    utils.rename_files(data_dir, '-', '_')

    cmd = ["souffle", "-F", data_dir, "-D", data_dir, updated_program_path, "-w", "--jobs=auto"]
    run(cmd) # generate facts for each stratum
    print(f'Facts for each stratum are stored at {data_dir}.')
    return data_dir


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

        def remove_edge_if_exists(graph: nx.Graph, node1: str, node2: str) -> None:
            if graph.has_edge(node1, node2):
                graph.remove_edge(node1, node2)

        for n1, n2 in le_relations:
            n2_cc = nx.node_connected_component(leq_graph, n2)
            for n in set(precedence_graph.successors(n1)) & n2_cc:
                remove_edge_if_exists(leq_graph, n1, n)

        return leq_graph

    def get_stratum_info(precedence_graph: nx.DiGraph, cc: Generator[Set, None, None]) -> Dict[str, Set[str]]:
        schs = set(cc)
        schs = schs | set(itertools.chain.from_iterable(precedence_graph.predecessors(node) for node in cc)) - common.SOUFFLE_INTRINSIC_PREDS # filter out intrinsic preds
        edbs = set(n for n in schs if not precedence_graph.in_degree(n) or not (set(precedence_graph.predecessors(n)) & schs - {n})) - common.SOUFFLE_INTRINSIC_PREDS # n's predecessors are all not in stratum's schs

        # extract negative edbs which are negated at least in one rule.
        neg_edbs = {n1 for n1, _, data in precedence_graph.edges(data=True)
                        if n1 not in common.SOUFFLE_INTRINSIC_PREDS and data[common.DEFAULT_GRAPH_ATTR_NAME] != common.POS_LIT_LABEL}

        return {common.DL_SCHS: schs, common.DL_EDBS: edbs, common.DL_NEG_EDBS: neg_edbs}

    def compare(x, y):
        if (x[common.DL_SCHS] - x[common.DL_EDBS]) & y[common.DL_EDBS]: # stratum x is prior to stratum y
            return -1
        elif (y[common.DL_SCHS] - y[common.DL_EDBS]) & x[common.DL_EDBS]: # stratum y is prior to stratum x
            return 1
        else:
            return 0

    def process_stratum(stratum: Dict[str, Set[str]]) -> str:
        program = parse(utils.read_file(dl_program_path))

        # replace negative literal with its complementary positive literal
        def replace_neg_body_literals(rule: Rule) -> Rule:
            def replace_neg_literal(literal: Literal) -> Literal:
                if isinstance(literal, Literal) and not literal.positive:
                    return Literal(add_neg_prefix(literal.name), literal.args, True)
                return literal

            body = tuple(map(replace_neg_literal, rule.body))
            return Rule(rule.head, body)

        rules = [replace_neg_body_literals(rule) for rule in program.rules if rule.head.name in (stratum[common.DL_SCHS] - stratum[common.DL_EDBS])]

        declarations = program.declarations | {
            add_neg_prefix(decl): val
            for decl, val in program.declarations.items()
            if decl in stratum[common.DL_NEG_EDBS]
        }

        outputs = [output for output in program.outputs if output in stratum[common.DL_SCHS]]
        inputs = [input for input in program.inputs if input in stratum[common.DL_SCHS]]

        return pprint(Program(declarations, inputs, outputs, rules))

    def store_stratum(idx: int, stratum: Dict[str, Set[str]]) -> None:
        program_text = process_stratum(stratum)
        utils.store_file(program_text, os.path.join(os.getcwd(), 'tmp', f'stratum_{idx}.dl'))
        print(f'Stratum {idx} is stored at {os.path.join(os.getcwd(), "tmp", f"stratum_{idx}.dl")}')

    # Create leq graph (<= relations)
    leq_graph = create_leq_graph(precedence_graph)
    # Get strata info from the leq graph
    strata_list = [get_stratum_info(precedence_graph, cc) for cc in nx.connected_components(leq_graph)]
    # sort strata from top to bottom
    sorted_strata = sorted(strata_list, key=functools.cmp_to_key(compare), reverse=True)
    for idx, stratum in enumerate(sorted_strata):
        store_stratum(len(sorted_strata) - idx, stratum)

    return sorted_strata


def is_target_in_outputs(inp_fact_rules: List[Rule], p: Program, target_tuples: List[Rule], num: int) -> int:
    """Test whether the program p produces the target tuples."""

    # append the inputs to the program
    p = Program(p.declarations, p.inputs, p.outputs, p.rules + inp_fact_rules)
    # run program
    output_relations = run_program(p, [])

    values =  [', '.join(v[:-num]) for v in itertools.chain(*output_relations.values())] # remove the last num values used for recording facts

    # check whether target tuples are derived
    derived = all(tar_tup in values for tar_tup in target_tuples)

    return FAIL if derived else PASS


def ddmin(test: Callable, p: Program, target_tuples: List[Rule], edbs: List[str]) -> Tuple[bool, List[Rule]]:
    """Reduce the input inp, using the outcome of test(fun, inp). p is a program with input facts."""

    n = 2     # Initial granularity
    old_n = 2 # Previous granularity

    rec_p, inp = transform_for_recording_facts(p, n, edbs)

    if test(inp, rec_p, target_tuples, n) == PASS:
        return False, []

    while len(inp) >= 2:
        block_no = 0

        # reset program and inputs
        reset_p = reset_for_recording_facts(rec_p, inp, old_n)

        rec_p, inp = transform_for_recording_facts(reset_p, n, edbs)

        some_complement_is_failing = False

        while block_no < n:
            complement = [f for f in inp if f.head.args[-(n-block_no)].value != common.MARKED]

            if test(complement, rec_p, target_tuples, n) == FAIL:
                inp = complement
                old_n = n
                n = max(n - 1, 2)
                some_complement_is_failing = True
                break

            block_no += 1

        if not some_complement_is_failing:
            if n == len(inp):
                break
            old_n = n
            n = min(n * 2, len(inp))

    return True, inp


def repair(the_bug_fact: List[str], data_path: str, bug_id: str, dl_program_path: str) -> None:

    time_out = 60

    data_dir = extract_facts_around_bug(bug_id, the_bug_fact, data_path)
    strata = partition_to_strata(dl_program_path)

    # get facts for all strata
    facts_dir = gen_facts_by_stratum(dl_program_path, strata, bug_id, data_dir)
    input_facts = load_relations(facts_dir)

    def select_sym_locs(declarations: Dict[str, List[str]], preds: Set[str], forbidden_loc_list: List[Tuple[str, int]], rank: Callable, top_n: int=5) -> List[str]:
        locs = [(pred, i) for pred in preds for i in range(len(declarations[pred])) if (pred, i) not in forbidden_loc_list]
        locs = sorted(locs, key=lambda x: rank(x[0], x[1]), reverse=True)

        return locs[:top_n]

    def contain_queries(results: Dict[str, List[List[str]]], queries: Dict[str, List[List[str]]]) -> bool:
        if not queries:
            return True
        for pred in queries:
            if pred not in results:
                return False
            return utils.is_sublist(queries[pred], results[pred])

    def handle_pos_queries(stratum_p: Program, stratum: Dict[str, Set[str]], forbidden_loc_list: List[Tuple[str, int]], pos_queries: Dict[str, List[List[str]]]):
        # select locs in edbs of stratum for symbolization        
        locs_list = select_sym_locs(stratum_p.declarations, stratum[common.DL_EDBS], forbidden_loc_list, lambda pred, i: 1, 5) # TODO: rank function

        # Create symbolic facts from the selected locations
        sym_facts = create_sym_facts(locs_list, stratum_p.declarations)
        
        # Merge symbolic and input facts
        facts = {k: sym_facts.get(k, []) + input_facts.get(k, []) for k in (input_facts.keys() | sym_facts.keys())}

        # Transform the stratum program with the merged facts
        stratum_trans_p = transform_program(stratum_p, facts)

        # Run the transformed program
        output = run_program(stratum_trans_p, [])

        # Check if the output of the program contains the positive queries
        is_fixed = contain_queries(output, pos_queries)
        if is_fixed:
            is_reduced, key_fact_rules = ddmin(is_target_in_outputs, stratum_trans_p, pos_queries, stratum[common.DL_EDBS]) 
            
            assert is_reduced # the first returned value must be True

            return True, key_fact_rules, locs_list
        return False, [], locs_list

    def handle_neg_queries(stratum_p: Program, stratum: Dict[str, Set[str]], neg_queries: Dict[str, List[List[str]]], rank: Callable, top_n: int=1):

        facts_for_neg_queries = []

        q = queue.Queue()
        is_reduced, reduced_inp_fact_rules = ddmin(is_target_in_outputs, stratum_p, neg_queries, stratum[common.DL_EDBS])

        assert is_reduced

        q.put(reduced_inp_fact_rules)

        while not q.empty():
            inp_facts = q.get()
            
            # save the 1-minimal inp_facts for neg_queries
            facts_for_neg_queries.append(inp_facts)
            
            for fact in inp_facts:
                # remove the fact from new stratum program
                rules = [rule for rule in stratum_p.rules if rule != fact] 
                new_stratum_p = Program(stratum_p.declarations, stratum_p.inputs, stratum_p.outputs, rules)
                
                # check if the new stratum program still can generate neg_queries
                is_reduced, reduced_inp_fact_rules = ddmin(is_target_in_outputs, new_stratum_p, neg_queries, stratum[common.DL_EDBS])

                if is_reduced:
                    q.put(reduced_inp_fact_rules)

        query_rules_for_next_stratum = itertools.chain(*[sorted(inp_facts, key=lambda x: rank(x), reverse=True)[:top_n] for inp_facts in facts_for_neg_queries])

        return query_rules_for_next_stratum

        # reduced_inp_facts = sorted(reduced_inp_facts, key=lambda x: rank(x), reverse=True)

        # return reduced_inp_facts[:top_n]

    def process_fact_rules(added_facts: List[Rule], removed_facts: List[Rule]) -> Dict[str, List[List[str]]]:
        # transform the facts to the format of the output of the program
        added_facts = transform_fact_rules(added_facts)
        removed_facts = transform_fact_rules(removed_facts)

        # place negated facts to corresponding added/removed facts
        to_remove = {k.replace(common.NEG_PREFIX, ''): v for k, v in added_facts.items() if k.startswith(common.NEG_PREFIX)}
        to_add = {k.replace(common.NEG_PREFIX, ''): v for k, v in removed_facts.items() if k.startswith(common.NEG_PREFIX)}

        added_facts = {k: v for k, v in added_facts.items() if not k.startswith(common.NEG_PREFIX)}
        added_facts.update(to_add)

        removed_facts = {k: v for k, v in removed_facts.items() if not k.startswith(common.NEG_PREFIX)}
        removed_facts.update(to_remove) 

        return added_facts, removed_facts

    def repair_by_stratum(stratum: Dict[str, Set[str]], idx: int, queries, forbidden_queries) -> Tuple[bool, Dict[str, List[List[str]]]]:

        pos_queries = queries.get(common.POS_QUERY, None)
        neg_queries = queries.get(common.NEG_QUERY, None)
        forb_loc_list = []

        if pos_queries is None and neg_queries is None:
            print(f'No queries for stratum {idx}.')
            return True, {}

        # get the program of the stratum
        stratum_p = Program.load(os.path.join(common.TMP_DIR, f'stratum_{idx}.dl'))

        while not time_out:
            is_fixed, added_fact_rules, forb_loc_list2 = handle_pos_queries(stratum_p, stratum, forb_loc_list, pos_queries)
            if not is_fixed:
                forb_loc_list = forb_loc_list + forb_loc_list2 
                continue

            removed_fact_rules = handle_neg_queries(stratum_p, stratum, neg_queries, lambda x: x) #TODO: rank the neg queries

            added_facts, removed_facts = process_fact_rules(added_fact_rules, removed_fact_rules)

            if not utils.lists_intersect(added_facts, removed_facts):
                queries_for_next_stratum = {common.POS_QUERY: added_facts, common.NEG_QUERY: removed_facts}

                if utils.lists_intersect(added_facts, forbidden_queries[common.POS_QUERY]) or utils.lists_intersect(removed_facts, forbidden_queries[common.NEG_QUERY]):
                    continue

                return True, queries_for_next_stratum, {}
            else:
                forb_loc_list = forb_loc_list + forb_loc_list2

        return False, {}, queries

    stratum_no = len(strata) - 1
    queries = {common.POS_QUERY: [], common.NEG_QUERY: {'ReachableNullAtLine':[the_bug_fact]}}
    forbidden_queries = {common.POS_QUERY: [], common.NEG_QUERY: []}

    queries_of_strata = [{} for _ in range(len(strata))]

    # repair by stratum
    while not time_out:
        fixed, queries_for_next_stratum, forbidden_queries = repair_by_stratum(strata[stratum_no], stratum_no, queries, forbidden_queries)
        
        queries_of_strata.insert(stratum_no, queries)

        if fixed:
            stratum_no -= 1
            queries = queries_for_next_stratum
            if stratum_no < 0:
                return queries
        else:
            stratum_no += 1
            queries = queries_of_strata[stratum_no]


if __name__ == '__main__':

    the_bug_fact = '<org.jfree.chart.plot.XYPlot: org.jfree.data.Range getDataRange(org.jfree.chart.axis.ValueAxis)>	92	4493	<org.jfree.chart.plot.XYPlot: org.jfree.data.Range getDataRange(org.jfree.chart.axis.ValueAxis)>/r#_4473	Virtual Method Invocation'

    data_path = '/home/liuyu/info3600-bugchecker-benchmarks/digger/out/jfreechart-1.2.0-pre1/database'

    bug_id = 'chart4'

    DATA_DIR = extract_facts_around_bug(bug_id, the_bug_fact, data_path)
    # DATA_DIR = "/home/liuyu/symlog/tmp/spurious_database/chart4"

    strata = partition_to_strata('may-cfg.dl')

    gen_facts_by_stratum('may-cfg.dl', strata, bug_id, DATA_DIR)

    # edbs_list = [stratum[common.DL_EDBS] for stratum in strata]
    fact_names = strata[0][common.DL_EDBS]
    program = parse(utils.read_file("tmp/stratum_2.dl"))

    input_facts = load_relations(DATA_DIR)

    fact_rules = transform_input_facts(input_facts, program.declarations)
    program.rules.extend(fact_rules)

    tar_tuple =  ", ".join(the_bug_fact.split("\t")) 
    target_tuples = [tar_tuple]

    _, tar_inp = ddmin(is_target_in_outputs, program, target_tuples, fact_names)

    for i in tar_inp:
        print(i)

    # transfromed_p = parse(utils.read_file("tests/small_transformed_program.dl"))

    # n = 2

    # transformed, facts = transform_for_recording_facts(transfromed_p, n, fact_names)

    # utils.store_file(pprint(transformed), "tests/transformed_record_program.dl")

    # print("transformed program for recording facts is stored in tests/transformed_record_program.dl")