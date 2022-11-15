from src import souffle_parser
from src import souffle
from src import add_facts
from tempfile import TemporaryDirectory
from src import utils


program_text = """
.decl reach_no_call(from:number, to:number, v:symbol)
.decl call(f:symbol, node:number, v:symbol)
.decl final(n:number)
.decl flow(x:number, y:number)
.decl correct_usage(n:number)
.decl incorrect_usage(n:number)        
.decl label(l:number)
.decl variable(v:symbol)        
.input final
.input call    
.input flow
.input label     
.input variable
.output correct_usage

correct_usage(L) :-
call("open", L, _),
! incorrect_usage(L),
label(L).
incorrect_usage(L) :-
call("open", L, V),
flow(L, L1),
final(F),
reach_no_call(L1, F, V).

reach_no_call(X, X, V) :-
label(X),
! call("close", X, V),
variable(V).

reach_no_call(X, Y, V) :-
! call("close", X, V),
flow(X, Z),
reach_no_call(Z, Y, V).
"""

relations = {
    "call": [("open", 1, "x"), ("close", 4, "x")],
    "final": [(5,)],
    "flow": [(1, 2), (2, 3), (3, 4), (4, 5)],
    "label": [(1,), (2,), (3,), (4,), (5,)],
    "variable": [("x",)]
}


def test_parser(program_text):
    program = souffle_parser.parse(program_text)
    print(program)


def test_run_program(program_text, relations):
    program = souffle_parser.parse(program_text)
    result = souffle.run_program(program, relations)
    print(result)


def test_add_EDB_rules(program_text, relations, k):
    program = souffle_parser.parse(program_text)

    with TemporaryDirectory() as input_directory:
        utils.write_relations(input_directory, relations)

        EDB_rules = add_facts.get_EDB_rules(program.declarations, input_directory, k)
        print(EDB_rules)


if __name__ == "__main__":
    # test_parser(program_text)
    # test_run_program(program_text, relations)
    test_add_EDB_rules(program_text, relations, 1)