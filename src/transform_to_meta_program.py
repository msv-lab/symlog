import common
from souffle import (
    collect,
    transform,
    parse,
    pprint,
    Variable,
    Literal,
    Rule,
    String,
    Number,
    Program,
)
import utils

from typing import Any, List, Dict, Set, Tuple, Optional, DefaultDict, Union
import itertools
from collections import defaultdict
from sympy.utilities.iterables import multiset_partitions
import pytest
import os

DEBUG = False


def extract_pred_symconsts_pair(fact):
    return fact.head.name, [arg for arg in fact.head.args if isinstance(arg, String) and arg.value.startswith(common.SYMBOLIC_CONSTANT_PREFIX)]


def group_pred_consts_list(facts, f):
    d = defaultdict(list)
    for k, v in list(map(f, facts)):
        if v:
            d[k].append(v)
    return d


def analyse_symbolic_constants(
    p: Program,
) -> Dict[Tuple[Set[String | Number]], Set[String | Number]]:
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
            if isinstance(arg, Variable) and arg in lit.args and lit.positive:
                return True
            return False

        def find_arg_at_loc(
            loc: Loc, rule: Rule
        ) -> Optional[String | Number | Variable]:
            pred_name, idx = loc
            for l in rule.body:
                if l.name == pred_name:
                    return l.args[idx]
            return None

        def find_unifiable_locs_of_arg(
            arg: Variable | String | Number, lits: List[Literal]
        ) -> Set[Loc]:
            locs = set()
            for lit in lits:
                if var_in_pos_lit(arg, lit):  # only positive literals
                    locs.add((lit.name, lit.args.index(arg)))
            return locs

        def add_hloc_pos_blocs(rule: Rule) -> None:
            if not rule.body:
                return
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
            if not rule.body:
                for i, arg in enumerate(rule.head.args):
                    # store loc, and corresp value in fact
                    loc_values_map[(rule.head.name, i)].add(arg)

                    # when value is symbolic, add loc, value to
                    # loc_symvalues_map
                    if isinstance(arg, String) and arg.value.startswith(
                        common.SYMBOLIC_CONSTANT_PREFIX
                    ):
                        eloc_symvalues_map[(rule.head.name, i)].add(arg)
            else:
                for lit in [rule.head] + list(rule.body):
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

    def create_unifiable_consts_map(
        loc_values_map: LocValuesDict,
        eloc_symvalues_map: LocValuesDict,
        symloc_unifiable_locs_map: LocLocsDict,
    ) -> Dict[Tuple[Set[Value]], Set[Value]]:

        # sym const -> set of consts that sym const attempt to unify with
        unifiable_consts_map = dict()

        for loc, symvalues in eloc_symvalues_map.items():
            unifiable_consts_map[tuple(symvalues)] = set(
                itertools.chain(
                    *[loc_values_map[jloc] for jloc in symloc_unifiable_locs_map[loc]]
                )
            )  # set of in principle to-be-joined constants

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
        print(
            "\nloc_values_map: \n",
            "\n".join(
                [
                    f"{k} -> {set(map(lambda x: x.value, v))}"
                    for k, v in init_loc_values_map.items()
                ]
            ),
        )

        print(
            "\n symconsts_unifiable_consts_map: \n"
            + "\n".join(
                [
                    f"{','.join([i.value for i in k])} -> {[i.value for i in v]}"
                    for k, v in unifiable_consts_map.items()
                ]
            )
        )

    return unifiable_consts_map


def create_naive_domain_facts(p: Program) -> List[Rule]:

    def create_fact(pred_name, args):
        return Rule(Literal(pred_name, args, True), [])

    def extract_pred_nonsymconsts_pair(fact):
        if not any([isinstance(arg, String) and 
        arg.value.startswith(common.SYMBOLIC_CONSTANT_PREFIX) for arg in 
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
            facts = [create_fact(f"{common.DOMAIN_PREDICATE_PREFIX}{sym_const.value}", [const]) for (const, sym_const) in zip(consts, sym_consts)]
            naive_facts.extend(facts)

    return naive_facts


def create_abstract_domain_facts(p: Program) -> List[Rule]:

    sym_consts = collect(
        p,
        lambda x: isinstance(x, String)
        and x.value.startswith(common.SYMBOLIC_CONSTANT_PREFIX),
    )

    def create_fact(pred_name: str, args: List[String | Number]) -> Rule:
        return Rule(Literal(pred_name, args, True), [])

    def create_sym_cstr(
        sym_const: String, equiv_partition: List[List[String]]
    ) -> List[str]:
        eq_relations = []
        neq_relations = []

        for equiv_class in equiv_partition:
            if sym_const in equiv_class:
                eq_relations.append(sorted(equiv_class, key=lambda x: x.value))

            else:
                neq_relations.append(sorted(equiv_class, key=lambda x: x.value))

        def sort_and_to_string(
            eq_relations: List[List[String]], neq_relations: List[List[String]]
        ) -> List[str]:
            eq_relations.sort()
            neq_relations.sort()

            str_relations = (
                [
                    utils.list_to_str([eqc.value for eqc in eq_rel])
                    for eq_rel in eq_relations
                ]
                + [common.EQ_NONEQ]
                + [
                    utils.list_to_str([neqc.value for neqc in neq_rel])
                    for neq_rel in neq_relations
                ]
            )

            return str_relations

        return sort_and_to_string(eq_relations, neq_relations)

    def create_symcstr_facts() -> List[Rule] | List[Any]:
        """Construct the facts of symbolic constraints."""

        symcstr_facts = []

        # divide the sym consts into equivalence classes:
        # https://math.stackexchange.com/questions/703475/determine-the-number-of-equivalence-relations-on-the-set-1-2-3-4

        if not len(sym_consts):  # no symbolic constants
            return symcstr_facts
        elif len(sym_consts) == 1:
            equiv_partitions = multiset_partitions(sym_consts, 1)
        else:
            equiv_partitions = list(multiset_partitions(sym_consts, 1)) + list(
                multiset_partitions(sym_consts, 2)
            )

        for (sym_const, equiv_partition) in itertools.product(
            sym_consts, equiv_partitions
        ):

            symconst_cstr = common.DELIMITER.join(
                create_sym_cstr(sym_const, equiv_partition)
            )

            symcstr_facts.append(
                create_fact(
                    f"{common.DOMAIN_PREDICATE_PREFIX}{sym_const.value}",
                    [String(symconst_cstr)],
                )
            )

        return symcstr_facts

    # domain facts for to-be-joined constants
    def create_unifiable_facts() -> List[Rule]:
        symconsts_unifiable_consts_map = analyse_symbolic_constants(p)
        unifiable_facts = []

        for symconsts, consts in symconsts_unifiable_consts_map.items():
            for symconst, const in itertools.product(symconsts, consts):
                unifiable_facts.append(
                    create_fact(
                        f"{common.DOMAIN_PREDICATE_PREFIX}{symconst.value}", [const]
                    )
                )

        return unifiable_facts

    sym_cstr_facts = create_symcstr_facts()
    unifiable_symconst_facts = create_unifiable_facts()

    abstract_domain_facts = sym_cstr_facts + unifiable_symconst_facts

    if DEBUG:
        print(
            "\nsym_cstr_facts in program: \n",
            "\n".join([str(fact) for fact in sym_cstr_facts]),
        )

        print("\nsym_cstr_facts in human readable format: ")
        for fact in sym_cstr_facts:
            sym_const = fact.head.name.split(common.DOMAIN_PREDICATE_PREFIX)[1]
            str_cstr = fact.head.args[0].value

            str_eq_cstr, str_neq_cstr = str_cstr.split(common.EQ_NONEQ)

            str_eq_cstr = str_eq_cstr[
                str_eq_cstr.find(common.LEFT_SQUARE_BRACKET)
                + 1 : str_eq_cstr.find(common.RIGHT_SQUARE_BRACKET)
            ].strip()

            str_neq_cstr = str_neq_cstr[
                str_neq_cstr.find(common.LEFT_SQUARE_BRACKET)
                + 1 : str_neq_cstr.find(common.RIGHT_SQUARE_BRACKET)
            ].strip()

            human_readable_eqcstr = [
                sym_const + common.EQUAL + cstr
                for cstr in str_eq_cstr.split(common.DELIMITER)
                if cstr != sym_const and cstr != ""
            ]

            human_readable_neqcstr = [
                sym_const + common.NOT_EQUAL + cstr
                for cstr in str_neq_cstr.split(common.DELIMITER)
                if cstr != sym_const and cstr != ""
            ]

            print(
                f"{fact.head.name}({sym_const}, {common.DELIMITER.join(human_readable_eqcstr + human_readable_neqcstr)})"
            )

    return abstract_domain_facts


def transform_into_meta_program(p: Program) -> Program:
    """Transform a Datalog program into the meta-Datalog program.
    """

    symbolic_consts = collect(
        p,
        lambda x: (isinstance(x, String) or isinstance(x, Number))
        and str(x.value).startswith(common.SYMBOLIC_CONSTANT_PREFIX),
    )

    # collect facts
    facts = collect(p, lambda x: isinstance(x, Rule) and not x.body)

    pred_sym_consts_map = utils.flatten_dict(group_pred_consts_list(
        facts, lambda x: extract_pred_symconsts_pair(x)))

    edb_names = set(p.declarations.keys()) - set([x.head.name for x in collect(p, lambda x: isinstance(x, Rule) and x.body)])
    special_pred_names = edb_names | {"contains", "substr","cat"}
    # TODO: also exclude internal predicates, e.g., contains.

    binding_vars = [
        Variable(f"{common.BINDING_VARIABLE_PREFIX}{x.value}") for x in
        symbolic_consts]

    def add_binding_vars_to_literal(
        l: Literal, binding_vars: List[Variable]
    ) -> Literal:
        return Literal(l.name, l.args + binding_vars, l.positive)

    def binding_vars_of_pred(pred_name: str) -> List[Variable]:
        return [
            Variable(f"{common.BINDING_VARIABLE_PREFIX}{x.value}")
            for x in pred_symconsts_map.get(pred_name, [])
        ]

    def add_domain_literal(sym_arg: Union[String, Number]) -> Literal:
        # E.g., domain_alpha(var_alpha)
        return Literal(f"{common.DOMAIN_PREDICATE_PREFIX}{sym_arg.value}",
                       [Variable(f"{common.BINDING_VARIABLE_PREFIX}{sym_arg.value}")], True)

    def add_binding_vars(n):
        if isinstance(n, Rule):
            if not n.body:
                # fact
                replaced = transform(
                    n.head, lambda x: Variable(f"{common.BINDING_VARIABLE_PREFIX}{x.value}") if x in symbolic_consts
                    else x)

                domain_body = [add_domain_literal(
                    x) for x in pred_sym_consts_map.get(n.head.name, [])]

                return Rule(add_binding_vars_to_literal(replaced, binding_vars_of_pred(n.head.name)), domain_body)
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
call("_symlog_symbolic_open", "_symlog_symbolic_2", "_symlog_symbolic_x").
final(5).
final("_symlog_symbolic_1").
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
.decl _symlog_domain__symlog_symbolic_open(v0:symbol)
.decl _symlog_domain__symlog_symbolic_2(v0:number)
.decl _symlog_domain__symlog_symbolic_x(v0:symbol)
.decl _symlog_domain__symlog_symbolic_1(v0:number)
.input final
.input call
.input flow
.input label
.input variable
.output correct_usage
correct_usage(L, _symlog_binding__symlog_symbolic_open, _symlog_binding__symlog_symbolic_2, _symlog_binding__symlog_symbolic_x, _symlog_binding__symlog_symbolic_1) :- call("open", L, _, _symlog_binding__symlog_symbolic_open, _symlog_binding__symlog_symbolic_2, _symlog_binding__symlog_symbolic_x), !incorrect_usage(L, _symlog_binding__symlog_symbolic_open, _symlog_binding__symlog_symbolic_2, _symlog_binding__symlog_symbolic_x, _symlog_binding__symlog_symbolic_1), label(L), _symlog_domain__symlog_symbolic_open(_symlog_binding__symlog_symbolic_open), _symlog_domain__symlog_symbolic_2(_symlog_binding__symlog_symbolic_2), _symlog_domain__symlog_symbolic_x(_symlog_binding__symlog_symbolic_x), _symlog_domain__symlog_symbolic_1(_symlog_binding__symlog_symbolic_1).
incorrect_usage(L, _symlog_binding__symlog_symbolic_open, _symlog_binding__symlog_symbolic_2, _symlog_binding__symlog_symbolic_x, _symlog_binding__symlog_symbolic_1) :- call("open", L, V, _symlog_binding__symlog_symbolic_open, _symlog_binding__symlog_symbolic_2, _symlog_binding__symlog_symbolic_x), flow(L, L1), final(F, _symlog_binding__symlog_symbolic_1), reach_no_call(L1, F, V, _symlog_binding__symlog_symbolic_open, _symlog_binding__symlog_symbolic_2, _symlog_binding__symlog_symbolic_x, _symlog_binding__symlog_symbolic_1), _symlog_domain__symlog_symbolic_open(_symlog_binding__symlog_symbolic_open), _symlog_domain__symlog_symbolic_2(_symlog_binding__symlog_symbolic_2), _symlog_domain__symlog_symbolic_x(_symlog_binding__symlog_symbolic_x), _symlog_domain__symlog_symbolic_1(_symlog_binding__symlog_symbolic_1).
reach_no_call(X, X, V, _symlog_binding__symlog_symbolic_open, _symlog_binding__symlog_symbolic_2, _symlog_binding__symlog_symbolic_x, _symlog_binding__symlog_symbolic_1) :- label(X), !call("close", X, V, _symlog_binding__symlog_symbolic_open, _symlog_binding__symlog_symbolic_2, _symlog_binding__symlog_symbolic_x), variable(V), _symlog_domain__symlog_symbolic_open(_symlog_binding__symlog_symbolic_open), _symlog_domain__symlog_symbolic_2(_symlog_binding__symlog_symbolic_2), _symlog_domain__symlog_symbolic_x(_symlog_binding__symlog_symbolic_x), _symlog_domain__symlog_symbolic_1(_symlog_binding__symlog_symbolic_1).
reach_no_call(X, Y, V, _symlog_binding__symlog_symbolic_open, _symlog_binding__symlog_symbolic_2, _symlog_binding__symlog_symbolic_x, _symlog_binding__symlog_symbolic_1) :- !call("close", X, V, _symlog_binding__symlog_symbolic_open, _symlog_binding__symlog_symbolic_2, _symlog_binding__symlog_symbolic_x), flow(X, Z), reach_no_call(Z, Y, V, _symlog_binding__symlog_symbolic_open, _symlog_binding__symlog_symbolic_2, _symlog_binding__symlog_symbolic_x, _symlog_binding__symlog_symbolic_1), _symlog_domain__symlog_symbolic_open(_symlog_binding__symlog_symbolic_open), _symlog_domain__symlog_symbolic_2(_symlog_binding__symlog_symbolic_2), _symlog_domain__symlog_symbolic_x(_symlog_binding__symlog_symbolic_x), _symlog_domain__symlog_symbolic_1(_symlog_binding__symlog_symbolic_1).
call("open", 1, "x", _symlog_binding__symlog_symbolic_open, _symlog_binding__symlog_symbolic_2, _symlog_binding__symlog_symbolic_x) :- _symlog_domain__symlog_symbolic_open(_symlog_binding__symlog_symbolic_open), _symlog_domain__symlog_symbolic_2(_symlog_binding__symlog_symbolic_2), _symlog_domain__symlog_symbolic_x(_symlog_binding__symlog_symbolic_x).
call("close", 4, "x", _symlog_binding__symlog_symbolic_open, _symlog_binding__symlog_symbolic_2, _symlog_binding__symlog_symbolic_x) :- _symlog_domain__symlog_symbolic_open(_symlog_binding__symlog_symbolic_open), _symlog_domain__symlog_symbolic_2(_symlog_binding__symlog_symbolic_2), _symlog_domain__symlog_symbolic_x(_symlog_binding__symlog_symbolic_x).
call(_symlog_binding__symlog_symbolic_open, _symlog_binding__symlog_symbolic_2, _symlog_binding__symlog_symbolic_x, _symlog_binding__symlog_symbolic_open, _symlog_binding__symlog_symbolic_2, _symlog_binding__symlog_symbolic_x) :- _symlog_domain__symlog_symbolic_open(_symlog_binding__symlog_symbolic_open), _symlog_domain__symlog_symbolic_2(_symlog_binding__symlog_symbolic_2), _symlog_domain__symlog_symbolic_x(_symlog_binding__symlog_symbolic_x).
final(5, _symlog_binding__symlog_symbolic_1) :- _symlog_domain__symlog_symbolic_1(_symlog_binding__symlog_symbolic_1).
final(_symlog_binding__symlog_symbolic_1, _symlog_binding__symlog_symbolic_1) :- _symlog_domain__symlog_symbolic_1(_symlog_binding__symlog_symbolic_1).
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
_symlog_domain__symlog_symbolic_open("open").
_symlog_domain__symlog_symbolic_2(1).
_symlog_domain__symlog_symbolic_x("x").
_symlog_domain__symlog_symbolic_open("close").
_symlog_domain__symlog_symbolic_2(4).
_symlog_domain__symlog_symbolic_x("x").
_symlog_domain__symlog_symbolic_1(5).
"""

    program = parse(program_text)

    transformed = transform_into_meta_program(program)

    declarations = transform_declarations(program)

    facts = create_naive_domain_facts(program)

    transformed.rules.extend(facts)

    transformed.declarations.update(declarations)

    assert pprint(transformed).strip() == answer.strip()


def convert_dict_values_to_sets(my_dict):
    # Convert each value in the dictionary to a set and join the keys with a comma
    return {','.join([i.value for i in k]): set([i.value for i in v]) for k, v in my_dict.items()}


def test_symconst_unifiable_consts_mapping(program_text):
    program = parse(program_text)
    symconst_unifiable_consts_map = analyse_symbolic_constants(program)

    new_dict = convert_dict_values_to_sets(symconst_unifiable_consts_map)

    answer = {
        '_symlog_symbolic_open': set([]),
        '_symlog_symbolic_2': set([2, 5, 4, 1, 3]),
        '_symlog_symbolic_x': set(['x']),
        '_symlog_symbolic_1': set([2, 5, 4, 1, 3]),
    }

    assert new_dict == answer

if __name__ == '__main__':
    program_text = """

.decl Primitive(type: symbol)
Primitive("boolean").
Primitive("short").
Primitive("int").
Primitive("long").
Primitive("float").
Primitive("double").
Primitive("char").
Primitive("byte").

.decl InstructionLine(m: symbol, i: number, l: number, f: symbol)

.decl VarPointsTo(hctx: symbol, a: symbol, ctx: symbol, v: symbol)

.decl CallGraphEdge(ctx: symbol, ins: symbol, hctx: symbol, sig: symbol)

.decl Reachable(m: symbol)

.decl SpecialMethodInvocation(instruction:symbol, i: number, sig: symbol, base:symbol, m: symbol)

.decl LoadArrayIndex(ins: symbol, i: number, to: symbol, base: symbol, m: symbol)

.decl StoreArrayIndex(ins: symbol, i: number, from: symbol, base: symbol, m: symbol)

.decl StoreInstanceField(ins: symbol, i: number, from: symbol, base: symbol, sig: symbol, m: symbol)

.decl LoadInstanceField(ins: symbol, i: number, to: symbol, base: symbol, sig: symbol, m: symbol)

.decl VirtualMethodInvocation(ins: symbol, i: number, sig: symbol,  base: symbol, m: symbol)

.decl ThrowNull(ins: symbol, i: number, m: symbol)

.decl LoadStaticField(ins: symbol, i: number, to: symbol, sig: symbol, m: symbol)

.decl StoreStaticField(ins: symbol, i: number, from: symbol, sig: symbol, m: symbol)

.decl AssignCastNull(ins: symbol, i: number, to: symbol, t: symbol, m: symbol)

.decl AssignUnop(ins: symbol, i: number, to: symbol, m: symbol)

.decl AssignBinop(ins: symbol, i: number, to: symbol, m: symbol)

.decl AssignOperFrom(ins: symbol, from: symbol)

.decl Var_Type(var: symbol, type: symbol)

.decl EnterMonitor(ins: symbol, i: number, to: symbol, m: symbol)

.decl ExitMonitor(ins: symbol, i: number, to: symbol, m: symbol)

.decl VarPointsToNull(v: symbol)
.decl NullAt(m: symbol, i: number, type: symbol)
.decl ReachableNullAt(m: symbol, i: number, type: symbol)
.decl ReachableNullAtLine(m: symbol, i: number, f: symbol, l: number, type: symbol)
.output ReachableNullAtLine

VarPointsToNull(var) :- VarPointsTo(_, alloc, _, var),
						alloc = "<<null pseudo heap>>".

VarPointsToNull(var) :- AssignCastNull(_,_,var,_,_).

NullAt(meth, index, "Load Array number") :-
VarPointsToNull(var),
LoadArrayIndex(_, index, _, var, meth).

ReachableNullAt(meth, index, type) :- NullAt(meth, index, type), Reachable(meth).

ReachableNullAtLine(meth, index, file, line, type) :- 
ReachableNullAt(meth, index, type), 
InstructionLine(meth, index, line, file).
"""	

    program = parse(program_text)

    # convert input relations dictionary to a list of Rules
    inp_facts = load_relations('/home/liuyu/info3600-bugchecker-benchmarks/digger/logic/doop_logic/facts')
    inp_database = load_relations('/home/liuyu/info3600-bugchecker-benchmarks/digger/logic/doop_logic/database')
    relations = {**inp_facts, **inp_database}

    facts = []
    sym_cnt = 0
    for name, relation in relations.items():
        if name not in program.declarations:
            continue

        for row in relation:
            args = [String(x) if program.declarations[name][idx]=='symbol' else Number(x) for idx, x in enumerate(row)]

            facts.append(Rule(Literal(name, args, True), []))

    # add symbolic fact for VarPointsTo
    name = 'VarPointsTo'
    row = relations[name][0]
    sym_args = [String(common.SYMBOLIC_CONSTANT_PREFIX + str(sym_cnt + idx)) for idx, _ in enumerate(row)]
    sym_cnt += len(row)
    facts.append(Rule(Literal(name, sym_args, True), []))

    program.rules.extend(facts)
    declarations = transform_declarations(program)
    program.declarations.update(declarations)   
    transformed = transform_into_meta_program(program)
 
    facts = create_naive_domain_facts(program)
    transformed.rules.extend(facts)

    with open(os.path.join(os.getcwd(), 'tests/transformed.dl'), 'w') as f:
        f.write(pprint(transformed))
