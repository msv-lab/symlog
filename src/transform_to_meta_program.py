import common
from souffle import collect, transform, parse, pprint, Variable, Literal, Rule, String, Number, Program, Unification, load_relations
import utils

from typing import Any, List, Dict, Set, Tuple, Optional, DefaultDict, Union
import itertools
from collections import defaultdict
import pytest
import os
import argparse
import copy


parser = argparse.ArgumentParser(description='Transform Datalog program to meta program.')
parser.add_argument('-p', '--program_path', required=True, help='path to the Datalog program')
parser.add_argument('-d', '--data_path', required=True, help='path to the input facts')

DEBUG = False


def extract_pred_symconsts_pair(fact: Rule) -> Tuple[str, List[String]]:
    # get the name of the predicate
    pred_name = fact.head.name

    # get the list of symbolic constants in the predicate arguments
    symbolic_consts = [arg for arg in fact.head.args if utils.is_arg_symbolic(arg)]

    return pred_name, symbolic_consts


def group_pred_consts_list(facts, f):
    d = defaultdict(list)
    for k, v in list(map(f, facts)):
        if v:
            d[k].append(v)
    return d


def transform_for_recording_facts(
    p: Program, num: int, fact_heads: List[Literal]
) -> Program:
    """Transforms a program to a program that can record facts.

    This transformation is used to make the given program can record facts in a manner of adding new arguments to the head of each rule. The new arguments are used to record the facts.

    Args:
        p: The program to transform.
        num: The number of blocks that facts to be partitioned to.
        fact_heads: The heads of facts to be partitioned.

    Returns:
        A program that records facts.
    """

    fact_head_blocks = utils.split_into_chunks(fact_heads, num)

    fact_head_id_map = {
        utils.hash_literal(fact_head): [0 if i != bno else 1 for i in range(num)]
        for bno, fact_block in enumerate(fact_head_blocks)
        for fact_head in fact_block
    }

    def add_record_args(literal: Literal) -> Literal:
        return Literal(
            literal.name,
            literal.args
            + [
                Variable(f"{literal.name}{common.RECORD_ARG_PREFIX}{i}")
                for i in range(1, 1 + num)
            ],
            literal.positive,
        )

    def add_id_args(literal: Literal, id_args: List[int]) -> Literal:
        return Literal(
            literal.name,
            literal.args + [Number(id_arg) for id_arg in id_args],
            literal.positive,
        )

    def add_record_components(n: Any) -> Any:
        if isinstance(n, Rule) and n.body:
            rule = n
            head_hash = utils.hash_literal(rule.head)
            if head_hash not in fact_head_id_map:  # not a fact

                head_record_args = [
                    Variable(f"{rule.head.name}{common.RECORD_ARG_PREFIX}{i}")
                    for i in range(1, 1 + num)
                ]

                # store record args in columns (instead of rows)
                # TODO: The program for finding all paths should not contain negative literals. Let's keep this for now.
                body_record_argnames_list = [
                    [
                        f"{literal.name}{common.RECORD_ARG_PREFIX}{i}"
                        for literal in rule.body
                        if not literal.name.startswith(common.DOMAIN_PREDICATE_PREFIX)
                        and literal.positive
                    ]
                    for i in range(1, 1 + num)
                ]

                # construct unifications, e.g., t1 = t1'|t1'' ...
                unifications = [
                    Unification(
                        hrarg,
                        Variable(common.SOUFFLE_LOGICAL_OR.join(brargnames)),
                        True,
                    )
                    for hrarg, brargnames in zip(
                        head_record_args, body_record_argnames_list
                    )
                ]

                return Rule(
                    add_record_args(rule.head),
                    [add_record_args(literal) for literal in rule.body] + unifications,
                )

            else:  # a fact
                return Rule(
                    add_id_args(rule.head, fact_head_id_map[head_hash]), rule.body
                )

        return n

    transformed = transform(p, add_record_components)

    return transform(p, add_record_components)


def analyse_symbolic_constants(
    p: Program,
) -> Dict[Tuple[Set[Union[String, Number]]], Set[Union[String, Number]]]:
    """Analyse the constansts that symbolic constants in program `p` in principle attempt to unify with during evaluation."""

    rules = collect(p, lambda x: isinstance(x, Rule))

    Loc = Tuple[str, int]  # loc: (pred_name, index)
    Value = Union[String, Number]
    LocValuesDict = DefaultDict[Loc, Set[Value]]
    LocLocsDict = DefaultDict[Loc, Set[Loc]]

    def init_maps(
        rules: List[Rule],
    ) -> Tuple[LocValuesDict, LocValuesDict, LocLocsDict, LocLocsDict]:

        # loc -> set of values that variable at loc can take
        loc_values_map: LocValuesDict = defaultdict(set)
        # loc in edb -> set of symbolic values that variable at loc can take
        eloc_symvalues_map: LocValuesDict = defaultdict(set)
        # loc in head -> set of locs in body that share the same variable as loc
        # in head
        hloc_pos_blocs_map: DefaultDict[Loc, Set[Loc]] = defaultdict(set)
        # loc of sym const in edb -> set of locs where variables try to unified
        # with sym const
        symloc_unifiable_locs_map: DefaultDict[Loc, Set[Loc]] = defaultdict(set)

        def var_in_pos_lit(arg: Union[Variable, String, Number], lit: Literal) -> bool:
            if isinstance(arg, Variable) and isinstance(lit, Literal) and arg in lit.args and lit.positive:
                return True
            return False

        def find_arg_at_loc(
            loc: Loc, rule: Rule
        ) -> Optional[Union[String, Number, Variable]]:
            pred_name, idx = loc
            for l in rule.body:
                if isinstance(l, Literal) and l.name == pred_name:
                    return l.args[idx]
            return None

        def find_unifiable_locs_of_arg(
            arg: Union[Variable, String, Number], lits: List[Literal]
        ) -> Set[Loc]:
            locs = set()
            for lit in lits:
                if var_in_pos_lit(arg, lit):  # only positive literals
                    locs.add((lit.name, lit.args.index(arg)))
            return locs

        def add_hloc_pos_blocs(rule: Rule) -> None:
            if not rule.body:
                return  # skip facts.
            for i, arg in enumerate(rule.head.args):
                hloc = (rule.head.name, i)
                hloc_pos_blocs_map[hloc].update(
                    set(
                        [
                            (body_lit.name, body_lit.args.index(arg))
                            for body_lit in rule.body
                            if var_in_pos_lit(arg, body_lit)
                        ]
                    )
                )  # only positive literals

        def add_loc_values(rule: Rule) -> None:
            if not rule.body:  # rule is a fact.
                for i, arg in enumerate(rule.head.args):
                    # store loc, and corresp value in fact
                    loc_values_map[(rule.head.name, i)].add(arg)

                    # when value is symbolic, add loc, value to
                    # eloc_symvalues_map
                    if utils.is_arg_symbolic(arg):
                        eloc_symvalues_map[(rule.head.name, i)].add(arg)
            else:
                for lit in [rule.head] + [l for l in rule.body if isinstance(l, Literal)]:
                    for i, arg in enumerate(lit.args):
                        if isinstance(arg, String) or isinstance(arg, Number):
                            # store loc, and corresp constant appearing in rules
                            loc_values_map[(lit.name, i)].add(arg)

        # initilize loc_values_map, eloc_symvalues_map, hloc_pos_blocs_map
        for rule in rules:
            add_hloc_pos_blocs(rule)
            add_loc_values(rule)

        # initilize symloc_unifiable_locs_map
        for loc in eloc_symvalues_map:
            for rule in collect(
                p, lambda x: isinstance(x, Rule) and x.body
            ):  # non-facts rules
                arg_at_loc = find_arg_at_loc(loc, rule)
                if arg_at_loc is None:
                    continue
                unifiable_locs = find_unifiable_locs_of_arg(
                    arg_at_loc, rule.body
                ) - set([loc])
                symloc_unifiable_locs_map[loc].update(unifiable_locs)

        return (
            loc_values_map,
            eloc_symvalues_map,
            hloc_pos_blocs_map,
            symloc_unifiable_locs_map,
        )

    def analyse_loc_values(
        loc_values_map: LocValuesDict, hloc_blocs_map: LocLocsDict
    ) -> LocValuesDict:
        """Analyse the values that variable at loc can take during evaluation."""
        is_changed = True

        while is_changed:
            is_changed = False

            for hloc in hloc_blocs_map.keys():
                if not hloc_blocs_map[hloc]:
                    continue
                union_blocs_values = set.union(
                    *[loc_values_map[bloc] for bloc in hloc_blocs_map[hloc]]
                )

                is_changed = (
                    not loc_values_map[hloc].issuperset(union_blocs_values)
                    if not is_changed
                    else True
                )

                loc_values_map[hloc].update(union_blocs_values)

        return loc_values_map

    def create_unifiable_consts_map(loc_values_map: LocValuesDict,
                                       eloc_symvalues_map: LocValuesDict,
                                       symloc_unifiable_locs_map: LocLocsDict) -> Dict[Tuple[Set[Value]], Set[Value]]:

        # sym const -> set of consts that sym const attempt to unify with
        unifiable_consts_map = dict()

        for loc, symvalues in eloc_symvalues_map.items():
            unifiable_consts_map[tuple(symvalues)] = set( # set of in principle to-be-joined constants
                itertools.chain(
                    *[loc_values_map[sloc] for sloc in symloc_unifiable_locs_map[loc]]
                )
            ) | loc_values_map[loc]

        return unifiable_consts_map

    (
        init_loc_values_map,
        eloc_symvalues_map,
        hloc_blocs_map,
        symloc_unifiable_locs_map,
    ) = init_maps(rules)

    loc_values_map = analyse_loc_values(init_loc_values_map, hloc_blocs_map)

    unifiable_consts_map = create_unifiable_consts_map(
        loc_values_map, eloc_symvalues_map, symloc_unifiable_locs_map
    )

    if DEBUG:
        # print the loc values map
        print("\nloc_values_map: \n", "\n".join(
            [f"{k} -> {set(map(lambda x: x.value, v))}" for k, v in
             loc_values_map.items()]))

        print("\n symconsts_unifiable_consts_map: \n" +
              '\n'.join([f"{','.join([i.value for i in k])} -> {[i.value for i in v]}" for k, v in unifiable_consts_map.items()]))

    return unifiable_consts_map


def create_naive_domain_facts(p: Program) -> List[Rule]:
    def create_fact(pred_name, args):
        return Rule(Literal(pred_name, args, True), [])

    def extract_pred_nonsymconsts_pair(fact):
        if not any([utils.is_arg_symbolic(arg) for arg in 
        fact.head.args]):
            return (fact.head.name, fact.head.args)
        return (None, None)

    facts = collect(p, lambda x: isinstance(x, Rule) and not x.body)

    pred_symconsts_list_map = group_pred_consts_list(facts, lambda x:
                                                     extract_pred_symconsts_pair(x))
    pred_consts_list_map = group_pred_consts_list(facts, lambda x:
                                                  extract_pred_nonsymconsts_pair(x))

    naive_facts = []

    # for each predicate name
    for pred_name in pred_symconsts_list_map.keys():
        # get the list of symbolic constants and constants for the current predicate
        sym_consts_list = pred_symconsts_list_map[pred_name]
        consts_list = pred_consts_list_map[pred_name]

        # iterate over all combinations of symbolic constants and constants
        for sym_consts, consts in itertools.product(sym_consts_list, consts_list):
            # create a list of facts and add it to the naive_facts list 
            facts = [create_fact(f"{common.DOMAIN_PREDICATE_PREFIX}{symvalue_for_pred(sym_const)}", [const]) for (const, sym_const) in zip(consts, sym_consts)]
            naive_facts.extend(facts)

    return naive_facts


def create_abstract_domain_facts(p: Program) -> List[Rule]:

    def create_fact(pred_name: str, args: List[String | Number]) -> Rule:
        return Rule(Literal(pred_name, args, True), [])

    # domain facts for to-be-joined constants
    def create_unifiable_facts() -> List[Rule]:
        symconsts_unifiable_consts_map = analyse_symbolic_constants(p)
        unifiable_facts = []

        for symconsts, consts in symconsts_unifiable_consts_map.items():
            for symconst, const in itertools.product(symconsts, consts):
                #FIXME: temporarily disabled non-symbolic const
                # unifiable_facts.append(create_fact(
                #     f"{common.DOMAIN_PREDICATE_PREFIX}{symvalue_for_pred(symconst)}",
                #     [const]))
                #TODO: add the non-symbolic const which appears in original rules
                if utils.is_arg_symbolic(const):
                    unifiable_facts.append(create_fact(
                        f"{common.DOMAIN_PREDICATE_PREFIX}{symvalue_for_pred(symconst)}",
                        [const]))

        return unifiable_facts

    abstract_domain_facts = create_unifiable_facts()

    return abstract_domain_facts


def transform_declarations(p: Program) -> Dict[str, List[str]]:

    def extract_pred_symconstype_pair(fact):
        # get the name of the predicate
        name = fact.head.name

        # get the list of symbolic constants and their types in the predicate arguments
        symconst_types = [(arg, p.declarations[name][idx]) for idx, arg in 
enumerate(fact.head.args) if utils.is_arg_symbolic(arg)]

        return name, symconst_types

    # collect facts
    facts = collect(p, lambda x: isinstance(x, Rule) and not x.body)

    pred_symconstype_map = utils.flatten_dict(
        group_pred_consts_list(facts, lambda x: 
extract_pred_symconstype_pair(x)))

    # create a dictionary that maps symbolic constants to their types
    symconst_type_map = {symconst: type for fact in facts for symconst, type in extract_pred_symconstype_pair(fact)[1]}

    # symbolic_consts must have the same order as that in transform_into_meta_program
    sym_consts = collect(p, lambda x: utils.is_arg_symbolic(x))

    # create a list of the binding variable types
    binding_var_types = [symconst_type_map[x] for x in sym_consts]

    def transform_declaration(n: Rule) -> List[Tuple[Any, Any]]:

        if not n.body:
            # collect symbolic constant types for the current predicate
            symconstypes_of_pred = pred_symconstype_map.get(n.head.name, [])

            # EDB head declaration
            res = [(n.head.name, p.declarations[n.head.name] +
                    [type for _, type in symconstypes_of_pred])]

            # domain declarations
            for symconst, type in symconstypes_of_pred:
                if p.declarations.get(f"{common.DOMAIN_PREDICATE_PREFIX}{symvalue_for_pred(symconst)}", None) is None:
                    res.append(
                        (f"{common.DOMAIN_PREDICATE_PREFIX}{symvalue_for_pred(symconst)}", [type]))

            return res

        else:
            # IDB head declaration
            return [(n.head.name, p.declarations[n.head.name] + binding_var_types)]

    rules = collect(p, lambda x: isinstance(x, Rule))

    transformed_declarations = {k: v for k, v in itertools.chain(
        *map(transform_declaration, rules))}

    return transformed_declarations


def transform_into_meta_program(p: Program) -> Program:
    """Transform a Datalog program into the meta-Datalog program."""

    symbolic_consts = collect(
        p,
        lambda x: utils.is_arg_symbolic(x)
    )

    # collect facts
    facts = collect(p, lambda x: isinstance(x, Rule) and not x.body)

    pred_symconsts_map = utils.flatten_dict(group_pred_consts_list(
        facts, lambda x: extract_pred_symconsts_pair(x)))

    edb_names = p.declarations.keys() - set([r.head.name for r in collect(p, lambda x: isinstance(x, Rule) and x.body)])
    special_pred_names = edb_names | common.SOUFFLE_INTRINSIC_PREDS

    binding_vars = [
        Variable(f"{common.BINDING_VARIABLE_PREFIX}{symvalue_for_pred(x)}") for x in symbolic_consts
    ]

    def add_binding_vars_to_literal(
        l: Literal, binding_vars: List[Variable]
    ) -> Literal:
        return Literal(l.name, l.args + binding_vars, l.positive)

    def binding_vars_of_pred(pred_name: str) -> List[Variable]:
        return [
            Variable(f"{common.BINDING_VARIABLE_PREFIX}{symvalue_for_pred(x)}")
            for x in pred_symconsts_map.get(pred_name, [])
        ]

    def add_domain_literal(sym_arg: Union[String, Number]) -> Literal:
        # E.g., domain_alpha(var_alpha)
        return Literal(
            f"{common.DOMAIN_PREDICATE_PREFIX}{symvalue_for_pred(sym_arg)}",
            [Variable(f"{common.BINDING_VARIABLE_PREFIX}{symvalue_for_pred(sym_arg)}")],
            True,
        )

    def add_binding_vars(n: Any) -> Any:
        if isinstance(n, Rule):
            if not n.body:
                # fact
                replaced = transform(
                    n.head,
                    lambda x: Variable(f"{common.BINDING_VARIABLE_PREFIX}{symvalue_for_pred(x)}")
                    if x in symbolic_consts
                    else x,
                )

                domain_body = [
                    add_domain_literal(x)
                    for x in pred_symconsts_map.get(n.head.name, [])
                ]

                return Rule(
                    add_binding_vars_to_literal(
                        replaced, binding_vars_of_pred(n.head.name)
                    ),
                    domain_body,
                )
            else:
                # rule
                replaced_head = transform(n.head, lambda x:
                                          add_binding_vars_to_literal(
                                              x, binding_vars) if isinstance(x, Literal) else x)

                replaced_body = list(map(lambda l: transform(l, lambda x: add_binding_vars_to_literal(x, binding_vars_of_pred(
                    x.name) if x.name in special_pred_names else binding_vars) if
                    isinstance(x, Literal) else x), n.body))

                domain_body = [add_domain_literal(x) for x in symbolic_consts]

                return Rule(replaced_head, replaced_body + domain_body)

        return n

    return transform(p, add_binding_vars)

def symvalue_for_pred(x):
    if isinstance(x, Number):
        return abs(x.value)
    return x.value

@pytest.fixture
def program_text():
    return """
.decl reach_no_call(from:number, to:number, v:symbol)
.decl call(f:symbol, node:number, v:symbol)
.decl final(n:number)
.decl flow(x:number, y:number)
.decl correct_usage(n:number)
.decl incorrect_usage(n:number)
.decl label(l:number)
.decl variable(v:symbol)
.input final
.input call    
.input flow
.input label     
.input variable
.output correct_usage
correct_usage(L) :-
   call("open", L, _),
   ! incorrect_usage(L),
   label(L).
incorrect_usage(L) :-
  call("open", L, V),
  flow(L, L1),
  final(F),
  reach_no_call(L1, F, V).
  
reach_no_call(X, X, V) :-
  label(X),
  ! call("close", X, V),
  variable(V).
reach_no_call(X, Y, V) :-
  ! call("close", X, V),
  flow(X, Z),
  reach_no_call(Z, Y, V).
call("open", 1, "x").
call("close", 4, "x").
call("symlog_symbolic_open", "symlog_symbolic_2", "symlog_symbolic_x").
final(5).
final("symlog_symbolic_1").
flow(1, 2).
flow(2, 3).
flow(3, 4).
flow(4, 5).
label(1).
label(2).
label(3).
label(4).
label(5).
variable("x").
    """


def test_naive_meta_program_transformation(program_text):
    answer = """
.decl reach_no_call(v0:number, v1:number, v2:symbol, v3:symbol, v4:number, v5:symbol, v6:number)
.decl call(v0:symbol, v1:number, v2:symbol, v3:symbol, v4:number, v5:symbol)
.decl final(v0:number, v1:number)
.decl flow(v0:number, v1:number)
.decl correct_usage(v0:number, v1:symbol, v2:number, v3:symbol, v4:number)
.decl incorrect_usage(v0:number, v1:symbol, v2:number, v3:symbol, v4:number)
.decl label(v0:number)
.decl variable(v0:symbol)
.decl symlog_domain_symlog_symbolic_open(v0:symbol)
.decl symlog_domain_symlog_symbolic_2(v0:number)
.decl symlog_domain_symlog_symbolic_x(v0:symbol)
.decl symlog_domain_symlog_symbolic_1(v0:number)
.input final
.input call
.input flow
.input label
.input variable
.output correct_usage
correct_usage(L, symlog_binding_symlog_symbolic_open, symlog_binding_symlog_symbolic_2, symlog_binding_symlog_symbolic_x, symlog_binding_symlog_symbolic_1) :- call("open", L, _, symlog_binding_symlog_symbolic_open, symlog_binding_symlog_symbolic_2, symlog_binding_symlog_symbolic_x), !incorrect_usage(L, symlog_binding_symlog_symbolic_open, symlog_binding_symlog_symbolic_2, symlog_binding_symlog_symbolic_x, symlog_binding_symlog_symbolic_1), label(L), symlog_domain_symlog_symbolic_open(symlog_binding_symlog_symbolic_open), symlog_domain_symlog_symbolic_2(symlog_binding_symlog_symbolic_2), symlog_domain_symlog_symbolic_x(symlog_binding_symlog_symbolic_x), symlog_domain_symlog_symbolic_1(symlog_binding_symlog_symbolic_1).
incorrect_usage(L, symlog_binding_symlog_symbolic_open, symlog_binding_symlog_symbolic_2, symlog_binding_symlog_symbolic_x, symlog_binding_symlog_symbolic_1) :- call("open", L, V, symlog_binding_symlog_symbolic_open, symlog_binding_symlog_symbolic_2, symlog_binding_symlog_symbolic_x), flow(L, L1), final(F, symlog_binding_symlog_symbolic_1), reach_no_call(L1, F, V, symlog_binding_symlog_symbolic_open, symlog_binding_symlog_symbolic_2, symlog_binding_symlog_symbolic_x, symlog_binding_symlog_symbolic_1), symlog_domain_symlog_symbolic_open(symlog_binding_symlog_symbolic_open), symlog_domain_symlog_symbolic_2(symlog_binding_symlog_symbolic_2), symlog_domain_symlog_symbolic_x(symlog_binding_symlog_symbolic_x), symlog_domain_symlog_symbolic_1(symlog_binding_symlog_symbolic_1).
reach_no_call(X, X, V, symlog_binding_symlog_symbolic_open, symlog_binding_symlog_symbolic_2, symlog_binding_symlog_symbolic_x, symlog_binding_symlog_symbolic_1) :- label(X), !call("close", X, V, symlog_binding_symlog_symbolic_open, symlog_binding_symlog_symbolic_2, symlog_binding_symlog_symbolic_x), variable(V), symlog_domain_symlog_symbolic_open(symlog_binding_symlog_symbolic_open), symlog_domain_symlog_symbolic_2(symlog_binding_symlog_symbolic_2), symlog_domain_symlog_symbolic_x(symlog_binding_symlog_symbolic_x), symlog_domain_symlog_symbolic_1(symlog_binding_symlog_symbolic_1).
reach_no_call(X, Y, V, symlog_binding_symlog_symbolic_open, symlog_binding_symlog_symbolic_2, symlog_binding_symlog_symbolic_x, symlog_binding_symlog_symbolic_1) :- !call("close", X, V, symlog_binding_symlog_symbolic_open, symlog_binding_symlog_symbolic_2, symlog_binding_symlog_symbolic_x), flow(X, Z), reach_no_call(Z, Y, V, symlog_binding_symlog_symbolic_open, symlog_binding_symlog_symbolic_2, symlog_binding_symlog_symbolic_x, symlog_binding_symlog_symbolic_1), symlog_domain_symlog_symbolic_open(symlog_binding_symlog_symbolic_open), symlog_domain_symlog_symbolic_2(symlog_binding_symlog_symbolic_2), symlog_domain_symlog_symbolic_x(symlog_binding_symlog_symbolic_x), symlog_domain_symlog_symbolic_1(symlog_binding_symlog_symbolic_1).
call("open", 1, "x", symlog_binding_symlog_symbolic_open, symlog_binding_symlog_symbolic_2, symlog_binding_symlog_symbolic_x) :- symlog_domain_symlog_symbolic_open(symlog_binding_symlog_symbolic_open), symlog_domain_symlog_symbolic_2(symlog_binding_symlog_symbolic_2), symlog_domain_symlog_symbolic_x(symlog_binding_symlog_symbolic_x).
call("close", 4, "x", symlog_binding_symlog_symbolic_open, symlog_binding_symlog_symbolic_2, symlog_binding_symlog_symbolic_x) :- symlog_domain_symlog_symbolic_open(symlog_binding_symlog_symbolic_open), symlog_domain_symlog_symbolic_2(symlog_binding_symlog_symbolic_2), symlog_domain_symlog_symbolic_x(symlog_binding_symlog_symbolic_x).
call(symlog_binding_symlog_symbolic_open, symlog_binding_symlog_symbolic_2, symlog_binding_symlog_symbolic_x, symlog_binding_symlog_symbolic_open, symlog_binding_symlog_symbolic_2, symlog_binding_symlog_symbolic_x) :- symlog_domain_symlog_symbolic_open(symlog_binding_symlog_symbolic_open), symlog_domain_symlog_symbolic_2(symlog_binding_symlog_symbolic_2), symlog_domain_symlog_symbolic_x(symlog_binding_symlog_symbolic_x).
final(5, symlog_binding_symlog_symbolic_1) :- symlog_domain_symlog_symbolic_1(symlog_binding_symlog_symbolic_1).
final(symlog_binding_symlog_symbolic_1, symlog_binding_symlog_symbolic_1) :- symlog_domain_symlog_symbolic_1(symlog_binding_symlog_symbolic_1).
flow(1, 2).
flow(2, 3).
flow(3, 4).
flow(4, 5).
label(1).
label(2).
label(3).
label(4).
label(5).
variable("x").
symlog_domain_symlog_symbolic_open("open").
symlog_domain_symlog_symbolic_2(1).
symlog_domain_symlog_symbolic_x("x").
symlog_domain_symlog_symbolic_open("close").
symlog_domain_symlog_symbolic_2(4).
symlog_domain_symlog_symbolic_x("x").
symlog_domain_symlog_symbolic_1(5).
"""

    program = parse(program_text)

    transformed = transform_into_meta_program(program)

    declarations = transform_declarations(program)

    facts = create_naive_domain_facts(program)

    transformed.rules.extend(facts)

    transformed.declarations.update(declarations)

    assert pprint(transformed).strip() == answer.strip()


def test_symconst_unifiable_consts_mapping(program_text):
    program = parse(program_text)
    symconst_unifiable_consts_map = analyse_symbolic_constants(program)

    new_dict = utils.convert_dict_values_to_sets(symconst_unifiable_consts_map)

    answer = {
        'symlog_symbolic_open': set([]),
        'symlog_symbolic_2': set([1, 2, 3, 4, 5]),
        'symlog_symbolic_x': set(['x']),
        'symlog_symbolic_1': set([1, 2, 3, 4, 5]),
    }

    assert new_dict == answer


def transform_input_facts(input_facts, declarations):
    # transform input_fact into a list of fact rules

    def to_parsed_arg(x):
        if utils.is_number(x):
            return Number(x)
        else:
            return String(x)

    fact_rules = [Rule(Literal(name, [to_parsed_arg(x) for x in row], True), [])
                  for name, arguments in input_facts.items()
                  if name in declarations
                  for row in arguments]

    return fact_rules


def create_sym_facts(idb_list, declarations):
    '''Create symbolic facts for the given idb list for original program'''
    sym_cnt = 0
    sym_facts = defaultdict(list)

    def to_sym_arg(t, idx):
        if t == common.SOUFFLE_SYMBOL:
            return f"{common.SYMBOLIC_CONSTANT_PREFIX}{idx}"
        elif t == common.SOUFFLE_NUMBER:
            return common.SYMLOG_NUM_POOL[idx] #TODO: use seperated idx for numbers
        else:
            raise ValueError('Unsupported type: {}'.format(type(t)))

    def add_sym_fact(sym_cnt, name):
        args = [to_sym_arg(t, sym_cnt + idx) for idx, t in enumerate(declarations[name])]
        sym_facts[name].append(args)
        return sym_cnt + len(declarations[name])

    for idb in idb_list:
        sym_cnt = add_sym_fact(sym_cnt, idb)

    return sym_facts


def transform_and_store_program(program, input_facts, output_file):

    fact_rules = transform_input_facts(input_facts, program.declarations)
    program.rules.extend(fact_rules)

    transformed = transform_into_meta_program(program)
    declarations = transform_declarations(program)
    transformed.declarations.update(declarations)

    # facts = create_naive_domain_facts(program)
    abstract_facts = create_abstract_domain_facts(program)
    # transformed.rules.extend(facts + abstract_facts)
    transformed.rules.extend(abstract_facts)

    dir_name = os.path.dirname(output_file)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    with open(output_file, 'w') as f:
        f.write(pprint(transformed))

    print('Program written to {}'.format(output_file))


if __name__ == '__main__':

    args = parser.parse_args()

    program_text = utils.read_file(args.program_path)
    DATA_DIR = args.data_path
    TEST_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tests')

    program = parse(program_text)
    input_facts = load_relations(DATA_DIR) # merge two dictionaries

    transformations = [    
        ('original', []),
        # ('small_transformed', ['OperatorAt', 'If_Var', 'If_Constant', 'Instruction_Next']),
        ('large_transformed', ['OperatorAt', 'If_Var', 'If_Constant', 'JumpTarget', 'Instruction_Method', 'Dominates', 'Instruction_Index', 'BasicBlockHead'])
    ]

    for transformation in transformations:
        name, idb_list = transformation
        program_file = os.path.join(TEST_DIR, f'{name}_program.dl')
        sym_facts = create_sym_facts(idb_list, program.declarations)
        facts = {k: sym_facts.get(k, []) + input_facts.get(k, []) for k in (input_facts.keys() | sym_facts.keys())}
        transform_and_store_program(copy.deepcopy(program), facts, program_file)
