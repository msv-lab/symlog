import common
from souffle import collect, transform, parse, pprint, Variable, Literal, Rule, String, Number, Program, load_relations
import utils

from typing import Any, List, Dict, Set, Tuple, Optional, DefaultDict, Union
import itertools
from collections import defaultdict
from sympy.utilities.iterables import multiset_partitions
import pytest

DEBUG = False


def extract_pred_symconsts_pair(fact: Rule) -> Tuple[str, List[String]]:
    # get the name of the predicate
    pred_name = fact.head.name

    # get the list of symbolic constants in the predicate arguments
    symbolic_consts = [arg for arg in fact.head.args if isinstance(arg, String) and arg.value.startswith(common.SYMBOLIC_CONSTANT_PREFIX)]

    return pred_name, symbolic_consts


def group_pred_consts_list(facts, f):
    d = defaultdict(list)
    for k, v in list(map(f, facts)):
        if v:
            d[k].append(v)
    return d


def analyse_symbolic_constants(p: Program) -> Dict[Tuple[Set[Union[String, Number]]], Set[Union[String, Number]]]:
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

        def find_arg_at_loc(loc: Loc, rule: Rule) -> Optional[Union[String, Number, Variable]]:
            pred_name, idx = loc
            for l in rule.body:
                if isinstance(l, Literal) and l.name == pred_name:
                    return l.args[idx]
            return None

        def find_unifiable_locs_of_arg(arg: Union[Variable, String, Number], lits: List[Literal]) -> Set[Loc]:
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
                    # eloc_symvalues_map
                    if isinstance(arg, String) and arg.value.startswith(common.SYMBOLIC_CONSTANT_PREFIX):
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

        # FIXME: uncomment above and remove below
        # for loc, symvalues in eloc_symvalues_map.items():
        #     unifiable_consts_map[tuple(symvalues)] = set(
        #         itertools.chain(
        #             *[loc_values_map[sloc] for sloc in symloc_unifiable_locs_map[loc]]
        #         )
        #     ) # set of in principle to-be-joined constants


        return unifiable_consts_map

    (
        init_loc_values_map,
        eloc_symvalues_map,
        hloc_blocs_map,
        symloc_unifiable_locs_map,
    ) = init_maps(rules)

    loc_values_map = analyse_loc_values(init_loc_values_map, hloc_blocs_map)

    unifiable_consts_map = create_unifiable_consts_map(
        loc_values_map, eloc_symvalues_map, symloc_unifiable_locs_map)

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

    def create_sym_cstr(sym_const: String, equiv_partition: List[List[String]]) -> List[str]:
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
                create_sym_cstr(sym_const, equiv_partition))

            symcstr_facts.append(create_fact(
                f"{common.DOMAIN_PREDICATE_PREFIX}{sym_const.value}", [String
                                                                       (symconst_cstr)]))

        return symcstr_facts

    # domain facts for to-be-joined constants
    def create_unifiable_facts() -> List[Rule]:
        symconsts_unifiable_consts_map = analyse_symbolic_constants(p)
        unifiable_facts = []

        for symconsts, consts in symconsts_unifiable_consts_map.items():
            for symconst, const in itertools.product(symconsts, consts):
                unifiable_facts.append(create_fact(
                    f"{common.DOMAIN_PREDICATE_PREFIX}{symconst.value}", [const]))

        return unifiable_facts

    sym_cstr_facts = create_symcstr_facts()
    unifiable_symconst_facts = create_unifiable_facts()

    # abstract_domain_facts = sym_cstr_facts + unifiable_symconst_facts
    # FIXME: uncomment above line and remove the following line
    abstract_domain_facts = unifiable_symconst_facts

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


def transform_declarations(p: Program) -> Dict[str, List[str]]:

    def extract_pred_symconstype_pair(fact):
        # get the name of the predicate
        name = fact.head.name

        # get the list of symbolic constants and their types in the predicate arguments
        symconst_types = [(arg, p.declarations[name][idx]) for idx, arg in 
enumerate(fact.head.args) if isinstance(arg, String) and 
arg.value.startswith(common.SYMBOLIC_CONSTANT_PREFIX)]

        return name, symconst_types

    # collect facts
    facts = collect(p, lambda x: isinstance(x, Rule) and not x.body)

    pred_symconstype_map = utils.flatten_dict(
        group_pred_consts_list(facts, lambda x: 
extract_pred_symconstype_pair(x)))

    # create a dictionary that maps symbolic constants to their types
    symconst_type_map = {symconst: type for fact in facts for symconst, type in extract_pred_symconstype_pair(fact)[1]}

    # symbolic_consts must have the same order as that in transform_into_meta_program
    sym_consts = collect(p, lambda x: isinstance(x, String) and 
        x.value.startswith(common.SYMBOLIC_CONSTANT_PREFIX))

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
                if p.declarations.get(f"{common.DOMAIN_PREDICATE_PREFIX}{symconst.value}", None) is None:
                    res.append(
                        (f"{common.DOMAIN_PREDICATE_PREFIX}{symconst.value}", [type]))

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
        lambda x: (isinstance(x, String) or isinstance(x, Number))
        and str(x.value).startswith(common.SYMBOLIC_CONSTANT_PREFIX),
    )

    # collect facts
    facts = collect(p, lambda x: isinstance(x, Rule) and not x.body)

    pred_symconsts_map = utils.flatten_dict(group_pred_consts_list(
        facts, lambda x: extract_pred_symconsts_pair(x)))

    edb_names = p.declarations.keys() - set([r.head.name for r in collect(p, lambda x: isinstance(x, Rule) and x.body)])
    special_pred_names = edb_names | {'contains', 'substr'}

    binding_vars = [
        Variable(f"{common.BINDING_VARIABLE_PREFIX}{x.value}") for x in symbolic_consts
    ]

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
        return Literal(
            f"{common.DOMAIN_PREDICATE_PREFIX}{sym_arg.value}",
            [Variable(f"{common.BINDING_VARIABLE_PREFIX}{sym_arg.value}")],
            True,
        )

    def add_binding_vars(n):
        if isinstance(n, Rule):
            if not n.body:
                # fact
                replaced = transform(
                    n.head,
                    lambda x: Variable(f"{common.BINDING_VARIABLE_PREFIX}{x.value}")
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


def convert_dict_values_to_sets(my_dict):
    # Convert each value in the dictionary to a set and join the keys with a comma
    return {','.join([i.value for i in k]): set([i.value for i in v]) for k, v in my_dict.items()}


def test_symconst_unifiable_consts_mapping(program_text):
    program = parse(program_text)
    symconst_unifiable_consts_map = analyse_symbolic_constants(program)

    new_dict = convert_dict_values_to_sets(symconst_unifiable_consts_map)

    answer = {
        'symlog_symbolic_open': set([]),
        'symlog_symbolic_2': set([1, 2, 3, 4, 5]),
        'symlog_symbolic_x': set(['x']),
        'symlog_symbolic_1': set([1, 2, 3, 4, 5]),
    }

    assert new_dict == answer


if __name__ == '__main__':

    program_text = """
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

    # test_symconst_unifiable_consts_mapping(program_text)

    program_text2 = """
.decl InstructionLine(m: symbol, i: symbol, l: symbol, f: symbol)
.decl VarPointsTo(hctx: symbol, a: symbol, ctx: symbol, v: symbol)
.decl Reachable(m: symbol)
.decl SpecialMethodInvocation(instruction:symbol, i: symbol, sig: symbol, base:symbol, m: symbol)
.decl LoadArrayIndex(ins: symbol, i: symbol, to: symbol, base: symbol, m: symbol)
.decl LoadInstanceField(ins: symbol, i: symbol, to: symbol, base: symbol, sig: symbol, m: symbol)

.decl VarPointsToNull(v: symbol)
.decl NullAt(m: symbol, i: symbol, type: symbol)
.decl ReachableNullAt(m: symbol, i: symbol, type: symbol)
.decl ReachableNullAtLine(m: symbol, i: symbol, f: symbol, l: symbol, type:
symbol)

.decl GuardCheck(insn: symbol, op: symbol, var: symbol, const: symbol)
.decl If_Var(insn: symbol, pos: symbol, var: symbol)
.decl If_Constant(insn: symbol, pos: symbol, cons: symbol)
.decl _OperatorAt(insn: symbol, op:symbol)
.output ReachableNullAtLine
.output GuardCheck

GuardCheck(insn, op, var, const) :- _OperatorAt(insn, op), If_Var(insn, _, var), If_Constant(insn, _, const).

VarPointsToNull(var) :- VarPointsTo(_, "<<null pseudo heap>>", _, var).

NullAt(meth, index, "Load Array Index") :-
VarPointsToNull(var),
LoadArrayIndex(_, index, _, var, meth).

ReachableNullAt(meth, index, type) :- NullAt(meth, index, type), Reachable(meth).

ReachableNullAtLine(meth, index, file, line, type) :- 
ReachableNullAt(meth, index, type), 
InstructionLine(meth, index, line, file).
"""

    program = parse(program_text2)

    facts = load_relations('/home/liuyu/info3600-bugchecker-benchmarks/digger/logic/doop_logic/facts')
    database = load_relations('/home/liuyu/info3600-bugchecker-benchmarks/digger/logic/doop_logic/database')
    # merge two dictionaries
    input_facts = {**facts, **database}

    # transform input_fact into a list of fact rules
    fact_rules = []
    for name, relations in input_facts.items():
        if name not in program.declarations:
            continue
        for row in relations:
            args = [String(x) for x in row]
            fact_rules.append(Rule(Literal(name, args, True), []))

    with open('tests/original.dl', 'w') as f:
        program.rules.extend(fact_rules)
        f.write(pprint(program))

    sym_cnt = 0
    def add_sym_fact(name, sym_cnt):
        arity = len(program.declarations[name])
        args = [String(f"{common.SYMBOLIC_CONSTANT_PREFIX}{sym_cnt + idx}") for idx in range(arity)]
        fact_rules.append(Rule(Literal(name, args, True), []))
        sym_cnt += arity
        return sym_cnt
    
    # sym_cnt = add_sym_fact('VarPointsTo', sym_cnt)
    # sym_cnt = add_sym_fact('LoadArrayIndex', sym_cnt)
    # sym_cnt = add_sym_fact('Reachable', sym_cnt)

    sym_cnt = add_sym_fact('_OperatorAt', sym_cnt)
    sym_cnt = add_sym_fact('If_Var', sym_cnt)
    sym_cnt = add_sym_fact('If_Constant', sym_cnt)

    program.rules.extend(fact_rules)

    print(pprint(program))

    transformed = transform_into_meta_program(program)
    declarations = transform_declarations(program)
    facts = create_naive_domain_facts(program)
    abstract_facts = create_abstract_domain_facts(program)

    transformed.rules.extend(facts + abstract_facts)
    transformed.declarations.update(declarations)
    with open('tests/transformed.dl', 'w') as f:
        f.write(pprint(transformed))
