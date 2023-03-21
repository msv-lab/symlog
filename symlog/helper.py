from symlog.souffle import parse, collect, Rule, Literal
from symlog.utils import sort_z3_expressions
from symlog.common import BINDING_VARIABLE_PREFIX, SOUFFLE_SYMBOL, SOUFFLE_NUMBER, SOUFFLE_FLOAT, SOUFFLE_UNSIGNED
from collections import defaultdict
import z3
import json


def _extract_sym_var(program):
    # output predicate --> lists of (index, variable name, variable type)
    predicate_sym_info = {
        name: [
            (i, rule.head.args[i].name, program.declarations[name][i])
            for rule in collect(program, lambda x: isinstance(x, Rule) and x.head.name == name)
            for i in range(len(rule.head.args))
            if rule.head.args[i].name.startswith(BINDING_VARIABLE_PREFIX)
        ]
        for name in program.outputs
    }

    return predicate_sym_info


def _map_output_constraints(predicate_sym_info, relations):
    # output tuple --> lists of lists of (variable name, value, variable type)
    output_constraints = defaultdict(list)
    if not predicate_sym_info:
        return output_constraints
    for name, args_list in relations.items():
        if name not in predicate_sym_info:
            continue
        for args in args_list:
            if not predicate_sym_info[name]:
                min_index = len(args)
            else:
                min_index = min([x[0] for x in predicate_sym_info[name]])
            output_tuple = Literal(name, tuple(args[:min_index]), True) 
            constraint_for_oup_tuple = tuple([(var, args[i], type_v) for i, var, type_v in predicate_sym_info[name]])
            output_constraints[output_tuple].append(constraint_for_oup_tuple)

    return output_constraints


def _output_constraints_to_z3(output_constraints):
    # output tuple --> z3 constraints
    output_z3_constraints = defaultdict()
    for output_tuple, constraints in output_constraints.items():
        z3_constraints = []
        for constraint in constraints:
            for var, value, type_v in constraint:
                if type_v == SOUFFLE_SYMBOL:
                    z3_constraints.append(z3.String(var) == value)
                elif type_v == SOUFFLE_NUMBER:
                    z3_constraints.append(z3.Int(var) == value)
                elif type_v == SOUFFLE_FLOAT:
                    z3_constraints.append(z3.Float64(var) == value)
                elif type_v == SOUFFLE_UNSIGNED:
                    z3_constraints.append(z3.BitVec(var, 32) == value)
                else:
                    raise ValueError('Unknown type: {}'.format(type_v))

        output_z3_constraints[output_tuple] = z3.Or(*sort_z3_expressions( z3_constraints)) # sort z3 constraints

    return output_z3_constraints


def format_output(program, output_relations):

    predicate_sym_info = _extract_sym_var(program)
    output_constraints = _map_output_constraints(predicate_sym_info, output_relations)
    z3_output_constraints = _output_constraints_to_z3(output_constraints)

    # sort z3 output constraints
    z3_output_constraints = dict(sorted(z3_output_constraints.items(), key=lambda x: x[0].name))

    return {
        f"{output_tuple.name}({output_tuple.args})": z3_constraint.sexpr() if z3_constraint.sexpr() != "or" else ""
        for output_tuple, z3_constraint in z3_output_constraints.items()
    }
