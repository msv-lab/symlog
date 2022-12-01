from souffle import Program, Fact, Relation, Rule, Literal, run_program
from typing import List, Dict, Set, Any
from transform_to_meta_program import transform_to_meta_program, transform_for_recording_facts


def search(p: Program) -> List[Literal]:
    """Search for facts that cause some tuples to be derived."""

    transformed = transform_for_recording_facts(p)

    # extract facts
    
