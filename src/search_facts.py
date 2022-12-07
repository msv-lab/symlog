from souffle import Program, Fact, Relation, Rule, Literal, run_program, collect
from typing import List, Dict, Set, Any
from transform_to_meta_program import transform_to_meta_program, transform_for_recording_facts


def search(p: Program) -> List[Literal]:
    """Search for facts that cause some tuples to be derived via delta-debugging."""

    # extract original facts from the transformed meta program
    fact_names = list(map(lambda x: x.head.name, collect(
                        p, lambda x: isinstance(x, Rule) and not x.body)))
    # collect fact heads which are no longer 'facts' after transform_into_meta_program
    fact_heads = [fact.head for fact in collect(transformed, lambda x: isinstance(
        x, Rule) and x.head.name in fact_names and x.body)]

    # delta debugging
    n = 2
    
    transformed = transform_for_recording_facts(p, n, fact_heads)

    
    

    # run program

    
