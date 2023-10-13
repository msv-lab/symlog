import copy
import symlog.common as common
from symlog.souffle import (
    collect,
    transform,
    pprint,
    Variable,
    Literal,
    Rule,
    String,
    Number,
    Program,
    Aggregator,
    SymbolicString,
    SymbolicNumber,
)
import symlog.utils as utils
from typing import Any, List, Dict, Set, Tuple, Optional, DefaultDict, Union
import itertools
from more_itertools import unique_everseen
from collections import defaultdict, namedtuple
import os

DEBUG = False

Location = namedtuple("Location", ["predicate_name", "index", "arg_name"])
LocationProduct = namedtuple("LocationProduct", ["locations"])


class Transformer:
    def __init__(self, env=None) -> None:
        self.env = env
        self._symbolic_constants = None

    def _extract_pred_symconsts_pair(self, fact: Rule) -> Tuple[str, List[String]]:
        pred_name = fact.head.name
        # get the list of symbolic constants in the predicate arguments
        symbolic_consts = [
            arg for arg in fact.head.args if utils.is_arg_symbolic_or_wildcard(arg)
        ]

        return pred_name, symbolic_consts

    def _group_pred_consts_list(self, facts, f):
        d = defaultdict(list)
        for k, v in list(map(f, facts)):
            if v:
                d[k].append(v)
        return d

    def analyse_symbolic_constants(
        self,
        p: Program,
    ) -> Dict[Tuple[Set[Union[String, Number]]], Set[Union[String, Number]]]:
        # Analyse the constansts that symbolic constants in program `p` in principle
        # attempt to unify with during evaluation.

        rules = collect(p, lambda x: isinstance(x, Rule))

        # Loc = Tuple[str, int]  # loc: (pred_name, index)
        Index = list[int]
        Loc = Tuple[str, Index]  # loc: (pred_name, Index)
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

            def var_in_pos_lit(
                arg: Union[Variable, String, Number], lit: Literal
            ) -> bool:
                if (
                    isinstance(arg, Variable)
                    and isinstance(lit, Literal)
                    and arg in lit.args
                    and lit.positive
                ):
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
                    if var_in_pos_lit(arg, lit):  # only positive literals and var arg
                        locs.add((lit.name, lit.args.index(arg)))
                return locs

            def add_hloc_pos_blocs(rule: Rule) -> None:
                if not rule.body:
                    return  # skip facts.

                for i, arg in enumerate(rule.head.args):
                    if not isinstance(arg, Variable):  # skip complex arg
                        continue

                    hloc = (rule.head.name, i)
                    hloc_pos_blocs_map[hloc].update(
                        set(
                            [
                                (body_lit.name, body_lit.args.index(arg))
                                for body_lit in rule.body
                                if var_in_pos_lit(arg, body_lit)  # only variable arg
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
                        if utils.is_arg_symbolic_or_wildcard(arg):
                            eloc_symvalues_map[(rule.head.name, i)].add(arg)
                else:
                    for lit in [rule.head] + [
                        l for l in rule.body if isinstance(l, Literal)
                    ]:
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

                    if arg_at_loc is None or (
                        isinstance(arg_at_loc, Variable)
                        and arg_at_loc.name == common.DL_UNDERSCORE
                    ):
                        continue  # skip '_' variables

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

        def create_unifiable_consts_map(
            loc_values_map: LocValuesDict,
            eloc_symvalues_map: LocValuesDict,
            symloc_unifiable_locs_map: LocLocsDict,
        ) -> Dict[Tuple[Set[Value]], Set[Value]]:
            # sym const -> set of consts that sym const attempt to unify with
            unifiable_consts_map = defaultdict(set)

            for loc, symvalues in eloc_symvalues_map.items():
                for symvalue in symvalues:
                    # union of set of in principle to-be-joined constants and constants
                    # may at loc #FIXME: originally, it is unifiable_consts_map[symvalue] = set(...). Seems like a bug.
                    unifiable_consts_map[symvalue] |= (
                        set(
                            itertools.chain(
                                *[
                                    loc_values_map[sloc]
                                    for sloc in symloc_unifiable_locs_map[loc]
                                ]
                            )
                        )
                        | loc_values_map[loc]
                    )

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
                        for k, v in loc_values_map.items()
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

    def create_abstract_domain_facts(self, p: Program) -> List[Rule]:
        # facts_dict = defaultdict(set)

        # domain facts for to-be-joined constants
        def create_unifiable_facts() -> List[Rule]:
            symconsts_unifiable_consts_map = self.analyse_symbolic_constants(p)
            unifiable_facts = []

            for sym_const, consts in symconsts_unifiable_consts_map.items():
                for const in consts:
                    sym_pred_name = f"{common.DOMAIN_PREDICATE_PREFIX}{self.symvalue_for_name(sym_const)}"

                    unifiable_facts.append(
                        Rule(Literal(sym_pred_name, [const], True), [])
                    )

            return unifiable_facts

        abstract_domain_facts = create_unifiable_facts()

        return abstract_domain_facts

    def transform_declarations(self, p: Program) -> Dict[str, List[str]]:
        def extract_pred_symconstype_pair(fact):
            # get the name of the predicate
            name = fact.head.name

            # get the list of symbolic constants and their types in the predicate arguments
            symconst_types = [
                (arg, p.relation_decls[name][idx])
                for idx, arg in enumerate(fact.head.args)
                if utils.is_arg_symbolic_or_wildcard(arg)
            ]

            return name, symconst_types

        # collect facts
        facts = collect(p, lambda x: isinstance(x, Rule) and not x.body)

        pred_symconstype_map = utils.flatten_dict(
            self._group_pred_consts_list(
                facts, lambda x: extract_pred_symconstype_pair(x)
            )
        )

        # create a dictionary that maps symbolic constants to their types
        symconst_type_map = {
            symconst: type
            for fact in facts
            for symconst, type in extract_pred_symconstype_pair(fact)[1]
        }

        # symbolic_consts must have the same order as that in transform_into_meta_program
        sym_consts = self._symbolic_constants

        # create a list of the binding variable types
        binding_var_types = [symconst_type_map[x] for x in sym_consts]

        def transform_declaration(n: Rule) -> List[Tuple[Any, Any]]:
            if n.head.name in p.inputs:
                # collect symbolic constant types for the current predicate
                symconstypes_of_pred = pred_symconstype_map.get(n.head.name, [])

                # EDB head declaration
                res = [
                    (
                        n.head.name,
                        p.relation_decls[n.head.name]
                        + [type for _, type in symconstypes_of_pred],
                    )
                ]

                # domain relation_decls
                for symconst, type in symconstypes_of_pred:
                    if (
                        p.relation_decls.get(
                            f"{common.DOMAIN_PREDICATE_PREFIX}{self.symvalue_for_name(symconst)}",
                            None,
                        )
                        is None
                    ):
                        res.append(
                            (
                                f"{common.DOMAIN_PREDICATE_PREFIX}{self.symvalue_for_name(symconst)}",
                                [type],
                            )
                        )

                return res
            elif n.body:
                # else:
                # IDB head declaration
                return [
                    (n.head.name, p.relation_decls[n.head.name] + binding_var_types)
                ]

        rules = collect(p, lambda x: isinstance(x, Rule))

        transformed_declarations = {
            k: v
            for k, v in itertools.chain(
                *[
                    result
                    for result in map(transform_declaration, rules)
                    if result is not None
                ]
            )
        }

        return transformed_declarations

    def transform_into_meta_program(self, program: Program) -> Program:
        # Transform a Datalog program into the meta-Datalog program.

        symbolic_consts = self._symbolic_constants

        # collect facts
        facts = collect(program, lambda x: isinstance(x, Rule) and not x.body)

        pred_symconsts_map = utils.flatten_dict(
            self._group_pred_consts_list(
                facts, lambda x: self._extract_pred_symconsts_pair(x)
            )
        )

        idb_names = set(
            [
                r.head.name
                for r in collect(program, lambda x: isinstance(x, Rule) and x.body)
            ]
        )
        edb_names = program.relation_decls.keys() - idb_names
        special_pred_names = edb_names | common.SOUFFLE_INTRINSIC_PREDS

        binding_vars = [
            Variable(f"{common.BINDING_VARIABLE_PREFIX}{self.symvalue_for_name(x)}")
            for x in symbolic_consts
        ]

        def add_binding_vars_to_literal(
            l: Literal, binding_vars: List[Variable]
        ) -> Literal:
            return Literal(l.name, list(l.args) + binding_vars, l.positive)

        def binding_vars_of_pred(pred_name: str) -> List[Variable]:
            return [
                Variable(f"{common.BINDING_VARIABLE_PREFIX}{self.symvalue_for_name(x)}")
                for x in pred_symconsts_map.get(pred_name, [])
            ]

        def add_binding_vars_to_body_item(
            item: Literal | Aggregator,
        ) -> Literal | Aggregator:
            if isinstance(item, Literal):
                updated_literal = add_binding_vars_to_literal(
                    item,
                    (
                        binding_vars_of_pred(item.name)
                        if item.name in special_pred_names
                        else binding_vars
                    ),
                )
                return updated_literal
            elif isinstance(item, Aggregator):
                updated_atom = add_binding_vars_to_literal(
                    item.atom,
                    (
                        binding_vars_of_pred(item.atom.name)
                        if item.atom.name in special_pred_names
                        else binding_vars
                    ),
                )
                return Aggregator(item.op, updated_atom)
            else:
                return item

        def add_domain_literal(sym_arg: String | Number) -> Literal:
            # E.g., domain_alpha(var_alpha)
            return Literal(
                f"{common.DOMAIN_PREDICATE_PREFIX}{self.symvalue_for_name(sym_arg)}",
                [
                    Variable(
                        f"{common.BINDING_VARIABLE_PREFIX}{self.symvalue_for_name(sym_arg)}"
                    )
                ],
                True,
            )

        def add_binding_vars(n):
            if isinstance(n, Rule):
                if n.head.name in edb_names:
                    # fact
                    replaced_head = transform(
                        n.head,
                        lambda x: (
                            Variable(
                                f"{common.BINDING_VARIABLE_PREFIX}{self.symvalue_for_name(x)}"
                            )
                            if x in symbolic_consts
                            else x
                        ),
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
                    replaced_head = transform(
                        n.head,
                        lambda x: (
                            add_binding_vars_to_literal(x, binding_vars)
                            if isinstance(x, Literal)
                            else x
                        ),
                    )
                    replaced_body = list(
                        map(
                            lambda l: transform(l, add_binding_vars_to_body_item),
                            n.body,
                        )
                    )

                    domain_body = [add_domain_literal(x) for x in symbolic_consts]

                    return Rule(replaced_head, replaced_body + domain_body)

            return n

        return transform(program, add_binding_vars)

    def symvalue_for_name(self, x: Number | String) -> str:
        if isinstance(x, Number):
            return abs(x.value)
        if isinstance(x, SymbolicString):
            return x.name
        if isinstance(x, SymbolicNumber):
            return abs(x.name)
        return x.value

    def is_monotonic_semi_positive_check(self, program: Program) -> bool:
        neg_lit_names = {
            l.name
            for l in collect(
                program, lambda x: isinstance(x, Literal) and not x.positive
            )
        }
        edb_names = program.relation_decls.keys() - {
            r.head.name
            for r in collect(program, lambda x: isinstance(x, Rule) and x.body)
        }

        pos_edb_names = {
            l.name
            for l in collect(
                program,
                lambda x: isinstance(x, Literal) and x.positive and x.name in edb_names,
            )
        }

        if not (
            neg_lit_names.issubset(edb_names)
            and not pos_edb_names.intersection(neg_lit_names)
        ):
            print(
                "The program is not monotonic. Do not symbolize the negative EDB which"
                " also occurs as positive in the program."
            )

    def transform_program(
        self,
        program: Program,
        facts: List[Rule] = None,
        is_store=True,
    ) -> Program:
        program = copy.deepcopy(program)
        if facts:
            assert utils.is_sublist(
                facts, program.facts
            ), "Facts are inconsistent with the current managed program."

        # extract symbolic constants from the program
        self._symbolic_constants = list(
            unique_everseen(collect(program, lambda x: utils.is_symbolic_constant(x)))
        )

        # is_monotonic_semi_positive_check(program)
        output_file = os.path.join(common.TMP_DIR, f"transformed.dl")

        transformed = self.transform_into_meta_program(program)
        relation_decls = self.transform_declarations(program)
        transformed.relation_decls.update(relation_decls)

        abstract_facts = self.create_abstract_domain_facts(program)

        # replace SymbolicString/SymbolicNumber objects with String/Number objects

        transformed.facts.extend(abstract_facts)

        dir_name = os.path.dirname(output_file)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        # # Latest version of Souffle requires all declared .input to have corresponding .fact file.
        # # So, I remove inputs of transformed program to avoid troubles
        # transformed = Program(transformed.type_decls, transformed.relation_decls, transformed.functor_decls, [], transformed.outputs, transformed.rules)

        if is_store:
            with open(output_file, "w") as f:
                f.write(pprint(transformed))
            # print("Transformed program is written to {}".format(output_file))

        return transformed

    @property
    def symbolic_constants(self):
        return self._symbolic_constants
