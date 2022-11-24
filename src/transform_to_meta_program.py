import copy
import common
from souffle import collect, transform, parse, pprint, Variable, Literal, Rule, String, Number, Program
import utils

from typing import List, Dict, Set, Tuple, Optional, Union, Any, Callable, DefaultDict
import itertools
from collections import defaultdict

DEBUG = True


def extract_pred_symbolic_consts(fact, symbolic_consts):
    return fact.head.name, [arg for arg in fact.head.args if arg in symbolic_consts]


def constr_pred_consts_lst_map(facts, f):
    d = defaultdict(list)
    for k, v in list(map(f, facts)):
        if v:
            d[k].append(v)
    return d


def constr_loc_joined_locs_map(joined_locs, f):
    d = defaultdict(set)
    for k, v in list(map(f, joined_locs)):
        if v:
            d[k].add(v)
    return d


def analyse_symbolic_constants(p: Program) -> Dict[Tuple[Set[Union[String, Number]]], Set[Union[String, Number]]]:
    """Analyse the constansts that symbolic constants in program `p` in principle attempt to unify with during evaluation."""

    rules = collect(p, lambda x: isinstance(x, Rule))

    Loc = Tuple[str, int]  # loc -> (pred_name, index)
    Value = Union[String, Number]  # value -> (String | Number)
    LocValuesDict = DefaultDict[Loc, Set[Value]]
    LocLocsDict = DefaultDict[Loc, Set[Loc]] 

    def init(rules: List[Rule]) -> Tuple[LocValuesDict, LocValuesDict, LocLocsDict]:

        loc_values_map: LocValuesDict = defaultdict(set) # loc_values -> (Loc -> Values)
        loc_symvalues_map: LocValuesDict = defaultdict(set)
        hloc_blocs_map: DefaultDict[Loc, Set[Loc]] = defaultdict(set) # hloc_blocs -> (Loc -> Set[Loc])
        symloc_unifiable_locs_map: DefaultDict[Loc, Set[Loc]] = defaultdict(set)

        def check_arg_lit(arg: Union[Variable, String, Number], lit: Literal) -> bool:
            if isinstance(arg, Variable) and arg in lit.args and lit.positive:
                return True
            return False

        def find_lit_by_name(name: str, lits: List[Literal]) -> Optional[Literal]:
            for lit in lits:
                if lit.name == name:
                    return lit
            return None

        def find_locs_by_arg(arg: Union[Variable, String, Number], lits: List[Literal]) -> Optional[Set[Loc]]:      
            locs = set()
            for lit in lits:
                if check_arg_lit(arg, lit):
                    locs.add((lit.name, lit.args.index(arg)))
            return locs

        def add_hloc_blocs(rule: Rule) -> None:
            """Add the head location and its corresp positive body locations to `hloc_blocs_map`."""
            for i, arg in enumerate(rule.head.args):
                hloc = (rule.head.name, i)
                hloc_blocs_map[hloc].update(set([(body_lit.name, body_lit.args.index(
                    arg)) for body_lit in rule.body if check_arg_lit(arg, body_lit)]))

        def add_loc_values(fact: Rule) -> None:
            """Add location in fact and its corresp values/symbolic values to `loc_values_map` and `loc_symvalues_map`."""
            for i, arg in enumerate(fact.head.args):
                loc_values_map[(fact.head.name, i)].add(arg)
                if isinstance(arg, String) and arg.value.startswith(common.SYMBOLIC_CONSTANT_PREFIX):
                    loc_symvalues_map[(fact.head.name, i)].add(arg)

        for rule in rules:
            if rule.body:
                add_hloc_blocs(rule) 
            else:
                add_loc_values(rule) # initial values of a location are from facts.

        for symloc in loc_symvalues_map.keys():
            edb_pred_name, idx = symloc
            for rule in rules:
                if not rule.body:
                    continue
                ret_lit = find_lit_by_name(edb_pred_name, rule.body)
                if ret_lit is None:
                    continue
                unifiable_locs = find_locs_by_arg(ret_lit.args[idx], rule.body) - set([symloc])
                symloc_unifiable_locs_map[symloc].update(unifiable_locs)
        
        
        return loc_values_map, loc_symvalues_map, hloc_blocs_map, symloc_unifiable_locs_map

    def analyse_loc_values(loc_values_map: LocValuesDict, hloc_blocs_map: LocLocsDict) -> LocValuesDict:
        is_changed = True

        while is_changed:
            is_changed = False

            for hloc in hloc_blocs_map.keys():
                union_blocs_values = set.union(*[loc_values_map[bloc] for bloc in hloc_blocs_map[hloc]])

                is_changed = not loc_values_map[hloc].issuperset(
                        union_blocs_values) if not is_changed else True
                
                loc_values_map[hloc].update(union_blocs_values)
        
        return loc_values_map

    def construct_unifiable_consts_map(loc_values_map: LocValuesDict, loc_symvalues_map: LocValuesDict, symloc_unifiable_locs_map: LocLocsDict) -> Dict[Tuple[Set[Value]], Set[Value]]:
        # sym const -> set of consts that sym const attempt to unify with
        unifiable_consts_map = dict()

        for loc, symvalues in loc_symvalues_map.items():
            # symconst_key = common.DELIMITER.join([x.value for x in symvalues])

            unifiable_consts_map[tuple(symvalues)] = loc_values_map[loc] | set(
                itertools.chain(*[loc_values_map[jloc] for jloc in symloc_unifiable_locs_map[loc]]))  # union of original constants and in principle to be joined constants

        return unifiable_consts_map

    init_loc_values_map, loc_symvalues_map, hloc_blocs_map, symloc_unifiable_locs_map = init(rules)
    
    loc_values_map = analyse_loc_values(init_loc_values_map, hloc_blocs_map)

    unifiable_consts_map = construct_unifiable_consts_map(loc_values_map, loc_symvalues_map, symloc_unifiable_locs_map)

    if DEBUG:
        # print the loc values map
        print("\nloc_values_map: \n", "\n".join(
            [f"{k} -> {set(map(lambda x: x.value, v))}" for k, v in init_loc_values_map.items()]))

    return unifiable_consts_map


def construct_naive_domain_facts(p):

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


def construct_abstract_domain_facts(p):
    pass


def transform_into_meta_program(p):
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
        Variable(f"{common.BINDING_VARIABLE_PREFIX}{x.value}") for x in symbolic_consts]

    def add_binding_vars_to_literal(l, binding_vars):
        return Literal(l.name, l.args + binding_vars, l.positive)

    def binding_vars_of_pred(pred_name):
        return [Variable(f"{common.BINDING_VARIABLE_PREFIX}{x.value}") for x in pred_sym_consts_map.get(pred_name, [])]

    def add_domain_literal(sym_arg):
        # E.g., domain_alpha(var_alpha)
        return Literal(f"{common.DOMAIN_PREDICATE_PREFIX}{sym_arg.value}", [Variable(f"{common.BINDING_VARIABLE_PREFIX}{sym_arg.value}")], True)

    def transform_declarations():

        def transform_declaration(n):
            if not n.body:
                symbolic_consts_of_n_pred = pred_sym_consts_map.get(
                    n.head.name, [])

                res = [(n.head.name, p.declarations[n.head.name] +
                        [common.DEFAULT_SOUFFLE_TYPE] * len(symbolic_consts_of_n_pred))]  # EDB head declaration

                res.extend(
                    [(f"{common.DOMAIN_PREDICATE_PREFIX}{x.value}", [common.DEFAULT_SOUFFLE_TYPE])
                     for x in symbolic_consts_of_n_pred if p.declarations.get(f"{common.DOMAIN_PREDICATE_PREFIX}{x.value}", None) is None]
                )  # domain declarations

                return res

            else:
                # IDB head declaration
                return [(n.head.name, p.declarations[n.head.name] + [common.DEFAULT_SOUFFLE_TYPE] * len(binding_vars))]

        rules = collect(p, lambda x: isinstance(x, Rule))

        transformed_declarations = {k: v for k, v in itertools.chain(
            *map(transform_declaration, rules))}

        return transformed_declarations

    def add_binding_vars(n):
        if isinstance(n, Rule):
            if not n.body:
                # fact
                replaced = transform(
                    n.head, lambda x: Variable(f"{common.BINDING_VARIABLE_PREFIX}{x.value}") if x in symbolic_consts else x)

                domain_body = [add_domain_literal(
                    x) for x in pred_sym_consts_map.get(n.head.name, [])]

                return Rule(add_binding_vars_to_literal(replaced, binding_vars_of_pred(n.head.name)), domain_body)
            else:
                # rule
                replaced_head = transform(n.head, lambda x: add_binding_vars_to_literal(
                    x, binding_vars) if isinstance(x, Literal) else x)

                replaced_body = list(map(lambda l: transform(l, lambda x: add_binding_vars_to_literal(x, binding_vars_of_pred(
                    x.name) if x.name in edb_names else binding_vars) if isinstance(x, Literal) else x), n.body))

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

    transformed.rules.extend(facts)

    print(pprint(transformed))

    symconst_unifiable_consts_map = analyse_symbolic_constants(program)

    print("\n symconst_unifiable_consts_map: \n" +
          '\n'.join([f"{','.join([i.value for i in k])} -> {[i.value for i in v]}" for k, v in symconst_unifiable_consts_map.items()]))
