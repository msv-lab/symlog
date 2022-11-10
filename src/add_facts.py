import common
import utils


def get_symbolic_facts(declarations, k):
    """
    Create `k` symbolic facts for each edb of passed `declarations`, where `declarations` is a sub dictionary of all declarations.
    """

    facts = dict()
    # TODO: types may be useful in future, so they are left here.
    for (edb, types) in declarations.items():
        values = list()
        for _ in range(k):
            values.append(common.ALPHA + str(utils.get_id()))
        facts[edb] = values

    return facts
