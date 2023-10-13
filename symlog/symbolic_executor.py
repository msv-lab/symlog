from symlog.souffle import (
    run_program,
    Program,
    Rule,
    Literal,
    String,
    Number,
    SymbolicNumber,
    SymbolicString,
)
from symlog.utils import is_sublist, flatten_lists_only, is_arg_symbolic
from symlog.delta_debugging import ddmin_all_monotonic
from symlog.common import CONTAINS, DOES_NOT_CONTAIN

from typing import List, Dict, Tuple, Any, Optional, Set
from collections import defaultdict, namedtuple, Counter
from itertools import product, chain
from functools import lru_cache
from z3 import Or, And, simplify, Const, IntSort, StringSort, BoolSort


_AtomicCondition = namedtuple("AtomicCondition", ["symbolic_assigns", "dep_facts"])


class AtomicCondition(_AtomicCondition):
    """Represents an atomic condition for generating a Datalog output fact."""

    PysmtTypeMap = {
        Number: IntSort(),
        String: StringSort(),
        SymbolicNumber: IntSort(),
        SymbolicString: StringSort(),
    }

    def _convert_symbol(self, sym_const) -> Const:
        try:
            return Const(sym_const.name, self.PysmtTypeMap[type(sym_const)])
        except KeyError:
            raise ValueError(f"Unknown type: {type(sym_const)}")

    def to_z3(self):
        """Converts the atomic condition to an z3 formula."""

        formula = And(
            [
                (self._convert_symbol(sym_const) == assigned_val.value)
                for sym_const, assigned_val in self.symbolic_assigns
            ]
            + [Const(str(dep_fact), BoolSort()) for dep_fact in self.dep_facts]
        )

        final_formula = simplify(formula)
        return final_formula


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
        return self.to_z3().sexpr()

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


class SymbolicExecutor:
    def __init__(self, env=None):
        self.env = env
        self.mgr = env.program_manager
        self.trf = env.transformer

    def symex(
        self, rules: list, input_facts: list, interested_output_facts: set = None
    ):
        """Symbolic execution of the datalog program."""

        program = self.mgr.program

        assert is_sublist(
            rules, program.rules
        ), "Rules are inconsistent with the current managed program."

        assert is_sublist(
            input_facts, program.facts
        ), "Facts are inconsistent with the current managed program."

        # if sizes of ruls or facts are less than the current managed program, create a new program by projecting the current managed program
        if len(rules) < len(program.rules) or len(input_facts) < len(program.facts):
            program = self.mgr.create_subprogram_copy(rules, input_facts)

        meta_output_facts = self._transform_exec_meta_program(program)

        # divide output tuples by assignments of symbolic constants and sort them by assignment
        assignment_outputs = {
            k: v for k, v in sorted(self._divide_output(meta_output_facts).items())
        }

        constraints = defaultdict(list)

        # compute constraints under each assignment of symbolic constants
        for symbol_value_assigns, output_facts in assignment_outputs.items():
            constraints_for_outputs = self._preprocess_and_compute_constraints(
                program,
                symbol_value_assigns,
                output_facts,
                interested_output_facts,
            )

            if constraints_for_outputs:
                for output_fact, condition in constraints_for_outputs.items():
                    constraints[output_fact].append(condition)

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
        output_facts: Set[Rule],
        interested_facts: Set[Rule],
    ):
        """
        Get the target outputs. If interested_facts is None, return the outputs. Otherwise, return the outputs that match the interested_facts.
        """

        if not interested_facts:
            return output_facts

        target_outputs = set()

        if interested_facts:
            for output_fact in output_facts:
                for intrst_fact in interested_facts:
                    # check if the fact matches the target fact by ignoring the internal keywords of symbolic constants
                    is_match, _ = self._get_matched_symbolic_pairs(
                        output_fact, intrst_fact
                    )
                    if is_match:
                        target_outputs.add(output_fact)
                        break

        return target_outputs

    def _update_constraints_with_intrst_outputs(
        self, interested_facts: Set[Rule], constraints: Dict[Rule, OutputCondition]
    ):
        """
        Match the concrete interesting outputs with the symbolic facts in the constraints, and update the constraints.
        """

        if not interested_facts:
            return constraints

        updated_constraints = {}

        for fact, condition in constraints.items():
            for intrst_fact in interested_facts:
                # check if the fact matches the target fact by ignoring the internal keywords of symbolic constants
                is_match, matched_symbolic_pairs = self._get_matched_symbolic_pairs(
                    fact, intrst_fact
                )
                if matched_symbolic_pairs:
                    # concretise the fact with the matched values to the symbols
                    symbol_value_map = dict(matched_symbolic_pairs)

                    new_sub_conditions = [
                        AtomicCondition(
                            [
                                (symbol, symbol_value_map.get(symbol, value))
                                for symbol, value in sub_condition.symbolic_assigns
                            ],
                            sub_condition.dep_facts,
                        )
                        for sub_condition in condition.sub_conditions
                    ]

                    new_condition = OutputCondition(new_sub_conditions)

                    concrete_fact = Rule(
                        Literal(
                            fact.head.name,
                            [symbol_value_map.get(arg, arg) for arg in fact.head.args],
                            True,
                        ),
                        [],
                    )
                    updated_constraints[concrete_fact] = new_condition
                else:
                    updated_constraints[fact] = condition

        return updated_constraints

    def _preprocess_and_compute_constraints(
        self,
        program: Program,
        symbol_value_assigns: Tuple[Any, ...],
        output_facts: List[Rule],
        interested_out_facts: Optional[Set[Rule]] = None,
    ):
        """Compute constraints under given assigned symbolic values."""

        # get target outputs NOTE: compute constraints for each target output. Do not repeat the computation for the same target output, thus use set.
        output_facts_set = frozenset(output_facts)

        target_outputs = self._get_target_outputs(
            output_facts_set, interested_out_facts
        )

        if not target_outputs:
            return None

        # map symbols to the assigned values
        symbol_value_map = dict(symbol_value_assigns)

        # Add non-symbolic sign facts to the program. The symbolic sign facts
        # will be processed by the delta debugging algorithm
        non_symsign_facts, symsign_facts = self._split_symsign_nonsymsign_facts(
            program.facts, self.mgr.symbolic_sign_facts
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
        added_concretised_facts_with_symbols = {
            **added_concrete_non_symsign_fact_dict,
            **added_concrete_symsign_fact_dict,
        }

        # update program with the concretised non-symbolic sign facts
        updated_program = self.mgr.create_subprogram_copy(
            program.rules, concrete_non_symsign_facts, skip_fact_check=True
        )

        # compute the constraints
        constraints_for_outputs = self._compute_constraints(
            updated_program,
            concrete_symsign_facts,
            symbol_value_map,
            added_concretised_facts_with_symbols,
            target_outputs,
        )

        # add extra equiv constraints to make the meta outputs to align with interested facts
        constraints_for_outputs = self._update_constraints_with_intrst_outputs(
            interested_out_facts, constraints_for_outputs
        )
        return constraints_for_outputs

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

        transformed_program = self.trf.transform_program(program)
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
        symbol_concretised_values: Dict[SymbolicNumber | SymbolicString, int | str],
        added_concretised_facts_with_symbols: Dict[
            Rule, List[SymbolicNumber | SymbolicString]
        ],
        target_outputs: Set[Rule],
    ) -> Dict[Rule, OutputCondition]:
        """
        Compute constraints for target outputs.

        Parameters:
        program (Program): ...
        facts_to_check (List[Rule]): ...
        symbol_concretised_values (Dict[SymbolicNumber | SymbolicString, int | str]): ...
        added_concretised_facts_with_symbols (Dict[
            Rule, List[SymbolicNumber | SymbolicString]
        ]): ...
        target_outputs (Set[Rule]): ...

        Returns:
        Dict[Rule, OutputCondition]: A dictionary mapping target outputs to their respective constraints.
        """

        # compute the list of dependent facts for target outputs, where each dependent facts list in the list can generate the target outputs
        dependent_facts_list = ddmin_all_monotonic(
            self._test_function(target_outputs, program), facts_to_check
        )

        # constraints for target outputs
        constraints = defaultdict(list)

        # search the relevent facts for target outputs one by one
        for tar_oup, dependent_facts in product(target_outputs, dependent_facts_list):
            new_dep_facts_list = ddmin_all_monotonic(
                self._test_function([tar_oup], program), dependent_facts
            )
            for new_dep_facts in new_dep_facts_list:
                # get all the symbols used to concretise the dependent facts
                symbols = set(
                    chain.from_iterable(
                        added_concretised_facts_with_symbols[fact]
                        for fact in program.facts  # NOTE: should check all facts in current program
                        if fact in added_concretised_facts_with_symbols
                    )
                )
                # symbol assignment constraints
                sym_assignment_constraints = [
                    (symbol, symbol_concretised_values[symbol]) for symbol in symbols
                ]
                constraints[tar_oup].append(
                    AtomicCondition(sym_assignment_constraints, new_dep_facts)
                )

        encap_constraints = {
            tar_oup: OutputCondition(sub_conditions)
            for tar_oup, sub_conditions in constraints.items()
        }

        return encap_constraints

    def _test_function(self, targets, program):
        """Returns a function that tests if the targets are in the output of the datalog program."""
        return lambda facts_to_check: self._exists_target(
            facts_to_check, targets, program
        )

    def _divide_output(
        self, output_facts: List[Rule]
    ) -> Dict[Tuple[Any, ...], List[Rule]]:
        """
        Divides output tuples by assignments of symbolic constants.

        :param output_facts: A list of output facts to process.
        :return: A dictionary mapping assigned values to simplified output facts.
        """
        assignment_outputs = defaultdict(list)
        symbolic_constants = self.trf.symbolic_constants
        symbol_num = len(symbolic_constants)

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
            simplified_oup_fact = Rule(
                Literal(output_fact.head.name, output_args, True), []
            )

            # map symbols to the assigned values
            symbol_value_tuple = self._create_symbol_value_tuple(
                symbolic_constants, assigned_values
            )

            assignment_outputs[symbol_value_tuple].append(simplified_oup_fact)

        return assignment_outputs

    def _create_symbol_value_tuple(self, symbolic_constants, assigned_values):
        """Create a symbol value tuple from the symbolic constants and assigned values."""
        assert len(symbolic_constants) == len(assigned_values), "Mismatched lengths"

        symbol_value_tuple = tuple(
            SymbolValueAssignment(symbol, assigned_values[i])
            for i, symbol in enumerate(symbolic_constants)
        )
        return symbol_value_tuple

    def _concretise_facts_with_symbols(
        self, input_facts: List[Rule], symbol_concretised_values: Dict[Any, Any]
    ) -> Tuple[List[Rule], Dict[Rule, Set[Any]]]:
        """Concretise the input facts with the assigned values to the symbols and get the associated symbols."""

        all_concretised_facts = []
        concretised_facts_with_symbols = {}
        symbol_keys = set(symbol_concretised_values.keys())

        for raw_fact in input_facts:
            concretised_args = [
                symbol_concretised_values.get(arg, arg) for arg in raw_fact.head.args
            ]
            concretised_fact = Rule(
                Literal(raw_fact.head.name, concretised_args, True), []
            )

            symbols_in_fact = {arg for arg in raw_fact.head.args if arg in symbol_keys}
            if symbols_in_fact:
                concretised_facts_with_symbols[concretised_fact] = symbols_in_fact

            all_concretised_facts.append(concretised_fact)

        return all_concretised_facts, concretised_facts_with_symbols

    def _split_symsign_nonsymsign_facts(self, program_facts, symbolic_sign_facts_list):
        # count occurrences of each fact
        program_facts_counter = Counter(program_facts)
        symbolic_sign_facts_counter = Counter(symbolic_sign_facts_list)

        non_symsign_facts = []
        symsign_facts = []

        # process each fact in program_facts
        for fact, count in program_facts_counter.items():
            # determine the count of this fact in symsign_facts and non_symsign_facts
            min_count = min(count, symbolic_sign_facts_counter[fact])
            symsign_facts.extend([fact] * min_count)
            non_symsign_facts.extend([fact] * (count - min_count))

        return non_symsign_facts, symsign_facts
