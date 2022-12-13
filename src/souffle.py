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

#TODO: add support for ?type
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
        if rule.body:
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
    test_program = """	

.decl Primitive(type: symbol)
Primitive("boolean").
Primitive("short").
Primitive("int").
Primitive("long").
Primitive("float").
Primitive("double").
Primitive("char").
Primitive("byte").


.decl InstructionLine(m: symbol, i: number, l: number, f: symbol)
.input InstructionLine

.decl VarPointsTo(hctx: symbol, a: symbol, ctx: symbol, v: symbol)
.input VarPointsTo

.decl CallGraphEdge(ctx: symbol, ins: symbol, hctx: symbol, sig: symbol)
.input CallGraphEdge

.decl Reachable(m: symbol)
.input Reachable

.decl SpecialMethodInvocation(instruction:symbol, i: number, sig: symbol, base:symbol, m: symbol)
.input SpecialMethodInvocation


.decl LoadArrayIndex(ins: symbol, i: number, to: symbol, base: symbol, m: symbol)
.input LoadArrayIndex

.decl StoreArrayIndex(ins: symbol, i: number, from: symbol, base: symbol, m: symbol)
.input StoreArrayIndex

.decl StoreInstanceField(ins: symbol, i: number, from: symbol, base: symbol, sig: symbol, m: symbol)
.input StoreInstanceField

.decl LoadInstanceField(ins: symbol, i: number, to: symbol, base: symbol, sig: symbol, m: symbol)
.input LoadInstanceField

.decl VirtualMethodInvocation(ins: symbol, i: number, sig: symbol,  base: symbol, m: symbol)
.input VirtualMethodInvocation

.decl ThrowNull(ins: symbol, i: number, m: symbol)
.input ThrowNull

.decl LoadStaticField(ins: symbol, i: number, to: symbol, sig: symbol, m: symbol)
.input LoadStaticField

.decl StoreStaticField(ins: symbol, i: number, from: symbol, sig: symbol, m: symbol)
.input StoreStaticField

.decl AssignCastNull(ins: symbol, i: number, to: symbol, t: symbol, m: symbol)
.input AssignCastNull

.decl AssignUnop(ins: symbol, i: number, to: symbol, m: symbol)
.input AssignUnop

.decl AssignBinop(ins: symbol, i: number, to: symbol, m: symbol)
.input AssignBinop

.decl AssignOperFrom(ins: symbol, from: symbol)
.input AssignOperFrom

.decl Var_Type(var: symbol, type: symbol)
.input Var_Type

.decl EnterMonitor(ins: symbol, i: number, to: symbol, m: symbol)
.input EnterMonitor

.decl ExitMonitor(ins: symbol, i: number, to: symbol, m: symbol)
.input ExitMonitor


.decl VarPointsToNull(v: symbol)

.decl NullAt(m: symbol, i: number, type: symbol)

.decl ReachableNullAt(m: symbol, i: number, type: symbol)

.decl ReachableNullAtLine(m: symbol, i: number, f: symbol, l: number, type: symbol)
.output ReachableNullAtLine

VarPointsToNull(var) :- VarPointsTo(_, alloc, _, var),
						alloc = "<<null pseudo heap>>".

VarPointsToNull(var) :- AssignCastNull(_,_,var,_,_).

NullAt(meth, index, "Throw NullPointerException") :-
CallGraphEdge(_, a, _, b),
contains("java.lang.NullPointerException", a),
SpecialMethodInvocation(a, index, b, _, meth).


NullAt(meth, index, "Load Array number") :-
VarPointsToNull(var),
LoadArrayIndex(_, index, _, var, meth).

NullAt(meth, index, "Load Array number") :-
!VarPointsTo(_,_,_,var),
LoadArrayIndex(_, index, _, var, meth).


NullAt(meth, index, "Store Array number") :-
VarPointsToNull(var),
StoreArrayIndex(_, index, _, var, meth).

NullAt(meth, index, "Store Array number") :-
!VarPointsTo(_,_,_,var),
StoreArrayIndex(_, index, _, var, meth).


NullAt(meth, index, "Store Instance Field") :-
VarPointsToNull(var),
StoreInstanceField(_, index, _, var, _, meth),
!StoreArrayIndex(_, _, _, var, meth).

NullAt(meth, index, "Store Instance Field") :-
!VarPointsTo(_,_,_,var),
StoreInstanceField(_, index, _, var, _, meth),
!StoreArrayIndex(_, _, _, var, meth).


NullAt(meth, index, "Load Instance Field") :-
VarPointsToNull(var),
LoadInstanceField(_, index, _, var, _, meth),
!LoadArrayIndex(_, _, _, var, meth).

NullAt(meth, index, "Load Instance Field") :-
!VarPointsTo(_,_,_,var),
LoadInstanceField(_, index, _, var, _, meth),
!LoadArrayIndex(_, _, _, var, meth).



NullAt(meth, index, "Virtual symbol Invocation") :-
VarPointsToNull(var),
VirtualMethodInvocation(_, index, _, var, meth).

NullAt(meth, index, "Virtual symbol Invocation") :-
!VarPointsTo(_,_,_,var),
VirtualMethodInvocation(_, index, _, var, meth).

NullAt(meth, index, "Special symbol Invocation") :-
VarPointsToNull(var),
SpecialMethodInvocation(_, index, _, var, meth).

NullAt(meth, index, "Special symbol Invocation") :-
!VarPointsTo(_,_,_,var),
SpecialMethodInvocation(_, index, _, var, meth).


NullAt(meth, index, "Unary Operator") :-
VarPointsToNull(var),
AssignUnop(ins, index, _, meth),
AssignOperFrom(ins, var).

NullAt(meth, index, "Unary Operator") :-
!VarPointsTo(_,_,_,var),
AssignUnop(ins, index, _, meth),
AssignOperFrom(ins, var),
Var_Type(var, type),
!Primitive(type).

NullAt(meth, index, "Binary Operator") :-
VarPointsToNull(var),
AssignBinop(ins, index, _, meth),
AssignOperFrom(ins, var).

NullAt(meth, index, "Binary Operator") :-
!VarPointsTo(_,_,_,var),
AssignBinop(ins, index, _, meth),
AssignOperFrom(ins, var),
Var_Type(var, type),
!Primitive(type).

NullAt(meth, index, "Throw Null") :-
ThrowNull(_, index, meth).

NullAt(meth, index, "Enter Monitor (Synchronized)") :-
VarPointsToNull(var),
EnterMonitor(_, index, var, meth).

NullAt(meth, index, "Enter Monitor (Synchronized)") :-
!VarPointsTo(_,_,_,var),
Var_Type(var, type),
!Primitive(type),
EnterMonitor(_, index, var, meth).

ReachableNullAt(meth, index, type) :- NullAt(meth, index, type), Reachable(meth).

ReachableNullAtLine(meth, index, file, line, type) :- 
ReachableNullAt(meth, index, type), 
InstructionLine(meth, index, line, file).


    """	
    print(pprint(parse(test_program)))