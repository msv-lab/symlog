import common
from souffle import collect, transform, parse, pprint, Variable, Literal, Rule, String, Number
import utils

import itertools
from collections import defaultdict


def extract_pred_symbolic_consts(fact, symbolic_consts):
    return fact.head.name, [arg for arg in fact.head.args if arg in symbolic_consts]


def constr_pred_consts_lst_map(facts, f):
    d = defaultdict(list)
    for k, v in list(map(f, facts)):
        if v:
            d[k].append(v)
    return d


def constr_varef_joined_varefs_set_map(joined_varefs, f):
    d = defaultdict(set)
    for k, v in list(map(f, joined_varefs)):
        if v:
            d[k].add(v)
    return d


def analyse_symbolic_constants(p):
    """Analyse the constansts that symbolic constants in program `p` in principle attmpte to unify with"""

    facts = collect(p, lambda x: isinstance(x, Rule) and not x.body)
    rules = collect(p, lambda x: isinstance(x, Rule) and x.body)
    sym_facts = collect(p, lambda x: isinstance(x, Rule) and not x.body and any([isinstance(
        arg, String) and str(arg.value).startswith(common.SYMBOLIC_CONSTANT_PREFIX) for arg in x.head.args]))

    # varef -> (pred_name, index), values -> the set of possible values at index of pred
    varef_values_map = defaultdict(set)
    symconst_consts_map = dict()

    def init_varef_values_map():
        for fact in facts:
            for i, arg in enumerate(fact.head.args):
                varef_values_map[(fact.head.name, i)].add(arg)

    def varef_values_of_head(rule):

        def varef_values_of_arg(idx_arg):
            idx, arg = idx_arg
            varef = (rule.head.name, idx)

            return varef, set(itertools.chain(*[varef_values_map[(body_lit.name, body_lit.args.index(arg))] for body_lit in rule.body if arg in body_lit.args and body_lit.positive]))

        return list(map(varef_values_of_arg, enumerate(rule.head.args)))

    def analyse_varef_values_of_program():

        init_varef_values_map()
        is_changed = True

        while is_changed:
            is_changed = False
            for rule in rules:
                for varef, values in varef_values_of_head(rule):
                    is_changed = not varef_values_map[varef].issuperset(
                        values) if not is_changed else True
                    varef_values_map[varef].update(values)

    def joined_varefs_of_sym_const_varef():

        def extract_joined_varef_pair(l1, l2):
            # l1 is the body literal has common variables with l2; l2 is the EDB literal uses symbolic constants
            return [((l2.name, l2.args.index(arg)), (l1.name, l1.args.index(arg))) for arg in set(l2.args).intersection(set(l1.args))]

        def joined_varefs_of_symbolic_fact(sym_fact):
            rules_using_sym_fact = collect(p, lambda x: isinstance(x, Rule) and x.body and any(
                [body_lit.name == sym_fact.head.name for body_lit in x.body if body_lit.positive]))  # positive body literals only

            rule_lit_using_sym_fact = {
                rule: body_lit for rule in rules_using_sym_fact for body_lit in rule.body if body_lit.name == sym_fact.head.name
            }

            varefs = []

            for rule in rules_using_sym_fact:
                lit_using_sym_fact = rule_lit_using_sym_fact[rule]
                varefs.extend(
                    list(itertools.chain(*map(lambda l: extract_joined_varef_pair(l, lit_using_sym_fact), filter(
                        lambda l: set(l.args).intersection(set(lit_using_sym_fact.args)) and l != lit_using_sym_fact, rule.body))))
                )

            return varefs

        joined_varefs = list(itertools.chain(
            *map(joined_varefs_of_symbolic_fact, sym_facts)))

        return constr_varef_joined_varefs_set_map(joined_varefs, lambda x: x)

    def construct_try_unify_consts_map():

        symvaref_joined_varefs_map = joined_varefs_of_sym_const_varef()

        symvaref_joined_consts_map = {x: set(
            itertools.chain(*[varef_values_map[varef] for varef in symvaref_joined_varefs_map[x]])) for x in symvaref_joined_varefs_map}

        symbolic_consts = collect(p, lambda x: (isinstance(
            x, String)) and x.value.startswith(common.SYMBOLIC_CONSTANT_PREFIX))

        pred_sym_consts_list_map = constr_pred_consts_lst_map(
            facts, lambda x: extract_pred_symbolic_consts(x, symbolic_consts))

        pred_consts_list_map = constr_pred_consts_lst_map(
            facts, lambda x: (x.head.name, x.head.args))

        # sym varefs
        sym_varefs = list()
        for pred_name, sym_consts_list in pred_sym_consts_list_map.items():
            if not sym_consts_list:
                return
            sym_varefs.extend(
                [(pred_name, i) for i, _ in enumerate(sym_consts_list[0])]
            )

        for varef in sym_varefs:
            # convert varef to symbolic constants
            symconst_key = common.DELIMITER.join(
                map(lambda x: x[varef[1]].value, pred_sym_consts_list_map[varef[0]]))

            # union of in principle to be joined constants and the original constants
            symconst_consts_map[symconst_key] = set(map(lambda x: x.value, symvaref_joined_consts_map[varef])) if varef in symvaref_joined_consts_map else set() | set(
                map(lambda x: x[varef[1]].value, pred_consts_list_map[varef[0]]))

    analyse_varef_values_of_program()  # analyse varef values of the program `p`
    construct_try_unify_consts_map()

    return symconst_consts_map


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

    symconst_consts_map = analyse_symbolic_constants(program)

    print("\n symconst_consts_map")
    for k, v in symconst_consts_map.items():
        print(k, v)
