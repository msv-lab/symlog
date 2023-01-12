from typing import List, Callable, List
import functools
import copy
import common
import utils


# predicate name -> list of tuples
PredTuplesDict = common.PredTuplesDict


def remove_multiple_assignments(args_list, related_facts, base_arg_idx, target_arg_idx):
    ret_args_list = copy.deepcopy(args_list)

    for args in args_list:
        if_arg = args[base_arg_idx]
        val = args[target_arg_idx]
        for tmp_args in related_facts:
            if tmp_args[base_arg_idx] == if_arg and tmp_args[target_arg_idx] != val and not common.SYMBOLIC_CONSTANT_PREFIX in tmp_args[target_arg_idx]:
                if tmp_args in ret_args_list:
                    ret_args_list.remove(tmp_args)
                if args in ret_args_list:
                    ret_args_list.remove(args)

    return ret_args_list


def JumpTarget_checker(pred: str, args_list: List[List[str]], database: PredTuplesDict) -> List[List[str]]:
    if pred != 'JumpTarget':
        return args_list

    # FIXME: hack for getting related facts
    related_facts = database.get(pred.replace('_', ''), [])
    remove_multiple_assignments(args_list, related_facts, 1, 0)    
    args_list = remove_multiple_assignments(args_list)

    return args_list

def OperatorAt_checker(pred: str, args_list: List[List[str]], database: PredTuplesDict) -> List[List[str]]:
    if pred != 'OperatorAt':
        return args_list

    # FIXME: hack for getting related facts
    related_facts = database.get(pred.replace('_', ''), [])
    args_list = remove_multiple_assignments(args_list, related_facts, 0, 1)

    return args_list


def If_checker(pred: str, args_list: List[List[str]], database: PredTuplesDict) -> List[List[str]]:
    if pred not in ('If_Var', 'If_Constant'):
        return args_list

    # FIXME: hack for getting related facts
    related_facts = database.get(pred.replace('_', ''), [])

    def is_if(args):
        return 'if' in args[0] or common.SYMBOLIC_CONSTANT_PREFIX in args[0]

    args_list = [args for args in args_list if is_if(args)]
    args_list = remove_multiple_assignments(args_list, related_facts, 0, 2)
    
    return args_list


def if_combo_checker(facts: PredTuplesDict, database: PredTuplesDict=None) -> PredTuplesDict:

    if not utils.is_sublist(['If_Var', 'If_Constant', 'OperatorAt', 'JumpTarget'], list(facts.keys())):
        return facts

    if_var_list = facts.get('If_Var', [])
    if_constant_list = facts.get('If_Constant', [])
    operator_at_list = facts.get('OperatorAt', [])
    jump_target_list = facts.get('JumpTarget', [])

    shared_args = set([args[0] for args in if_var_list]).intersection(set([args[0] for args in operator_at_list])).intersection(set([args[0] for args in if_constant_list])).intersection(set([args[1] for args in jump_target_list]))

    new_if_var_list = list(filter(lambda args: args[0] in shared_args, if_var_list))
    new_if_constant_list = list(filter(lambda args: args[0] in shared_args, if_constant_list))
    new_operator_at_list = list(filter(lambda args: args[0] in shared_args, operator_at_list))
    new_jump_target_list = list(filter(lambda args: args[1] in shared_args, jump_target_list))

    facts['If_Var'] = new_if_var_list
    facts['If_Constant'] = new_if_constant_list
    facts['OperatorAt'] = new_operator_at_list
    facts['JumpTarget'] = new_jump_target_list

    return facts


def semantics_filter(facts: PredTuplesDict, database: PredTuplesDict, pred_checkers: List[Callable], facts_checker: Callable=None):
    '''filter out queries that are not semantically correct'''
    result = {}
    for pred, args_list in facts.items():
        result[pred] = functools.reduce(lambda args_list, pred_checker: pred_checker(pred, args_list, database), pred_checkers, args_list)

    if facts_checker:
        result = facts_checker(result)
    return result