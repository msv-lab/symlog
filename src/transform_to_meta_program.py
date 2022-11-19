import src.common as common
from src.souffle import collect, transform, parse, pprint, Variable, Literal, Rule, String, Number
import src.utils as utils

import itertools
import copy
from collections import namedtuple
from collections import defaultdict


def extract_pred_symbolic_consts(fact, symbolic_consts):
    return fact.head.name, [arg for arg in fact.head.args if arg in symbolic_consts]

def constr_pred_consts_lst_map(facts, f):
    d = defaultdict(list)
    for k, v in list(map(f, facts)):
        if v: d[k].append(v)
    return d


def construct_naive_domain_facts(p):

    symbolic_consts = collect(p, lambda x: (isinstance(
        x, String) or isinstance(x, Number)) and str(x.value).startswith(common.SYMBOLIC_CONSTANT_PREFIX))

    facts = collect(p, lambda x: isinstance(x, Rule) and not x.body)

    pred_sym_consts_list_map = constr_pred_consts_lst_map(facts, lambda x: extract_pred_symbolic_consts(x, symbolic_consts))

    pred_consts_list_map = constr_pred_consts_lst_map(facts, lambda x: (x.head.name, x.head.args))

    def construct_fact(pred_name, args):
        return Rule(Literal(pred_name, args, True), [])

    const_facts = []
    for pred_name in pred_sym_consts_list_map.keys():
        for sym_consts, consts in itertools.product(pred_sym_consts_list_map[pred_name], pred_consts_list_map[pred_name]):
            const_facts.extend([construct_fact(f"{common.DOMAIN_PREDICATE_PREFIX}{sym_const.value}", [Variable(f"{const}")]) for (const, sym_const) in zip(consts, sym_consts)])

    return const_facts


def construct_abstract_domain_facts(p):
    pass


def transform_into_meta_program(p):
    """
    Create new rules for EDB goals. `k` is the number of symbolic facts for each
    edb. The rules have two types: 1. e1(1, 2, t1, t2) :- domain_alpha(t1),
    domain_beta(t2). e1(1, 2) is the original fact. 2. e1(t1, t2, t1, t2) :-
    domain_alpha(t1), domain_beta(t2).
    """

    symbolic_consts = collect(p, lambda x: (isinstance(
        x, String) or isinstance(x, Number)) and str(x.value).startswith(common.SYMBOLIC_CONSTANT_PREFIX))

    declarations = copy.deepcopy(p.declarations)

    # collect facts
    facts = collect(p, lambda x: isinstance(x, Rule) and not x.body)

    pred_sym_consts_map = utils.flatten_dict(constr_pred_consts_lst_map(facts, lambda x: extract_pred_symbolic_consts(x, symbolic_consts)))

    edb_names = list(map(lambda x: x.head.name, facts))

    binding_vars = [
        Variable(f"{common.BINDING_VARIABLE_PREFIX}{x.value}") for x in symbolic_consts]

    def add_declaration(name, types):
        p.declarations[name] = types

    def add_binding_vars_to_literal(l, binding_vars):
        return Literal(l.name, l.args + binding_vars, l.positive)

    def binding_vars_of_pred(pred_name):
        return [Variable(f"{common.BINDING_VARIABLE_PREFIX}{x.value}") for x in pred_sym_consts_map.get(pred_name, [])]

    def add_domain_literal(sym_arg):
        # E.g., domain_alpha(var_alpha)
        return Literal(f"{common.DOMAIN_PREDICATE_PREFIX}{sym_arg.value}", [Variable(f"{common.BINDING_VARIABLE_PREFIX}{sym_arg.value}")], True)

    def add_declarations(n):

        if isinstance(n, Rule):
            if len(n.body) == 0:
                symbolic_consts_of_n_pred = pred_sym_consts_map.get(n.head.name, [])

                add_declaration(n.head.name, declarations[n.head.name] + [common.DEFAULT_SOUFFLE_TYPE] * len(symbolic_consts_of_n_pred))

                for x in symbolic_consts_of_n_pred:  # add domain_symbol declarations
                    if p.declarations.get(f"{common.DOMAIN_PREDICATE_PREFIX}{x.value}", None) is None:
                        add_declaration(f"{common.DOMAIN_PREDICATE_PREFIX}{x.value}", [common.DEFAULT_SOUFFLE_TYPE])
            else:

                add_declaration(n.head.name, declarations[n.head.name] + [common.DEFAULT_SOUFFLE_TYPE] * len(binding_vars))

        return n

    def add_binding_vars(n):
        if isinstance(n, Rule):
            if len(n.body) == 0:
                # fact
                replaced = transform(
                    n.head, lambda x: Variable(f"{common.BINDING_VARIABLE_PREFIX}{x.value}") if x in symbolic_consts else x)

                domain_body = [add_domain_literal(x) for x in pred_sym_consts_map.get(n.head.name, [])]

                return Rule(add_binding_vars_to_literal(replaced, binding_vars_of_pred(n.head.name)), domain_body)
            else:
                # rule
                replaced_head = transform(n.head, lambda x: add_binding_vars_to_literal(
                    x, binding_vars) if isinstance(x, Literal) else x)

                replaced_body = list(map(lambda l: transform(l, lambda x: add_binding_vars_to_literal(x, binding_vars_of_pred(x.name) if x.name in edb_names else binding_vars) if isinstance(x, Literal) else x), n.body))

                domain_body = [add_domain_literal(x) for x in symbolic_consts]

                return Rule(replaced_head, replaced_body + domain_body)

        return n

    return transform(transform(p, add_declarations), add_binding_vars)


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

