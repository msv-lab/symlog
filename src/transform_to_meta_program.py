import common
from souffle import collect, transform, parse, pprint, Variable, Literal, Rule, String, Number, Program
import utils

from typing import Any, List, Dict, Set, Tuple, Optional, DefaultDict
import itertools
from collections import defaultdict
from sympy.utilities.iterables import multiset_partitions

DEBUG = True


def extract_pred_symbolic_consts(fact, symbolic_consts):
    return fact.head.name, [arg for arg in fact.head.args if arg in 
    symbolic_consts]


def constr_pred_consts_lst_map(facts, f):
    d = defaultdict(list)
    for k, v in list(map(f, facts)):
        if v:
            d[k].append(v)
    return d


def analyse_symbolic_constants(p: Program) -> Dict[Tuple[Set[String | Number]], Set[String | Number]]:
    """Analyse the constansts that symbolic constants in program `p` in principle attempt to unify with during evaluation."""

    rules = collect(p, lambda x: isinstance(x, Rule))

    Loc = Tuple[str, int]  # loc: (pred_name, index)
    Value = String | Number
    LocValuesDict = DefaultDict[Loc, Set[Value]]
    LocLocsDict = DefaultDict[Loc, Set[Loc]]

    def init_maps(rules: List[Rule]) -> Tuple[LocValuesDict, LocValuesDict, LocLocsDict, LocLocsDict]:

        # loc -> set of values that variable at loc can take
        loc_values_map: LocValuesDict = defaultdict(set)
        # loc in edb -> set of symbolic values that variable at loc can take
        eloc_symvalues_map: LocValuesDict = defaultdict(set)
        # loc in head -> set of locs in body that share the same variable as loc
        # in head
        hloc_pos_blocs_map: DefaultDict[Loc, Set[Loc]] = defaultdict(set)
        # loc of sym const in edb -> set of locs where variables try to unified
        # with sym const
        symloc_unifiable_locs_map: DefaultDict[Loc, Set[Loc]] = defaultdict(
            set)

        def var_in_pos_lit(arg: Variable | String | Number, lit: Literal) -> bool:
            if isinstance(arg, Variable) and arg in lit.args and lit.positive:
                return True
            return False

        def find_arg_at_loc(loc: Loc, rule: Rule) -> Optional[String | Number | Variable]:
            pred_name, idx = loc
            for l in rule.body:
                if l.name == pred_name:
                    return l.args[idx]
            return None

        def find_unifiable_locs_of_arg(arg: Variable | String | Number, lits: List[Literal]) -> Set[Loc]:
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
                hloc_pos_blocs_map[hloc].update(set([(body_lit.name, body_lit.args.index(
                    arg)) for body_lit in rule.body if var_in_pos_lit(arg, 
                    body_lit)]))  # only positive literals

        def add_loc_values(rule: Rule) -> None:
            if not rule.body:
                for i, arg in enumerate(rule.head.args):
                    # store loc, and corresp value in fact
                    loc_values_map[(rule.head.name, i)].add(arg)

                    # when value is symbolic, add loc, value to
                    # loc_symvalues_map
                    if isinstance(arg, String) and arg.value.startswith(common.SYMBOLIC_CONSTANT_PREFIX):
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
            for rule in collect(p, lambda x: isinstance(x, Rule) and x.body):  # non-facts rules
                arg_at_loc = find_arg_at_loc(loc, rule)
                if arg_at_loc is None:
                    continue
                unifiable_locs = find_unifiable_locs_of_arg(
                    arg_at_loc, rule.body) - set([loc])
                symloc_unifiable_locs_map[loc].update(unifiable_locs)

        return loc_values_map, eloc_symvalues_map, hloc_pos_blocs_map, symloc_unifiable_locs_map

    def analyse_loc_values(loc_values_map: LocValuesDict, hloc_blocs_map: LocLocsDict) -> LocValuesDict:
        """Analyse the values that variable at loc can take during evaluation."""
        is_changed = True

        while is_changed:
            is_changed = False

            for hloc in hloc_blocs_map.keys():
                union_blocs_values = set.union(
                    *[loc_values_map[bloc] for bloc in hloc_blocs_map[hloc]])

                is_changed = not loc_values_map[hloc].issuperset(
                    union_blocs_values) if not is_changed else True

                loc_values_map[hloc].update(union_blocs_values)

        return loc_values_map

    def construct_unifiable_consts_map(loc_values_map: LocValuesDict,
                                       eloc_symvalues_map: LocValuesDict, 
                                       symloc_unifiable_locs_map: LocLocsDict) -> Dict[Tuple[Set[Value]], Set[Value]]:

        # sym const -> set of consts that sym const attempt to unify with
        unifiable_consts_map = dict()

        for loc, symvalues in eloc_symvalues_map.items():
            unifiable_consts_map[tuple(symvalues)] = set(
                itertools.chain(*[loc_values_map[jloc] for jloc in
                                  symloc_unifiable_locs_map[loc]]))  # set of in principle to-be-joined constants

        return unifiable_consts_map

    init_loc_values_map, eloc_symvalues_map, hloc_blocs_map, symloc_unifiable_locs_map = init_maps(
        rules)

    loc_values_map = analyse_loc_values(init_loc_values_map, hloc_blocs_map)

    unifiable_consts_map = construct_unifiable_consts_map(
        loc_values_map, eloc_symvalues_map, symloc_unifiable_locs_map)

    if DEBUG:
        # print the loc values map
        print("\nloc_values_map: \n", "\n".join(
            [f"{k} -> {set(map(lambda x: x.value, v))}" for k, v in
             init_loc_values_map.items()]))

    return unifiable_consts_map


def construct_naive_domain_facts(p: Program) -> List[Rule]:

    symbolic_consts = collect(p, lambda x: (isinstance(
        x, String)) and x.value.startswith(common.SYMBOLIC_CONSTANT_PREFIX))

    facts = collect(p, lambda x: isinstance(x, Rule) and not x.body)

    pred_sym_consts_list_map = constr_pred_consts_lst_map(
        facts, lambda x: extract_pred_symbolic_consts(x, symbolic_consts))

    pred_consts_list_map = constr_pred_consts_lst_map(
        facts, lambda x: (x.head.name, x.head.args))

    def construct_fact(pred_name, args):
        return Rule(Literal(pred_name, args, True), [])

    const_facts = []
    for pred_name in pred_sym_consts_list_map.keys():
        for sym_consts, consts in itertools.product(pred_sym_consts_list_map[pred_name], pred_consts_list_map[pred_name]):
            const_facts.extend([construct_fact(f"{common.DOMAIN_PREDICATE_PREFIX}{sym_const.value}", [
                               const]) for (const, sym_const) in zip(consts, sym_consts)])

    return const_facts


def construct_abstract_domain_facts(p: Program) -> List[Rule]:
    symconst_unifiable_consts_map = analyse_symbolic_constants(p)
    sym_consts = collect(p, lambda x: isinstance(
        x, String) and x.value.startswith(common.SYMBOLIC_CONSTANT_PREFIX))

    def construct_fact(pred_name: str, args: List[String | Number]) -> Rule:
        return Rule(Literal(pred_name, args, True), [])

    def construct_sym_cstr(sym_const: String, equiv_partition: List[List[String]]) -> List[str]:
        eq_relations = []
        neq_relations = []
        eqclass_of_symconst = None

        for equiv_class in equiv_partition:
            if sym_const in equiv_class:
                eqclass_of_symconst = equiv_class
                eq_relations.append(sorted(equiv_class, key=lambda x: x.value))

            else:
                neq_relations.append(
                    sorted(equiv_class, key=lambda x: x.value))

        if eqclass_of_symconst is None:
            raise ValueError(
                f"Symbolic constant {sym_const} is not in any equivalence class")

        def sort_and_to_string(eq_relations: List[List[String]], neq_relations: List[List[String]], eqclass_of_symconst: List[String]) -> List[str]:
            eq_relations.sort()
            neq_relations.sort()

            str_relations = [str([eqc.value for eqc in equiv_rel]) for equiv_rel in eq_relations] + \
                [common.EQ_NONEQ] + \
                [str([neqc.value for neqc in non_equiv_rel])
                 for non_equiv_rel in neq_relations]

            str_eq_class = common.DELIMITER.join(
                [sym.value for sym in sorted(eqclass_of_symconst)])

            str_relations.insert(0, str_eq_class)
            return str_relations

        return sort_and_to_string(eq_relations, neq_relations, eqclass_of_symconst)

    def construct_symcstr_facts() -> List[Rule]:
        """Construct the facts of symbolic constraints."""

        # divide the sym consts into equivalence classes: https://math.stackexchange.com/questions/703475/determine-the-number-of-equivalence-relations-on-the-set-1-2-3-4
        equiv_partitions = itertools.chain(
            *[multiset_partitions(sym_consts, k) for k in range(1, len
            (sym_consts)-1)])  # end at len -1 because the case where all symbolic constants are mutually inequivalent is duplicated.

        symcstr_facts = []

        for (sym_const, equiv_partition) in itertools.product(sym_consts, equiv_partitions):

            symconst_cstr = common.DELIMITER.join(
                construct_sym_cstr(sym_const, equiv_partition))

            symcstr_facts.append(construct_fact(
                f"{common.DOMAIN_PREDICATE_PREFIX}{sym_const.value}", [String
                (symconst_cstr)]))

        return symcstr_facts

    # domain facts for to-be-joined constants
    def construct_unifiable_facts() -> List[Rule]:
        return [construct_fact(f"{common.DOMAIN_PREDICATE_PREFIX}{sym_const}", 
        [const]) for sym_const, consts in symconst_unifiable_consts_map.items() 
        for const in consts]

    sym_cstr_facts = construct_symcstr_facts()
    unifiable_symconst_facts = construct_unifiable_facts()

    abstract_domain_facts = sym_cstr_facts + unifiable_symconst_facts

    return abstract_domain_facts


def transform_into_meta_program(p: Program) -> Program:
    """Transform a Datalog program into the meta-Datalog program. E.g.,
    Original Datalog program: 
    r(x, x) :- n(x).
    r(x, y) :- r(x, z), e(z, y).
    e(1, 2).
    e(alpha, beta).
    n(1).
    n(2).
    n(gamma).
    Transformed meta-Datalog program:
    r(x, x, t1, t2, t3) :-
        n(x, t3),
        domain_alpha(t1),
        domain_beta(t2),
        domain_gamma(t3).
    r(x, y, t1, t2, t3) :-
        r(x, z, t1, t2, t3),
        e(z, y, t1, t2),
        domain_alpha(t1),
        domain_beta(t2),
        domain_gamma(t3).
    e(1, 2, t1, t2) :-
        domain_alpha(t1),
        domain_beta(t2).
    e(t1, t2, t1, t2) :-
        domain_alpha(t1),
        domain_beta(t2).
    n(1, t3) :-
        domain_gamma(t3).
    n(2, t3) :- domain_gamma(t3).
    n(t3, t3) :-domain_gamma(t3).
    """

    symbolic_consts = collect(p, lambda x: (isinstance(
        x, String) or isinstance(x, Number)) and str(x.value).startswith(common.SYMBOLIC_CONSTANT_PREFIX))

    # collect facts
    facts = collect(p, lambda x: isinstance(x, Rule) and not x.body)

    pred_sym_consts_map = utils.flatten_dict(constr_pred_consts_lst_map(
        facts, lambda x: extract_pred_symbolic_consts(x, symbolic_consts)))

    edb_names = list(map(lambda x: x.head.name, facts))

    binding_vars = [
        Variable(f"{common.BINDING_VARIABLE_PREFIX}{x.value}") for x in
        symbolic_consts]

    def add_binding_vars_to_literal(l: Literal, binding_vars: List[Variable]) -> Literal:
        return Literal(l.name, l.args + binding_vars, l.positive)

    def binding_vars_of_pred(pred_name: str) -> List[Variable]:
        return [Variable(f"{common.BINDING_VARIABLE_PREFIX}{x.value}") for x in 
        pred_sym_consts_map.get(pred_name, [])]

    def add_domain_literal(sym_arg: String | Number) -> Literal:
        # E.g., domain_alpha(var_alpha)
        return Literal(f"{common.DOMAIN_PREDICATE_PREFIX}{sym_arg.value}",
                       [Variable(f"{common.BINDING_VARIABLE_PREFIX}{sym_arg.value}")], True)

    def transform_declarations() -> Dict[str, List[str]]:

        def transform_declaration(n: Rule) -> List[Tuple[Any, Any]]:
            if not n.body:
                symbolic_consts_of_n_pred = pred_sym_consts_map.get(
                    n.head.name, [])

                res = [(n.head.name, p.declarations[n.head.name] +
                        [common.DEFAULT_SOUFFLE_TYPE] * len
                        (symbolic_consts_of_n_pred))]  # EDB head declaration

                res.extend(
                    [(f"{common.DOMAIN_PREDICATE_PREFIX}{x.value}", [common.DEFAULT_SOUFFLE_TYPE])
                     for x in symbolic_consts_of_n_pred if p.declarations.get(f"{common.DOMAIN_PREDICATE_PREFIX}{x.value}", None) is None]
                )  # domain declarations

                return res

            else:
                # IDB head declaration
                return [(n.head.name, p.declarations[n.head.name] + [common.
                                                                     DEFAULT_SOUFFLE_TYPE] 
                                                                     * len
                                                                     (binding_vars))]

        rules = collect(p, lambda x: isinstance(x, Rule))

        transformed_declarations = {k: v for k, v in itertools.chain(
            *map(transform_declaration, rules))}

        return transformed_declarations

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
                                              x, binding_vars) if isinstance(x, 
                                              Literal) else x)

                replaced_body = list(map(lambda l: transform(l, lambda x: add_binding_vars_to_literal(x, binding_vars_of_pred(
                    x.name) if x.name in edb_names else binding_vars) if
                    isinstance(x, Literal) else x), n.body))

                domain_body = [add_domain_literal(x) for x in symbolic_consts]

                return Rule(replaced_head, replaced_body + domain_body)

        return n

    transformed_decls = transform_declarations()
    p.declarations.update(transformed_decls)

    return transform(p, add_binding_vars)


if __name__ == "__main__":

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

    program = parse(program_text)

    transformed = transform_into_meta_program(program)

    facts = construct_naive_domain_facts(program)

    abstract_facts = construct_abstract_domain_facts(program)

    transformed.rules.extend(facts + abstract_facts)

    print(pprint(transformed))

    symconst_unifiable_consts_map = analyse_symbolic_constants(program)

    print("\n symconst_unifiable_consts_map: \n" +
          '\n'.join([f"{','.join([i.value for i in k])} -> {[i.value for i in v]}" for k, v in symconst_unifiable_consts_map.items()]))
