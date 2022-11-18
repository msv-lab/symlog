import src.common as common
from src.souffle import collect, transform, Variable, Literal, Rule, Unification
import itertools


def transform_into_meta_program(p):
    """
    Create new rules for EDB goals. `k` is the number of symbolic facts for each edb. The rules have two types: 
    1. e1(1, 2, t1, t2) :- domain_alpha(t1), domain_beta(t2). e1(1, 2) is the original fact. 
    2. e1(t1, t2, t1, t2) :-
    domain_alpha(t1), domain_beta(t2). domain_x refers to the domain of symbol x. E.g.: domain_alpha(1).
    domain_alpha('gamma!=alpha, gamma!=beta').
    """

    symbolic_consts = collect(p, lambda x: isinstance(
        x, Variable) and x.name.startswith(common.SYMBOLIC_CONSTANT_PREFIX))
    binding_vars = [
        Variable(f"{common.BINDING_VARIABLE_PREFIX}{x.name}") for x in symbolic_consts]

    facts = collect(p, lambda x: isinstance(x, Rule) and len(x.body) == 0)
    relat_sym_consts_list_map = {rel_name: [f.head.args for f in facts if f.head.name == rel_name and f.head.args[0].name.startswith(
        common.SYMBOLIC_CONSTANT_PREFIX)] for rel_name in [f.head.name for f in facts]}

    # Create all symbolic constraints. E.g., symbolic consts are alpha, beta, gamma. Then, we create the following constraints:
    # alpha != beta, alpha != gamma, beta != gamma;
    # alpha = beta, alpha != gamma, beta != gamma;
    # alpha != beta, alpha = gamma, beta != gamma;
    # alpha != beta, alpha != gamma, beta = gamma;
    # alpha = beta, alpha = gamma, beta!= gamma;
    # alpha = beta, alpha != gamma, beta = gamma;
    # alpha != beta, alpha = gamma, beta = gamma.

    # all pairs of symbolic constants
    sym_pairs = list(itertools.combinations(symbolic_consts, 2))
    eq_pair_list_iter = [list(itertools.combinations(sym_pairs, k)) for k in range(0, len(
        symbolic_consts) - 1)]  # the selected k pairs from sym_pairs are equal; the rest are not equal
    symbolic_constrs_list = [[Unification(pair[0], pair[1], True if pair in eq_pair_list else False)
                              for pair in sym_pairs] for eq_pair_list in eq_pair_list_iter]

    def add_declaration(pred_name, types):
        p.declarations[pred_name] = types

    def add_binding_vars_to_literal(l):
        return Literal(l.name, l.args + binding_vars, l.positive)

    def add_symbol_domain_literal(v):
        # E.g., domain_alpha(var_alpha)
        return Literal(f"{common.DOMAIN_PREDICATE_PREFIX}{v.name}", [Variable(f"{common.BINDING_VARIABLE_PREFIX}{v.name}")], True)

    def add_domain_facts(n):

        def contains(sym_constr, v):
            return v.name in sym_constr.left or v.name in sym_constr.right

        def add_fact(pred_name, args):
            return Rule(Literal(pred_name, args, True), [])

        if isinstance(n, Rule) and len(n.body) == 0:

            if not n.head.args[0].name.startswith(common.SYMBOLIC_CONSTANT_PREFIX):
                # n is a constant fact
                const_facts = [add_fact(f"{common.DOMAIN_PREDICATE_PREFIX}{v.name}", [f_const]) for sym_consts in relat_sym_consts_list_map[n.head.name] for (f_const, v) in zip(n.args, sym_consts)]
                return const_facts
            else:
                # constraints for symbolic constants
                symbolic_facts = [add_fact(f"{common.DOMAIN_PREDICATE_PREFIX}{v.name}", list(filter(lambda sym_constr: contains(sym_constr, v), sym_constrs))) for sym_consts in relat_sym_consts_list_map[n.head.name] for v in sym_consts for sym_constrs in symbolic_constrs_list]  # filter the symbolic constraints that contain the symbolic constant
                return symbolic_facts
        else:
            return n

    def add_binding_vars(n):
        if isinstance(n, Rule):
            if len(n.body) == 0:
                # fact
                replaced = transform(
                    n.head, lambda x: f"{common.BINDING_VARIABLE_PREFIX}{x.name}" if x in symbolic_consts else x)
                
                symbolic_consts_of_n = [x for x in collect(n, lambda x: isinstance(
                    x, Variable) and x.name.startswith(common.SYMBOLIC_CONSTANT_PREFIX))]

                domain_literals = [add_symbol_domain_literal(x) for x in symbolic_consts_of_n]
                
                add_declaration(n.head.name, p.declarations[n.head.name] + [common.DEFAULT_SOUFFLE_TYPE] * len(binding_vars))

                map(lambda x: add_declaration(f"{common.DOMAIN_PREDICATE_PREFIX}{x.name}", [common.DEFAULT_SOUFFLE_TYPE]), symbolic_consts_of_n)

                return Rule(add_binding_vars_to_literal(replaced), domain_literals)
            else:
                # rule
                transform(n.head, lambda x: add_binding_vars_to_literal(
                    x) if isinstance(x, Literal) else x)

                map(lambda l: transform(l, lambda x: add_binding_vars_to_literal(x) if isinstance(x, Literal) else x), n.body)

        return n

    return transform(transform(p, add_binding_vars), add_domain_facts)
