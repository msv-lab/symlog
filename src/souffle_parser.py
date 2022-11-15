import src.common as common
from lark import Lark, Transformer, v_args


souffle_grammar = """
    start: (declaration | rule | directive | output | input)*
    directive: "#" NAME ESCAPED_STRING
    declaration: ".decl" NAME "(" [typed_var ("," typed_var)*] ")"
    output: ".output" NAME
    input: ".input" NAME
    typed_var: NAME ":" NAME
    ?arg: NAME -> var
        | value
    ?value: string
          | SIGNED_NUMBER -> number
    string : ESCAPED_STRING
    rule: literal [ ":-" body] "."
    ?literal: NAME "(" [arg ("," arg)*] ")" -> atom
            | "!" NAME "(" [arg ("," arg)*] ")"  -> negated_atom
            | arg "=" arg -> unification
            | arg "!=" arg -> nagated_unification
    body: literal ("," literal)*
    %import common.CNAME -> NAME
    %import common.ESCAPED_STRING
    %import common.SIGNED_NUMBER
    %import common.WS
    %ignore WS
"""


@v_args(inline=True)
class ASTConstructor(Transformer):
    def NAME(self, v):
        return str(v)

    def __init__(self):
        self.program = common.Program({}, [], [], [])

    def number(self, n):
        return common.Number(int(n))
        
    def string(self, s):
        return common.String(s[1:-1])

    def var(self, v):
        return common.Variable(v)
    
    def directive(self, d, v):
        raise NotImplementedError("directives are not supported")

    def declaration(self, name, *args):
        self.program.declarations[name] = [x for _, x in args]

    def output(self, name):
        self.program.outputs.append(name)

    def input(self, name):
        self.program.inputs.append(name)

    def typed_var(self, v, t):
        return (v, t)

    def atom(self, name, *args):
        return common.Literal(name, args, True)

    def negated_atom(self, name, *args):
        return common.Literal(name, args, False)

    def unification(self, left, right):
        return common.Unification(left, right, True)

    def negated_unification(self, left, right):
        return common.Unification(left, right, False)
    
    def body(self, *args):
        return args

    def rule(self, head, body):
        self.program.rules.append(common.Rule(head, body))
    
    def start(self, *_):
        return self.program

    
souffle_parser = Lark(souffle_grammar)

def parse(s):
    return ASTConstructor().transform(souffle_parser.parse(s))

if __name__ == "__main__":

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

    program = parse(program_text)

    print(program)