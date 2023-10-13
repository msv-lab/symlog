from symlog.environment import Environment
from symlog.souffle import NUM, pprint
from symlog.utils import check_equality


def test_transform():
    program_str = """
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
call("open", 1, "x").
call("close", 4, "x").
final(5).
flow(1, 2).
flow(2, 3).
flow(3, 4).
flow(4, 5).
label(1).
label(2).
label(3).
label(4).
label(5).
variable("x").
"""
    with Environment() as env:
        parser = env.parser
        transformer = env.transformer
        manager = env.program_manager

        SymbolicConstant = manager.SymbolicConstant
        Fact = manager.Fact

        final_fact = Fact("final", [SymbolicConstant("F", NUM)])

        program = parser.parse(program_str)
        transformed = transformer.transform_program(program, [final_fact])
        result = pprint(transformed)

        answer = """
.decl reach_no_call(v0:number, v1:number, v2:symbol, v3:number)
.decl call(v0:symbol, v1:number, v2:symbol)
.decl final(v0:number, v1:number)
.decl flow(v0:number, v1:number)
.decl correct_usage(v0:number, v1:number)
.decl incorrect_usage(v0:number, v1:number)
.decl label(v0:number)
.decl variable(v0:symbol)
.decl symlog_domain_9223372036854775806(v0:number)
.input final
.input call
.input flow
.input label
.input variable
.output correct_usage
correct_usage(L, symlog_binding_9223372036854775806) :- call("open", L, _), !incorrect_usage(L, symlog_binding_9223372036854775806), label(L), symlog_domain_9223372036854775806(symlog_binding_9223372036854775806).
incorrect_usage(L, symlog_binding_9223372036854775806) :- call("open", L, V), flow(L, L1), final(F, symlog_binding_9223372036854775806), reach_no_call(L1, F, V, symlog_binding_9223372036854775806), symlog_domain_9223372036854775806(symlog_binding_9223372036854775806).
reach_no_call(X, X, V, symlog_binding_9223372036854775806) :- label(X), !call("close", X, V), variable(V), symlog_domain_9223372036854775806(symlog_binding_9223372036854775806).
reach_no_call(X, Y, V, symlog_binding_9223372036854775806) :- !call("close", X, V), flow(X, Z), reach_no_call(Z, Y, V, symlog_binding_9223372036854775806), symlog_domain_9223372036854775806(symlog_binding_9223372036854775806).
call("open", 1, "x").
call("close", 4, "x").
final(5, symlog_binding_9223372036854775806) :- symlog_domain_9223372036854775806(symlog_binding_9223372036854775806).
flow(1, 2).
flow(2, 3).
flow(3, 4).
flow(4, 5).
label(1).
label(2).
label(3).
label(4).
label(5).
variable("x").
final(symlog_binding_9223372036854775806, symlog_binding_9223372036854775806) :- symlog_domain_9223372036854775806(symlog_binding_9223372036854775806).
symlog_domain_9223372036854775806(1).
symlog_domain_9223372036854775806(2).
symlog_domain_9223372036854775806(3).
symlog_domain_9223372036854775806(4).
symlog_domain_9223372036854775806(5).
symlog_domain_9223372036854775806(-9223372036854775806).
"""
        assert check_equality(result, answer)


if __name__ == "__main__":
    test_transform()
