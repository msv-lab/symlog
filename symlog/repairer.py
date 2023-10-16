from symlog.souffle import Rule
from symlog.symbolic_executor import symex
from typing import Set, List
from z3 import Solver, sat, Not
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def repair(
    rules: List[Rule],
    facts: List[Rule],
    wanted_out_facts: Set[Rule],
    unwanted_out_facts: Set[Rule],
):
    try:
        constraints_for_wanted = symex(rules, facts, wanted_out_facts)
        constraints_for_unwanted = symex(rules, facts, unwanted_out_facts)
    except Exception as e:
        logging.error(f"Failed to generate constraints: {e}")
        return None

    solver = Solver()

    for constraint_dict, negate in [
        (constraints_for_wanted, False),
        (constraints_for_unwanted, True),
    ]:
        for _, out_condition in constraint_dict.items():
            solver.add(Not(out_condition.to_z3()) if negate else out_condition.to_z3())

    logging.info("Searching raw patches...")
    if solver.check() == sat:
        logging.info("Found raw patches.")
        model = solver.model()
        return model
    else:
        logging.error("Failed to solve constraints.")
        return None
