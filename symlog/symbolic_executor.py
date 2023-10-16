from symlog.souffle import (
    run_program,
    transform,
    Program,
    Rule,
    Fact,
    Literal,
    String,
    Number,
    SymbolicNumber,
    SymbolicString,
    SymbolicNumberWrapper,
    SymbolicStringWrapper,
)
from symlog.utils import (
    is_sublist,
    flatten_lists_only,
    is_arg_symbolic,
)
from symlog.delta_debugging import ddmin_all_monotonic
from symlog.common import CONTAINS, DOES_NOT_CONTAIN
from symlog.program_builder import infer_whole_program, update_program
from symlog.transformer import transform_program

from typing import List, Dict, Tuple, Any, Optional, Set, FrozenSet, Iterable
from collections import defaultdict, namedtuple
from itertools import product, chain
from more_itertools import partition
from functools import lru_cache
from z3 import Or, And, simplify, Const, IntSort, StringSort, BoolSort


_OutputCondition = namedtuple("OutputCondition", ["sub_conditions"])


class OutputCondition(_OutputCondition):
    """Represents an output condition for generating a Datalog output fact."""

    def __init__(self, sub_conditions: List):
        self._sub_conditions = sub_conditions

    def to_z3(self):
        """Converts the output condition to an z3 formula."""

        formula = [cond.to_z3() for cond in self._sub_conditions]

        final_formula = simplify(Or(formula))
        return final_formula

    def __str__(self) -> str:
        return self.to_z3().__str__()

    def __repr__(self) -> str:
        return self.__str__()

    def __hash__(self) -> int:
        return hash(self.__str__())

    @property
    def symbolic_assigns(self):
        return [
            sub_condition.symbolic_assigns for sub_condition in self._sub_conditions
        ]

    @property
    def dep_facts(self):
        return [sub_condition.dep_facts for sub_condition in self._sub_conditions]

    @property
    def sub_conditions(self):
        return self._sub_conditions


SymbolValueAssignment = namedtuple("SymbolValueAssignment", ["symbol", "value"])


class Condition(
    namedtuple("Condition", ["symbol_value_assigns", "dependent_facts_list"])
):
    z3TypeMap = {
        Number: IntSort(),
        String: StringSort(),
        SymbolicNumber: IntSort(),
        SymbolicString: StringSort(),
        SymbolicNumberWrapper: IntSort(),
        SymbolicStringWrapper: StringSort(),
    }

    def _convert_symbol(self, sym_const) -> Const:
        try:
            return Const(sym_const.name, self.z3TypeMap[type(sym_const)])
        except KeyError:
            raise ValueError(f"Unknown type: {type(sym_const)}")

    def to_z3(self):
        """Converts the condition to an z3 formula."""

        sym_asssign_formula = And(
            [
                (self._convert_symbol(sym_const) == assigned_val.value)
                for sym_const, assigned_val in self.symbol_value_assigns
            ]
        )

        fact_formula = (
            Or(
                [
                    And([Const(str(dep_fact), BoolSort()) for dep_fact in dep_facts])
                    for dep_facts in self.dependent_facts_list
                ]
            )
            if self.dependent_facts_list
            else BoolSort().cast(True)
        )

        formula = And(sym_asssign_formula, fact_formula)
        final_formula = simplify(formula)
        return final_formula

    def __str__(self) -> str:
        return str(self.to_z3())

    def __repr__(self) -> str:
        return self.__str__()

    def __hash__(self) -> int:
        return hash(self.__str__())


class SymbolicExecutor:
    def symex(
        self,
        rules: FrozenSet[Rule],
        input_facts: FrozenSet[Fact],
        interested_output_facts: FrozenSet[Fact],
    ):
        if len(rules) != len(set(rules)):
            print(
                "Warning: Duplicate elements found in 'rules'. Duplicates will be"
                " discarded in frozenset conversion."
            )
        if len(input_facts) != len(set(input_facts)):
            print(
                "Warning: Duplicate elements found in 'facts'. Duplicates will be"
                " discarded in frozenset conversion."
            )
        if len(interested_output_facts) != len(set(interested_output_facts)):
            print(
                "Warning: Duplicate elements found in 'interested_output_facts'."
                " Duplicates will be discarded in frozenset conversion."
            )
        constraints = {}
        # check interested output facts one by one
        for fact in interested_output_facts:
            if any(arg for arg in fact.head.args if is_arg_symbolic(arg)):
                raise ValueError(
                    "Arguments of interested facts are conflict with interal keywords."
                )
            constraints_of_fact = self._cached_symex(
                frozenset(rules), frozenset(input_facts), fact
            )
            constraints.update(constraints_of_fact)
        return constraints

    @lru_cache(maxsize=None)
    def _cached_symex(
        self,
        rules: FrozenSet[Rule],
        input_facts: FrozenSet[Fact],
        interested_output_fact: Fact,
    ):
        """Symbolic execution of the datalog program."""

        # the outputs of the program should at least contain relation of the interested output fact
        outputs = [interested_output_fact.head.name]
        program = infer_whole_program(rules, input_facts, outputs=outputs)

        meta_output_facts = self._transform_exec_meta_program(program)

        # divide output tuples by assignments of symbolic constants and sort them by assignment
        assignment_outputs = {
            k: v
            for k, v in sorted(
                self._divide_outputs_by_assignments(
                    meta_output_facts, program.symbols
                ).items()
            )
        }

        constraints = defaultdict(list)

        # compute constraints under each assignment of symbolic constants
        for symbol_value_assigns, output_facts in assignment_outputs.items():
            constraints_for_intrst_fact = self._preprocess_and_compute_constraints(
                program,
                symbol_value_assigns,
                output_facts,
                interested_output_fact,
            )

            if constraints_for_intrst_fact:
                assert len(constraints_for_intrst_fact) == 1, (
                    "More than one interested fact? "
                    "Bug? "
                    f"constraints_for_intrst_fact: {constraints_for_intrst_fact}"
                )
                for intrst_fact, condition in constraints_for_intrst_fact.items():
                    constraints[intrst_fact].append(condition)

        # further encapulate the constraints
        constraints = {
            output_fact: OutputCondition(conditions)
            for output_fact, conditions in constraints.items()
        }

        return constraints

    @lru_cache(maxsize=None)
    def _get_matched_symbolic_pairs(self, output_fact, intrst_fact):
        """Get the matched symbolic pairs between the constraint fact and the target fact."""
        matched_pairs = []
        is_match = True
        if (output_fact.head.name == intrst_fact.head.name) and len(
            output_fact.head.args
        ) == len(intrst_fact.head.args):
            for arg1, arg2 in zip(output_fact.head.args, intrst_fact.head.args):
                assert not is_arg_symbolic(
                    arg2
                ), "User interested fact cannot be symbolic. Bug?"

                if is_arg_symbolic(arg1):
                    matched_pairs.append((arg1, arg2))
                else:  # check if the arg1 and arg2 are the same
                    if arg1 != arg2:
                        is_match = False
                        break
        if not is_match:
            matched_pairs = []
        return is_match, matched_pairs

    def _get_target_outputs(
        self,
        output_facts: Set[Fact],
        interested_fact: Fact,
    ):
        """
        Get the target outputs that match the interested fact.
        """

        target_outputs = set()

        for output_fact in output_facts:
            # check if the fact matches the target fact by ignoring the internal keywords of symbolic constants
            is_match, _ = self._get_matched_symbolic_pairs(output_fact, interested_fact)
            if is_match:
                target_outputs.add(output_fact)

        return target_outputs

    def _preprocess_and_compute_constraints(
        self,
        program: Program,
        symbol_value_assigns: Tuple[SymbolValueAssignment],
        output_facts: List[Fact],
        interested_out_fact: Fact,
    ):
        """Compute constraints for the interested fact under given assigned symbolic values."""

        # get target outputs NOTE: compute constraints for each target output. Do not repeat the computation for the same target output, thus use set.
        output_facts_set = frozenset(output_facts)

        target_outputs = self._get_target_outputs(output_facts_set, interested_out_fact)

        if not target_outputs:
            return None

        # map symbols to the assigned values
        symbol_value_map = dict(symbol_value_assigns)

        # Add non-symbolic sign facts to the program. The symbolic sign facts
        # will be processed by the delta debugging algorithm
        non_symsign_facts, symsign_facts = self._split_symsign_nonsymsign_facts(
            program.facts
        )

        # concretise all facts with the assigned values to the symbols
        (
            concrete_non_symsign_facts,
            added_concrete_non_symsign_fact_dict,
        ) = self._concretise_facts_with_symbols(non_symsign_facts, symbol_value_map)
        (
            concrete_symsign_facts,
            added_concrete_symsign_fact_dict,
        ) = self._concretise_facts_with_symbols(symsign_facts, symbol_value_map)

        # merge the added concretised fact dicts
        assert (
            set(added_concrete_non_symsign_fact_dict.keys())
            & set(added_concrete_symsign_fact_dict.keys())
            == set()
        ), "Symbolic sign facts and non-symbolic sign facts are intersected. Bug?"

        # update program with the concretised non-symbolic sign facts and
        # remove the symbolic sign facts
        updated_program = update_program(
            program,
            facts=concrete_non_symsign_facts,
        )

        # compute the constraints
        constraints_for_intrst_fact = self._compute_constraints(
            updated_program,
            concrete_symsign_facts,
            symbol_value_assigns,
            target_outputs,
            interested_out_fact,
        )

        return constraints_for_intrst_fact

    def _exists_target(self, input_facts, target_outputs, program):
        """Test if the target outputs are in the output of the datalog program."""

        # flatten the input fatcs before running program
        input_facts = list(flatten_lists_only(input_facts))

        output_facts = run_program(program, input_facts)
        if is_sublist(target_outputs, output_facts):
            return CONTAINS
        else:
            return DOES_NOT_CONTAIN

    def _transform_exec_meta_program(self, program):
        """Transform program to meta program and execute the meta program."""

        transformed_program = transform_program(program)
        # run the transformed program, obtaining all possible outputs
        output_facts = run_program(transformed_program, [])

        # output fact predicates should only include IDB
        assert is_sublist(
            set(f.head.name for f in output_facts),
            set(r.head.name for r in program.rules),
        ), "Output tuples' predicates are not all defined IDB relations"

        return output_facts

    def _compute_constraints(
        self,
        program: Program,
        facts_to_check: List[Rule],
        symbol_value_assigns: Tuple[SymbolValueAssignment],
        target_outputs: Set[Rule],
        interested_out_fact: Fact,
    ) -> Dict[Fact, OutputCondition]:
        """
        Compute constraints for the the interested fact that match the target_outputs under given symbol_value_assigns.
        """

        # compute the list of dependent facts for target outputs, where each dependent facts list in the list can generate the target outputs
        dependent_facts_list = ddmin_all_monotonic(
            self._test_function(target_outputs, program), facts_to_check
        )

        # constraints for interested_out_fact
        constraints = defaultdict(list)

        # replace symbol's payloads with the assigned values in the dependent facts list
        symbol_value_map = dict(symbol_value_assigns)
        payload_to_val = {
            symbol.payload: val for symbol, val in symbol_value_map.items()
        }
        updated_dependent_facts_list = [
            [transform(f, lambda x: payload_to_val.get(x, x)) for f in dependent_facts]
            for dependent_facts in dependent_facts_list
        ]

        for target_fact in target_outputs:
            is_match, matched_symbolic_pairs = self._get_matched_symbolic_pairs(
                target_fact, interested_out_fact
            )
            if matched_symbolic_pairs:
                # further concretise the symbol_value_assigns and updated_dependent_facts_list with the matched values to the symbols
                new_payload_value_map = dict(matched_symbolic_pairs)
                new_symbol_value_assigns = [
                    (
                        symbol,
                        new_payload_value_map.get(symbol.payload, value),
                    )
                    for symbol, value in symbol_value_assigns
                ]
                new_updated_dependent_facts_list = [
                    [
                        transform(f, lambda x: new_payload_value_map.get(x, x))
                        for f in dependent_facts
                    ]
                    for dependent_facts in updated_dependent_facts_list
                ]
                condition = Condition(
                    new_symbol_value_assigns, new_updated_dependent_facts_list
                )
            else:
                condition = Condition(
                    symbol_value_assigns, updated_dependent_facts_list
                )

            constraints[interested_out_fact].append(condition)

        # further encapulate the constraints
        constraints = {
            output_fact: OutputCondition(conditions)
            for output_fact, conditions in constraints.items()
        }

        return constraints

    def _test_function(self, targets, program):
        """Returns a function that tests if the targets are in the output of the datalog program."""
        return lambda facts_to_check: self._exists_target(
            facts_to_check, targets, program
        )

    def _divide_outputs_by_assignments(
        self,
        output_facts: List[Rule],
        symbols: List[SymbolicNumberWrapper | SymbolicStringWrapper],
    ) -> Dict[Tuple[Any, ...], List[Rule]]:
        """
        Divides output tuples by assignments of symbolic constants.

        :param output_facts: A list of output facts to process.
        :return: A dictionary mapping assigned values to simplified output facts.
        """
        assignment_outputs = defaultdict(list)
        symbol_num = len(symbols)

        for output_fact in output_facts:
            output_arg_num = len(output_fact.head.args)

            assert (
                output_arg_num > symbol_num
            ), "Output tuple has less args than the number of symbols?"

            # get last len(symbol_list) args
            assigned_values = tuple(
                output_fact.head.args[output_arg_num - symbol_num :]
            )
            # the rest args are the real output args
            output_args = output_fact.head.args[: output_arg_num - symbol_num]
            simplified_oup_fact = Fact(
                Literal(output_fact.head.name, output_args, True),
                [],
                output_fact.symbolic_sign,
            )

            # map symbols to the assigned values
            symbol_value_tuple = self._create_symbol_value_tuple(
                symbols, assigned_values
            )

            assignment_outputs[symbol_value_tuple].append(simplified_oup_fact)

        return assignment_outputs

    def _create_symbol_value_tuple(self, symbolic_constants, assigned_values):
        """Create a symbol value tuple from the symbolic constants and assigned values."""
        assert len(symbolic_constants) == len(assigned_values), "Mismatched lengths"

        # NOTE: symbol is alias of symbolic constant
        symbol_value_tuple = tuple(
            SymbolValueAssignment(symbol, assigned_values[i])
            for i, symbol in enumerate(symbolic_constants)
        )
        return symbol_value_tuple

    def _concretise_facts_with_symbols(
        self,
        input_facts: FrozenSet[Fact],
        symbol_value_map: Dict[
            SymbolicNumberWrapper | SymbolicStringWrapper, Number | String
        ],
    ) -> Tuple[List[Rule], Dict[Rule, Set[Any]]]:
        """Concretise the input facts with the assigned values to the symbols and get the associated symbols."""

        all_concretised_facts = []
        concretised_facts_with_symbols = {}

        payload_to_symbol = {
            symbol.payload: symbol for symbol in symbol_value_map.keys()
        }
        payload_to_val = {
            symbol.payload: val for symbol, val in symbol_value_map.items()
        }

        for raw_fact in input_facts:
            concretised_args = []
            symbols_in_fact = set()
            for arg in raw_fact.head.args:
                if arg in payload_to_val:
                    concretised_args.append(payload_to_val[arg])
                    symbols_in_fact.add(payload_to_symbol[arg])
                else:
                    concretised_args.append(arg)

            concretised_fact = Fact(
                Literal(raw_fact.head.name, concretised_args, True),
                [],
                raw_fact.symbolic_sign,
            )

            if symbols_in_fact:
                concretised_facts_with_symbols[concretised_fact] = symbols_in_fact

            all_concretised_facts.append(concretised_fact)

        return all_concretised_facts, concretised_facts_with_symbols

    def _split_symsign_nonsymsign_facts(
        self,
        facts: FrozenSet[Fact],
    ) -> Tuple[FrozenSet[Fact], FrozenSet[Fact]]:
        """Split the facts into symbolic sign facts and non symbolic sign facts."""
        non_symbolic_sign_facts, symbolic_sign_facts = map(
            frozenset,
            partition(lambda f: isinstance(f, Fact) and f.symbolic_sign, facts),
        )

        return non_symbolic_sign_facts, symbolic_sign_facts


symbolic_executor = SymbolicExecutor()


def symex(
    rules: List[Rule],
    input_facts: List[Fact],
    interested_output_facts: List[Fact],
):
    return symbolic_executor.symex(rules, input_facts, interested_output_facts)
