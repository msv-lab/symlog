import common
import utils


def get_symbolic_facts(declarations, k):
    """
    Create `k` symbolic facts for each edb of passed `declarations`, where `declarations` is a sub dictionary of all declarations.
    """

    facts = {predicate: [f"{common.ALPHA}{utils.get_id()}" for _ in range(k)] for (predicate, _) in declarations.items()}

    return facts
