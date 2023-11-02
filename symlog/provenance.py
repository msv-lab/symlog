from symlog.souffle import Program, pprint, Fact, compile_and_run
from symlog.utils import is_sublist
from symlog.program_builder import update_program

from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile
import json
import re
from typing import List, Set, FrozenSet
from itertools import combinations
from more_itertools import unique_everseen
from collections import namedtuple, defaultdict
import numpy as np


ProgramTargetKey = namedtuple("ProgramTargetKey", ["program", "target"])


def filter_out_excluded_items(source_list, exclusion_list):
    # convert exclusion_list to a set for faster look-up
    exclusion_set = set(exclusion_list)

    # remove elements from source_list that are in exclusion_set
    return [item for item in source_list if item not in exclusion_set]


def combinations_and_complements(lst: list) -> list[tuple[tuple, tuple]]:
    all_combs_and_complements = []

    def get_complement(lst, comb):
        temp = lst - frozenset(comb)
        return tuple(temp)

    for comb in combinations(lst, len(lst) - 1):
        complement = get_complement(lst, comb)
        all_combs_and_complements.append((comb, complement))

    # remove duplicate combinations and complements
    all_combs_and_complements = list(unique_everseen(all_combs_and_complements))

    return all_combs_and_complements


class Provenancer:
    def __init__(self):
        self._provenance_cache_bv = defaultdict(list)
        self._provenance_cache = defaultdict(list)

    def _extract_relation_and_arguments(self, s):
        match = re.match(r"(\w+)\(([^)]+)\)", s)
        if match:
            relation_name = match.group(1)
            args = [
                arg.strip().replace('"', "") for arg in match.group(2).split(",")
            ]  # remove the double quotes
            return relation_name, args
        return None

    def _extract_axioms(self, node):
        """Recursively extract axioms from a proof node."""
        if "axiom" in node:
            return [node["axiom"]]
        elif "children" in node:
            # flatten the list of lists to a single list
            return [
                axiom
                for child in node["children"]
                for axiom in self._extract_axioms(child)
            ]
        return []

    def _provenance(
        self, bare_program: Program, target_fact: Fact, input_facts: List[Fact]
    ) -> FrozenSet[Fact]:
        """Returns the dependent facts of the given fact in the given bare program and input facts."""

        # quick check if the target fact is derivable
        derived_facts = compile_and_run(bare_program, facts=input_facts)

        if target_fact not in derived_facts:
            return []

        program = update_program(bare_program, facts=input_facts)

        dep_facts = self._base_provenance(program, target_fact)

        return dep_facts

    def _escape_invalid_json_chars(self, json_str):
        return json_str.replace("\\;", "\\\\;")

    def _base_provenance(self, program: Program, target_fact: Fact) -> FrozenSet[Fact]:
        """Returns the provenance of the given fact in the given program."""

        try:
            with NamedTemporaryFile() as datalog_script:
                datalog_script.write(pprint(program).encode())
                datalog_script.flush()

                cmd = [
                    "souffle",
                    "-t",
                    "explain",
                    datalog_script.name,
                ]

                try:
                    interactive_process = Popen(
                        cmd,
                        stdin=PIPE,
                        stdout=PIPE,
                        stderr=PIPE,
                    )

                    commands = [
                        f"setdepth {1e9}",  # set a large number
                        "format json",
                        "explain "
                        + "".join(
                            pprint(target_fact).rsplit(".", 1)
                        ).strip(),  # remove the '.' for identifying a fact and \n.
                    ]
                    output, errors = interactive_process.communicate(
                        "\n".join(commands).encode()
                    )

                    if interactive_process.returncode != 0:
                        raise RuntimeError(
                            f"'souffle' command failed with error: {errors.decode()}"
                        )
                except Exception as e:
                    print(f"Error executing external command: {e}")
                    raise

                try:
                    output = self._escape_invalid_json_chars(output.decode())
                    data = json.loads(output)
                except json.JSONDecodeError:
                    print("Error parsing JSON output from Souffle")
                    return None

                assert "proof" in data, "Bug in Souffle?"

                axioms = self._extract_axioms(data["proof"])

                if axioms == ["Tuple not found"]:
                    return None

                # match the axioms to program facts
                axioms_set = set(axioms)
                facts = {f for f in program.facts if str(f).rstrip(".") in axioms_set}

        except IOError as e:
            print(f"File operation error: {e}")
            raise

        return frozenset(facts)

    def _previous_computed_result(
        self, program_target_key: ProgramTargetKey, input_data: Set[Fact]
    ):
        for prev_result in unique_everseen(
            self._provenance_cache[program_target_key], key=tuple
        ):
            if is_sublist(prev_result, input_data):
                return prev_result
        return None

    def monotonic_all(
        self, bare_program: Program, target_output: Fact, input_facts: Set[Fact]
    ) -> list:
        """Final all minimized input facts that can produce the target output"""

        program_target_key = ProgramTargetKey(bare_program, target_output)

        def dfs(current_input_facts):
            results = []

            # try to reuse the minimized input computed previously
            minimized_input = self._previous_computed_result(
                program_target_key, current_input_facts
            )
            # if not, compute the minimal input
            if not minimized_input:
                minimized_input = self._provenance(
                    bare_program, target_output, current_input_facts
                )

            if not minimized_input:
                return results

            results.append(minimized_input)

            if not minimized_input in self._provenance_cache[program_target_key]:
                self._provenance_cache[program_target_key].append(minimized_input)

            # get combinations of the minimized_input
            for comb, complement in combinations_and_complements(minimized_input):
                comb = list(comb)  # convert tuple to list
                new_input = comb + filter_out_excluded_items(
                    current_input_facts, complement
                )

                results.extend(dfs(new_input))

            return results

        # execute dfs and retrieve results
        all_results = dfs(input_facts)

        # deduplicate results
        unique_results = list(unique_everseen(all_results, key=tuple))

        return unique_results
