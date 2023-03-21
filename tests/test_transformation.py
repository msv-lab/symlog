from symlog.main import Symlog
from symlog.interface import SymConstant, Literal
import symlog.common as common
from symlog.souffle import pprint
from symlog.utils import read_file


def test_transform1():
    symlog = Symlog('tests/data/programs/program1.dl')
    
    # create symbolic facts
    final = Literal('final', True, [SymConstant(common.SOUFFLE_NUMBER)])
    sym_facts = [final]
    symlog.input_facts = symlog.input_facts + sym_facts
    
    trans_p_list = sorted(pprint(symlog.transform()).split('\n'))
    ground_p_list = sorted(read_file('tests/data/programs/program1_trans.dl').split('\n'))
    assert trans_p_list == ground_p_list


def test_transform2():
    symlog = Symlog('tests/data/programs/program2.dl')
    
    # create symbolic facts
    succ = Literal('succ', True, [SymConstant(common.SOUFFLE_SYMBOL), SymConstant(common.SOUFFLE_SYMBOL)])
    sym_facts = [succ]
    symlog.input_facts = symlog.input_facts + sym_facts

    trans_p_list = sorted(pprint(symlog.transform()).split('\n'))
    ground_p_list = sorted(read_file('tests/data/programs/program2_trans.dl').split('\n'))
    assert trans_p_list == ground_p_list


def test_transform3():
    symlog = Symlog('tests/data/programs/program3.dl')
    
    # create symbolic facts
    new = Literal('new', True, [SymConstant(common.SOUFFLE_SYMBOL), SymConstant(common.SOUFFLE_SYMBOL)])

    sym_facts = [new]
    symlog.input_facts = symlog.input_facts + sym_facts
    
    trans_p_list =sorted(pprint(symlog.transform()).split('\n'))
    ground_p_list = sorted(read_file('tests/data/programs/program3_trans.dl').split('\n'))
    assert trans_p_list == ground_p_list 


def test_transform4():
    symlog = Symlog('tests/data/programs/program4.dl', 'tests/data/database/chart-4')

    # create symbolic facts
    operator_at = Literal('OperatorAt', True, [SymConstant(common.SOUFFLE_SYMBOL), SymConstant(common.SOUFFLE_SYMBOL)])
    if_var = Literal('If_Var', True, [SymConstant(common.SOUFFLE_SYMBOL), SymConstant(common.SOUFFLE_SYMBOL), SymConstant(common.SOUFFLE_SYMBOL)])
    if_constant = Literal('If_Constant', True, [SymConstant(common.SOUFFLE_SYMBOL), SymConstant(common.SOUFFLE_SYMBOL), SymConstant(common.SOUFFLE_SYMBOL)])
    jump_target = Literal('JumpTarget', True, [SymConstant(common.SOUFFLE_SYMBOL), SymConstant(common.SOUFFLE_SYMBOL)])

    sym_facts = [operator_at, if_var, if_constant, jump_target]
    symlog.input_facts = symlog.input_facts + sym_facts

    trans_p_list = sorted(pprint(symlog.transform()).split('\n'))
    ground_p_list = sorted(read_file('tests/data/programs/program4_trans.dl').split('\n'))
    assert trans_p_list == ground_p_list

if '__main__' == __name__:
    test_transform1()