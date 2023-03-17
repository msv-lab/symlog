import core.common as common
from core.souffle import collect, transform, pprint, Variable, Literal, Rule, String, Number, Program
import core.utils as utils
from typing import Any, List, Dict, Set, Tuple, Optional, DefaultDict, Union
import itertools
from collections import defaultdict
import os

DEBUG = False
id_dict = {} # store the mapping from ids of symbolic constants to natural numbers


def _extract_pred_symconsts_pair(fact: Rule) -> Tuple[str, List[String]]:
    pred_name = fact.head.name
    # get the list of symbolic constants in the predicate arguments
    symbolic_consts = [arg for arg in fact.head.args if utils.is_arg_symbolic(arg)]

    return pred_name, symbolic_consts


def _group_pred_consts_list(facts, f):
    d = defaultdict(list)
    for k, v in list(map(f, facts)):
        if v:
            d[k].append(v)
    return d


def analyse_symbolic_constants(
    p: Program,
) -> Dict[Tuple[Set[Union[String, Number]]], Set[Union[String, Number]]]:
    # Analyse the constansts that symbolic constants in program `p` in principle
    # attempt to unify with during evaluation.

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

                if arg_at_loc is None or (isinstance(arg_at_loc, Variable) 
                and arg_at_loc.name == common.DL_UNDERSCORE):
                    continue # skip '_' variables

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
        # Analyse the values that variable at loc can take during evaluation
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
            # union of set of in principle to-be-joined constants and constants
            # may at loc
            unifiable_consts_map[tuple(symvalues)] = set(
                itertools.chain(
                    *[loc_values_map[sloc] for sloc in symloc_unifiable_locs_map[loc]]
                )
            )  | loc_values_map[loc]

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


def create_abstract_domain_facts(p: Program) -> List[Rule]:

    facts_dict = defaultdict(set)
    
    # domain facts for to-be-joined constants
    def create_unifiable_facts() -> List[Rule]:
        symconsts_unifiable_consts_map = analyse_symbolic_constants(p)
        unifiable_facts = []

        for symconsts, consts in symconsts_unifiable_consts_map.items():
            for sym_const, const in itertools.product(symconsts, consts):

                sym_pred_name = f"{common.DOMAIN_PREDICATE_PREFIX}{symvalue_for_name(sym_const)}"
                for typ in p.declarations[sym_pred_name]:
                    if typ == common.SOUFFLE_SYMBOL:
                        facts_dict[sym_pred_name] |= set([const.value])
                    elif typ == common.SOUFFLE_NUMBER:
                        facts_dict[sym_pred_name] |= {const.value}

        ulti_dict = defaultdict(list)
        for pred_name, facts in facts_dict.items():
            ulti_dict[pred_name] = [[f] for f in facts]

        unifiable_facts = transform_input_facts(ulti_dict, p.declarations)
        return unifiable_facts

    abstract_domain_facts = create_unifiable_facts()

    print('abstract domain facts num: ', len(abstract_domain_facts))

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
        _group_pred_consts_list(facts, lambda x: 
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
                if p.declarations.get(f"{common.DOMAIN_PREDICATE_PREFIX}{symvalue_for_name(symconst)}", None) is None:
                    res.append(
                        (f"{common.DOMAIN_PREDICATE_PREFIX}{symvalue_for_name(symconst)}", [type]))

            return res

        else:
            # IDB head declaration
            return [(n.head.name, p.declarations[n.head.name] + binding_var_types)]

    rules = collect(p, lambda x: isinstance(x, Rule))

    transformed_declarations = {k: v for k, v in itertools.chain(
        *map(transform_declaration, rules))}

    return transformed_declarations


def transform_into_meta_program(p: Program) -> Program:
    # Transform a Datalog program into the meta-Datalog program.

    symbolic_consts = collect(
        p,
        lambda x: utils.is_arg_symbolic(x)
    )

    # collect facts
    facts = collect(p, lambda x: isinstance(x, Rule) and not x.body)

    pred_symconsts_map = utils.flatten_dict(_group_pred_consts_list(
        facts, lambda x: _extract_pred_symconsts_pair(x)))

    edb_names = p.declarations.keys() - set([r.head.name for r in collect(p, lambda x: isinstance(x, Rule) and x.body)])
    special_pred_names = edb_names | common.SOUFFLE_INTRINSIC_PREDS

    binding_vars = [
        Variable(f"{common.BINDING_VARIABLE_PREFIX}{symvalue_for_name(x)}") for x in symbolic_consts
    ]

    def add_binding_vars_to_literal(
        l: Literal, binding_vars: List[Variable]
    ) -> Literal:
        return Literal(l.name, l.args + binding_vars, l.positive)

    def binding_vars_of_pred(pred_name: str) -> List[Variable]:
        return [
            Variable(f"{common.BINDING_VARIABLE_PREFIX}{symvalue_for_name(x)}")
            for x in pred_symconsts_map.get(pred_name, [])
        ]

    def add_domain_literal(sym_arg: Union[String, Number]) -> Literal:
        # E.g., domain_alpha(var_alpha)
        return Literal(
            f"{common.DOMAIN_PREDICATE_PREFIX}{symvalue_for_name(sym_arg)}",
            [Variable(f"{common.BINDING_VARIABLE_PREFIX}{symvalue_for_name(sym_arg)}")],
            True,
        )

    def add_binding_vars(n):
        if isinstance(n, Rule):
            if not n.body:
                # fact
                replaced_head = transform(
                    n.head,
                    lambda x: Variable(f"{common.BINDING_VARIABLE_PREFIX}{symvalue_for_name(x)}")
                    if x in symbolic_consts
                    else x,
                )

                domain_body = [
                    add_domain_literal(x)
                    for x in pred_symconsts_map.get(n.head.name, [])
                ]

                return Rule(
                    add_binding_vars_to_literal(
                        replaced_head, binding_vars_of_pred(n.head.name)
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


def symvalue_for_name(x: Number|String) -> str:
    if isinstance(x, Number):
        return abs(x.value)
    return x.value


def transform_input_facts(input_facts: Dict[str, List[List[str]]], declarations: Dict[str, List[str]]) -> List[Rule]:
    # transform input_fact into a list of fact rules

    def to_parsed_arg(x, x_type):
        if x_type == common.SOUFFLE_NUMBER:
            return Number(x)
        elif x_type == common.SOUFFLE_SYMBOL:
            return String(x)
        else:
            raise ValueError('Unsupported type: {}'.format(x_type))

    fact_rules = []

    for name, arguments in input_facts.items():
        if name in declarations:
                for row in arguments:
                    if len(row) != len(declarations[name]):
                        raise ValueError('Invalid input facts: {} does not match declaration {}'.format(row, declarations[name]))
                    fact_rules.append(Rule(Literal(name, [to_parsed_arg(x, declarations[name][idx]) for idx, x in enumerate(row)], True), []))

    return fact_rules


def is_monotonic_semi_positive_check(program: Program) -> bool:
    neg_lit_names = {l.name for l in collect(program, lambda x: isinstance(x, Literal) and not x.positive)}
    edb_names = program.declarations.keys() - {r.head.name for r in collect(program, lambda x: isinstance(x, Rule) and x.body)}

    pos_edb_names = {l.name for l in collect(program, lambda x: isinstance(x, Literal) and x.positive and x.name in edb_names)}

    if not(neg_lit_names.issubset(edb_names) and not pos_edb_names.intersection(neg_lit_names)):
        print('The program is not monotonic. Do not symbolize the negative EDB which also occurs as positive in the program.')

def transform_program(program: Program, input_facts: Dict[str, List[List[str]]], is_store=True) -> Program:

    is_monotonic_semi_positive_check(program)
    output_file = os.path.join(common.TMP_DIR, f'transformed.dl')

    fact_rules = transform_input_facts(input_facts, program.declarations)
    program.rules.extend(fact_rules)

    transformed = transform_into_meta_program(program)
    declarations = transform_declarations(program)
    transformed.declarations.update(declarations)

    abstract_facts = create_abstract_domain_facts(program)
    transformed.rules.extend(abstract_facts)

    dir_name = os.path.dirname(output_file)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    if is_store:
        with open(output_file, 'w') as f:
            f.write(pprint(transformed))
        print('Transformed program is written to {}'.format(output_file))

    return transformed

