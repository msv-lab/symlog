import src.common as common
import src.utils as utils # Path: src/utils.py
import itertools


def get_symbolic_facts(declarations, k):
    """
    Create `k` symbolic facts for each edb of passed `declarations`, where `declarations` is a sub dictionary of all declarations.
    """

    symbolic_facts = {predicate: [[f"{common.ALPHA}{utils.get_id()}" for _ in range(k)] for _ in range(len(args))] for (predicate, args) in declarations.items()}

    return symbolic_facts

def get_EDB_rules(declarations, factsDirectory, k):
    """
    Create new rules for EDB goals. `k` is the number of symbolic facts for each edb.
    The rules have two types:
    1. e1(1, 2, t1, t2):- domain_alpha(t1), domain_beta(t2). e1(1, 2) is the original fact. 
    2. e1(t1, t2, t1, t2):- domain_alpha(t1), domain_beta(t2).
    domain_x refers to the domain of symbol x. E.g.:
    domain_alpha(1).
    domain_alpha('alpha').
    """

    nonsymbolic_facts = utils.load_relations(factsDirectory) # Load all facts from the facts directory
    symbolic_facts = get_symbolic_facts(declarations, k) # Create `k` symbolic facts for each edb
    temporary_vars = [f"{common.VAR}{i}" for i in range(1, k + 1)]
    rules = []

    for relation_name, tuples in nonsymbolic_facts.items():
        for given_tuple in tuples:
            rules.append(_get_EDB_predicate_rule(relation_name, given_tuple, temporary_vars, symbolic_facts[relation_name]))
    rules.append(_get_EDB_predicate_rule(relation_name, temporary_vars, temporary_vars, symbolic_facts[relation_name]))

    rules.extend(_get_domains(relation_name, nonsymbolic_facts, symbolic_facts))

    return rules

def _get_EDB_predicate_rule(relation_name, given_tuple, temporary_vars, symbolic_facts):
    """
    Create a rule for a given EDB relation name and tuples.
    """

    head_tuples = given_tuple + temporary_vars
    head = "{relation_name}({tuples})".format(relation_name=relation_name, tuples=', '.join(head_tuples))
    body = []

    symbolic_vars = list(itertools.chain.from_iterable(symbolic_facts))

    for i in range(len(temporary_vars)):
        body.append("{domain}{symbolic_var}({temporary_var})".format(domain=common.DOMAIN, symbolic_var=symbolic_vars[i], temporary_var=temporary_vars[i]))

    body = ":- {body}".format(body=', '.join(body)) if body else ""

    return "{head}{body}.".format(head=head, body=body)

def _get_domains(relation_name, non_symbolic_facts, symbolic_facts):
    """
    Create a rule for each domain of a given relation name.
    """

    non_symbolic_constants = list(itertools.chain.from_iterable(non_symbolic_facts[relation_name]))
    symbolic_vars = list(itertools.chain.from_iterable(symbolic_facts[relation_name]))

    domain_facts = []
    for symbolic_var in symbolic_vars:
        for non_symbolic_constant in non_symbolic_constants:
            domain_facts.append("{domain}{symbolic_var}({non_symbolic_constant}).".format(domain=common.DOMAIN, symbolic_var=symbolic_var, non_symbolic_constant=non_symbolic_constant))

    return domain_facts