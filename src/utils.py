import itertools


def remove_false_dict_values(d):
    return {k: v for k, v in d.items() if v}


def flatten_dict(d):
    return {k: list(itertools.chain(*v)) for k, v in d.items()}