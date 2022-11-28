from tempfile import TemporaryDirectory, NamedTemporaryFile
from pathlib import Path
from subprocess import run, DEVNULL, CalledProcessError
import itertools
import csv
from collections import namedtuple
from typing import Union

from lark import Lark, Transformer, v_args

# declarations: name -> argument types
# output: list of names
# rules: list of rules
Program = namedtuple('Program', ['declarations', 'inputs', 'outputs', 'rules'])
Rule = namedtuple('Rule', ['head', 'body'])
Literal = namedtuple('Literal', ['name', 'args', 'positive'])
Unification = namedtuple('Unification', ['left', 'right', 'positive'])
Variable = namedtuple('Variable', ['name'])
String = namedtuple('String', ['value'])
Number = namedtuple('Number', ['value'])
Term = Union[Variable, String, Number]


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
            | arg "!=" arg -> negated_unification
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
        self.program = Program({}, [], [], [])

    def number(self, n):
        return Number(int(n))
        
    def string(self, s):
        return String(s[1:-1])

    def var(self, v):
        return Variable(v)
    
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
        return Literal(name, args, True)

    def negated_atom(self, name, *args):
        return Literal(name, args, False)

    def unification(self, left, right):
        return Unification(left, right, True)

    def negated_unification(self, left, right):
        return Unification(left, right, False)
    
    def body(self, *args):
        return args

    def rule(self, head, body):
        self.program.rules.append(Rule(head, body))
    
    def start(self, *_):
        return self.program


souffle_parser = Lark(souffle_grammar)


def pprint(program):
    def pprint_term(term):
        if isinstance(term, Variable):
            return term.name
        if isinstance(term, String):
            return "\"" + term.value + "\""
        else:
            return str(term.value)

    def pprint_literal(l):
        literal_result = ""
        if not l.positive:
            literal_result += "!"
        args_result = ", ".join([pprint_term(t) for t in l.args])
        literal_result += f"{l.name}({args_result})"
        return literal_result
        
    def pprint_unification(u):
        op = "=" if u.positive else "!="
        return f"{pprint_term(u.left)} {op} {pprint_term(u.right)}"
    
    result = ""

    for (name, types) in program.declarations.items():
        result += f".decl {name}("
        types_results = [f"v{i}:{t}" for i, t in enumerate(types)] 
        result += ", ".join(types_results) + ")\n"

    for name in program.inputs:
        result += f".input {name}\n"

    for name in program.outputs:
        result += f".output {name}\n"
        
    for rule in program.rules:
        result += pprint_literal(rule.head)
        if rule.body:
            result += " :- "
        body_results = []
        for el in rule.body:
            if isinstance(el, Unification):
                body_results.append(pprint_unification(el))
            else:
                body_results.append(pprint_literal(el))
        result += ", ".join(body_results) + ".\n"

    return result


def transform(node, f):

    def transform_inner(node, f):
        if isinstance(node, Variable) or \
           isinstance(node, String) or \
           isinstance(node, Number):
            return transform_term(node, f)
        if isinstance(node, Unification):
            return transform_unification(node, f)
        if isinstance(node, Literal):
            return transform_literal(node, f)
        if isinstance(node, Rule):
            return transform_rule(node, f)
        if isinstance(node, Program):
            return transform_program(node, f)
    
    def transform_term(t, f):
        return f(t)
    
    def transform_unification(u, f):
        return f(Unification(transform_term(u.left, f),
                             transform_term(u.right, f),
                             u.positive))
    
    def transform_literal(l, f):
        return f(Literal(l.name,
                         [transform_term(t, f) for t in l.args],
                         l.positive))

    def transform_rule(rule, f):
        return f(Rule(transform_literal(rule.head, f),
                      [transform_inner(n, f) for n in rule.body] if rule.body else []))

    def transform_program(program, f):
        return f(Program(program.declarations,
                         program.inputs,
                         program.outputs,
                         [transform_rule(r, f) for r in program.rules]))
    
    return transform_inner(node, f)


def collect(node, p):
    result = []

    def collect_inner(node, p):
        if isinstance(node, Variable) or \
           isinstance(node, String) or \
           isinstance(node, Number):
            collect_term(node, p)
        if isinstance(node, Unification):
            collect_unification(node, p)
        if isinstance(node, Literal):
            collect_literal(node, p)
        if isinstance(node, Rule):
            collect_rule(node, p)
        if isinstance(node, Program):
            collect_program(node, p)

    def collect_term(t, p):
        if p(t):
            result.append(t)
    
    def collect_unification(unification, p):
        collect_term(unification.left, p)
        collect_term(unification.right, p)
        if p(unification):
            result.append(unification)
    
    def collect_literal(literal, p):
        for a in literal.args:
            collect_term(a, p)
        if p(literal):
            result.append(literal)

    def collect_rule(rule, p):
        collect_inner(rule.head, p)
        if rule.body:
            for el in rule.body:
                collect_inner(el, p)
        if p(rule):
            result.append(rule)

    def collect_program(program, p):
        for r in program.rules:
            collect_rule(r, p)
        if p(program):
            result.append(program)

    collect_inner(node, p)
    return result


def parse(s):
    return ASTConstructor().transform(souffle_parser.parse(s))


def load_relations(directory):
    """returns mapping from relation name to a list of tuples"""
    relations = dict()
    for file in itertools.chain(Path(directory).glob('*.facts'), Path(directory).glob('*.csv')):
        relation_name = file.stem
        with open(file) as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            relations[relation_name] = list(reader)
    return relations


def write_relations(directory, relations):
    for relation_name, tuples in relations.items():
        file = Path(directory) / (relation_name + '.facts')
        with file.open(mode='w') as file:
            writer = csv.writer(file, delimiter='\t')
            for tuple in tuples:
                writer.writerow(tuple)


def run_program(program, relations):
    with NamedTemporaryFile() as datalog_script:
        datalog_script.write(pprint(program).encode())
        datalog_script.flush()
        with TemporaryDirectory() as input_directory:
            write_relations(input_directory, relations)
            with TemporaryDirectory() as output_directory:
                cmd = [
                    "souffle",
                    "-F", input_directory,
                    "-D", output_directory,
                    datalog_script.name
                ]
                try:
                    run(cmd, check=True, stdout=DEVNULL)#, stderr=DEVNULL)
                except CalledProcessError:
                    print("----- error while solving: ----")
                    print(pprint(program))
                    print("---- on -----------------------")
                    print(relations)
                    exit(1)
                return load_relations(output_directory)


    

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
        "call": [("open", 1, "x"), ("close", 4, "x"), ("_symlog_symbolic_open", 2, "x"), ("_symlog_symbolic_close", 3, "x")],
        "final": [(5,)],
        "flow": [(1, 2), (2, 3), (3, 4), (4, 5)],
        "label": [(1,), (2,), (3,), (4,), (5,)],
        "variable": [("x",)]
    }

    program = parse(program_text)

    transformed = transform(program, lambda n: Variable(f"{n.name}_2") if isinstance(n, Variable) else n)

    print(pprint(transformed))

    result = run_program(transformed, relations)

    print(result)
