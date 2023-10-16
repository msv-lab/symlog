from tempfile import TemporaryDirectory, NamedTemporaryFile
from pathlib import Path
from subprocess import run, DEVNULL, CalledProcessError
import itertools
import csv
from collections import namedtuple
import os
import hashlib
from typing import List, Union, Callable, Optional
from lark import Lark, Transformer, v_args, UnexpectedInput, LarkError, UnexpectedEOF
import logging

from symlog.common import (
    SYMBOLIC_CONSTANT_PREFIX,
    BINDING_VARIABLE_PREFIX,
    DOMAIN_PREDICATE_PREFIX,
    SYMLOG_NUM_POOL,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


def namedtuple_with_methods(namedtuple_cls):
    class ExtendedNamedTuple(namedtuple_cls):
        def __repr__(self):
            return pprint(self).replace("\n", "")

        def __str__(self):
            return pprint(self).replace("\n", "")

        def __hash__(self):
            return hash(pprint(self).replace("\n", ""))

    ExtendedNamedTuple.__name__ = (
        namedtuple_cls.__name__
    )  # Set the class name to be the same as the namedtuple
    return ExtendedNamedTuple


# relation_decls: name -> argument types
# output: list of names
# rules: list of rules
Program = namedtuple(
    "Program",
    [
        "declarations",
        "inputs",
        "outputs",
        "rules",
        "facts",
        "symbols",
    ],
)

Variable = namedtuple("Variable", ["name"])
String = namedtuple("String", ["value"])
Number = namedtuple("Number", ["value"])
SymbolicSign = namedtuple("SymbolicSign", ["fact"])
Underscore = namedtuple("UnderScore", [])


class SymbolicString(namedtuple("SymbolicString", ["name"])):
    _next_free_id = 1

    def __new__(cls):
        name = f"{SYMBOLIC_CONSTANT_PREFIX}{cls._next_free_id}"
        instance = super().__new__(cls, name)
        cls._next_free_id += 1
        return instance

    def __deepcopy__(self, memo):
        # ignore memo
        return super().__new__(self.__class__, self.name)

    def __repr__(self) -> str:
        return f"SymbolicString({self.name})"

    def __str__(self) -> str:
        return f"SymbolicString({self.name})"


class SymbolicNumber(namedtuple("SymbolicNumber", ["name"])):
    _next_free_id = 1

    def __new__(cls, name=None):
        name = SYMLOG_NUM_POOL[cls._next_free_id]
        instance = super().__new__(cls, name)
        cls._next_free_id += 1
        return instance

    def __repr__(self) -> str:
        return f"SymbolicNumber({self.name})"

    def __str__(self) -> str:
        return f"SymbolicNumber({self.name})"


SymbolicStringWrapper = namedtuple("SymbolicStringWrapper", ["name", "payload"])
SymbolicNumberWrapper = namedtuple("SymbolicNumberWrapper", ["name", "payload"])
Rule = namedtuple_with_methods(namedtuple("Rule", ["head", "body"]))
Literal = namedtuple_with_methods(namedtuple("Literal", ["name", "args", "positive"]))
Fact = namedtuple_with_methods(namedtuple("Fact", ["head", "body", "symbolic_sign"]))


# types
SYM = "symbol"
NUM = "number"


souffle_grammar = """
    start: (relation_decl | rule | fact | directive | output | input )*
    directive: "#" NAME ESCAPED_STRING
    relation_decl: ".decl" NAME "(" [typed_var ("," typed_var)*] ")"
    output: ".output" NAME
    input: ".input" NAME
    typed_var: NAME ":" NAME
    ?arg: NAME -> var
        | value
    ?value: string
          | SIGNED_NUMBER -> number
    string : ESCAPED_STRING
    rule: literal ":-" body "."
    ?literal: NAME "(" [arg ("," arg)*] ")" -> atom
            | "!" NAME "(" [arg ("," arg)*] ")"  -> negated_atom
    body: literal ("," literal)*
    fact: literal "."
    COMMENT: /\/\/.*/
    %import common.CNAME -> NAME
    %import common.ESCAPED_STRING
    %import common.SIGNED_NUMBER
    %import common.WS
    %ignore WS
    %ignore COMMENT
"""


@v_args(inline=True)
class ASTConstructor(Transformer):
    def NAME(self, v):
        return str(v)

    def __init__(self):
        self.program = Program(
            declarations={},
            inputs=[],
            outputs=[],
            rules=[],
            facts=[],
            symbols=[],
        )

    def number(self, n):
        return Number(int(n))

    def string(self, s):
        return String(s[1:-1])

    def var(self, v):
        return Variable(v)

    def directive(self, d, v):
        raise NotImplementedError("directives are not supported")

    def relation_decl(self, name, *attrs):
        self.program.declarations[name] = [x for _, x in attrs]

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

    def body(self, *args):
        return args

    def rule(self, head, body):
        self.program.rules.append(Rule(head, body))

    def fact(self, head):
        self.program.facts.append(Fact(head, [], False))

    def start(self, *_):
        return self.program


def pprint(node):
    def pprint_inner(node):
        if isinstance(node, Program):
            return pprint_program(node)
        if isinstance(node, Rule):
            return pprint_rule(node)
        if isinstance(node, Literal):
            return pprint_literal(node)
        if isinstance(node, Variable):
            return pprint_term(node)
        if isinstance(node, String):
            return pprint_term(node)
        if isinstance(node, Number):
            return pprint_term(node)
        if isinstance(node, SymbolicNumber):
            return pprint_term(node)
        if isinstance(node, SymbolicString):
            return pprint_term(node)
        if isinstance(node, Fact):
            return pprint_fact(node)
        raise NotImplementedError(f"pprint for {type(node)} is not implemented")

    def pprint_term(term):
        if isinstance(term, Variable):
            return term.name
        elif isinstance(term, String):
            return '"' + term.value.replace('"', "") + '"'
        elif isinstance(term, SymbolicString):
            return '"' + term.name + '"'
        elif isinstance(term, SymbolicNumber):
            return str(term.name)
        elif isinstance(term, Number):
            return str(term.value)
        elif isinstance(term, SymbolicNumberWrapper):
            return term.payload.name
        elif isinstance(term, SymbolicStringWrapper):
            return term.payload.name
        else:
            assert False, f"unknown term {term}. Bug?"

    def pprint_literal(l):
        literal_result = ""
        if not l.positive:
            literal_result += "!"
        args_result = ", ".join([pprint_term(t) for t in l.args])
        literal_result += f"{l.name}({args_result})"
        return literal_result

    def pprint_rule(rule):
        result = ""
        result += pprint_literal(rule.head)

        if rule.body:
            result += " :- "
            body_results = []
            if rule.body:
                for el in rule.body:
                    if isinstance(el, Literal):
                        body_results.append(pprint_literal(el))
                    else:
                        raise ValueError(f"unknown body element {el}")
            result += ", ".join(body_results) + ".\n"
        return result

    def pprint_fact(fact):
        assert not fact.body, "fact body is not empty. Bug?"
        result = ""
        result += pprint_literal(fact.head)
        result += ".\n"
        return result

    def pprint_program(program):
        result = ""

        for name, types in program.declarations.items():
            result += f".decl {name}("
            types_results = [f"v{i}:{t}" for i, t in enumerate(types)]
            result += ", ".join(types_results) + ")\n"

        for name in program.inputs:
            result += f".input {name}\n"

        for name in program.outputs:
            result += f".output {name}\n"

        for rule in program.rules:
            result += pprint_rule(rule)

        for fact in program.facts:
            result += pprint_fact(fact)

        return result

    return pprint_inner(node)


def transform(node, f):
    def transform_inner(node, f):
        if (
            isinstance(node, Variable)
            or isinstance(node, String)
            or isinstance(node, Number)
            or isinstance(node, SymbolicNumber)
            or isinstance(node, SymbolicString)
            or isinstance(node, SymbolicNumberWrapper)
            or isinstance(node, SymbolicStringWrapper)
        ):
            return transform_term(node, f)

        if isinstance(node, Literal):
            return transform_literal(node, f)
        if isinstance(node, Rule):
            return transform_rule(node, f)
        if isinstance(node, Fact):
            return transform_fact(node, f)
        if isinstance(node, Program):
            return transform_program(node, f)

    def transform_term(t, f):
        return f(t)

    def transform_literal(l, f):
        return f(Literal(l.name, [transform_term(t, f) for t in l.args], l.positive))

    def transform_rule(rule, f):
        return f(
            Rule(
                transform_literal(rule.head, f),
                [transform_inner(n, f) for n in rule.body] if rule.body else [],
            )
        )

    def transform_fact(fact, f):
        return f(
            Fact(
                transform_literal(fact.head, f),
                [],
                fact.symbolic_sign,
            )
        )

    def transform_program(program, f):
        return f(
            Program(
                program.declarations,
                program.inputs,
                program.outputs,
                [transform_rule(r, f) for r in program.rules],
                [transform_fact(fact, f) for fact in program.facts],
                program.symbols,
            )
        )

    # re-orgainze the program, since the transform function may convert facts to rules
    tmp_innder = transform_inner(node, f)
    if not isinstance(tmp_innder, Program):
        return tmp_innder

    rules = []
    facts = []
    for fact_rule in tmp_innder.facts + tmp_innder.rules:
        if isinstance(fact_rule, Rule):
            rules.append(fact_rule)
        elif isinstance(fact_rule, Fact):
            facts.append(fact_rule)
        else:
            assert False, f"unknown fact_rule {fact_rule}. Bug?"
    return Program(
        tmp_innder.declarations,
        tmp_innder.inputs,
        tmp_innder.outputs,
        rules,
        facts,
        tmp_innder.symbols,
    )


def collect(node, p):
    result = []

    def collect_inner(node, p):
        if (
            isinstance(node, Variable)
            or isinstance(node, String)
            or isinstance(node, Number)
            or isinstance(node, SymbolicNumber)
            or isinstance(node, SymbolicString)
            or isinstance(node, SymbolicNumberWrapper)
            or isinstance(node, SymbolicStringWrapper)
        ):
            collect_term(node, p)

        if isinstance(node, Literal):
            collect_literal(node, p)
        if isinstance(node, Rule):
            collect_rule(node, p)
        if isinstance(node, Fact):
            collect_fact(node, p)
        if isinstance(node, Program):
            collect_program(node, p)

    def collect_term(t, p):
        if p(t):
            result.append(t)

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

    def collect_fact(fact, p):
        collect_inner(fact.head, p)

        assert not fact.body, "fact body is not empty. Bug?"

        if p(fact):
            result.append(fact)

    def collect_program(program, p):
        for r in program.rules:
            collect_rule(r, p)
        for fact in program.facts:
            collect_fact(fact, p)

        if p(program):
            result.append(program)

    collect_inner(node, p)
    return result


def walk(node, f):
    def walk_inner(node, f):
        if (
            isinstance(node, Variable)
            or isinstance(node, String)
            or isinstance(node, Number)
            or isinstance(node, SymbolicNumber)
            or isinstance(node, SymbolicString)
            or isinstance(node, SymbolicNumberWrapper)
            or isinstance(node, SymbolicStringWrapper)
        ):
            walk_term(node, f)
        if isinstance(node, Literal):
            walk_literal(node, f)
        if isinstance(node, Rule):
            walk_rule(node, f)
        if isinstance(node, Fact):
            walk_fact(node, f)
        if isinstance(node, Program):
            walk_program(node, f)

    def walk_term(t, f):
        f(t)

    def walk_literal(literal, f):
        for a in literal.args:
            walk_term(a, f)
        f(literal)

    def walk_rule(rule, f):
        walk_literal(rule.head, f)
        if rule.body:
            for bl in rule.body:
                walk_inner(bl, f)
        f(rule)

    def walk_fact(fact, f):
        walk_literal(fact.head, f)
        assert not fact.body, "fact body is not empty. Bug?"
        f(fact)

    def walk_program(program, f):
        for r in program.rules:
            walk_rule(r, f)
        for fact in program.facts:
            walk_fact(fact, f)
        f(program)

    walk_inner(node, f)


def user_arg_check(raw_arg: Union[str, int]) -> Union[str, int]:
    if any(
        raw_arg.startswith(prefix)
        for prefix in (
            SYMBOLIC_CONSTANT_PREFIX,
            BINDING_VARIABLE_PREFIX,
            DOMAIN_PREDICATE_PREFIX,
        )
    ):
        raise ValueError(f"conflict with keyword {raw_arg}")
    return raw_arg


def to_symlog_arg(
    raw_arg: Union[str, int],
    type_check_func: Optional[Callable[[Union[str, int]], Union[str, int]]] = None,
) -> Union[String, Number]:
    if type_check_func:
        raw_arg = type_check_func(raw_arg)

    if isinstance(raw_arg, str):
        return String(raw_arg)
    elif isinstance(raw_arg, int):
        return Number(raw_arg)
    else:
        raise ValueError(f"unknown type {type(raw_arg)}")


souffle_parser = Lark(souffle_grammar)


def parse(program_str):
    try:
        return souffle_parser.parse(program_str)

    except (UnexpectedEOF, UnexpectedInput) as e:
        error_location = f"line {e.line}, column {e.column}"
        logger.error(
            (
                f"A feature in {e.get_context(program_str)} at {error_location} is"
                " not supported."
            ),
            exc_info=False,
        )
        exit(1)
    except LarkError as e:
        logger.error(f"A parsing error occurred: {e}", exc_info=False)
        exit(1)


def load_facts(
    directory: Union[str, Path],
    type_check_func: Optional[Callable[[Union[str, int]], Union[str, int]]] = None,
) -> List[Fact]:
    facts_pattern = Path(directory).glob("*.facts")
    csv_pattern = Path(directory).glob("*.csv")

    facts = []
    for file in itertools.chain(facts_pattern, csv_pattern):
        relation_name = file.stem
        with file.open() as csvfile:
            reader = csv.reader(csvfile, delimiter="\t")
            for row in reader:
                facts.append(
                    Fact(
                        Literal(
                            relation_name,
                            [to_symlog_arg(ra, type_check_func) for ra in row],
                            True,
                        ),
                        [],
                        False,
                    )
                )
    return facts


def user_load_facts(directory: Union[str, Path]) -> List[Fact]:
    return load_facts(directory, user_arg_check)


def write_facts(directory, facts):
    """write facts to directory"""
    # Create directory if it does not exist
    Path(directory).mkdir(parents=True, exist_ok=True)

    # Sort facts by their name
    sorted_facts = sorted(facts, key=lambda fact: fact.head.name)

    # Group facts by their name
    grouped_facts = itertools.groupby(sorted_facts, key=lambda fact: fact.head.name)

    for name, facts_group in grouped_facts:
        file_path = Path(directory) / (name + ".facts")

        with file_path.open(mode="w") as file:
            writer = csv.writer(file, delimiter="\t")

            for fact in facts_group:
                writer.writerow(
                    pprint(arg).replace('"', "").replace("'", "")
                    for arg in fact.head.args
                )


def hash_program(program):
    def sort_by_string_representation(elements):
        if elements is None:
            return None
        return sorted(elements, key=str)

    # Create hash object
    hash_obj = hashlib.md5()

    normed_rules = [
        Rule(rule.head, sort_by_string_representation(rule.body))
        for rule in program.rules
    ]

    normed_rules = sort_by_string_representation(normed_rules)

    normed_facts = sort_by_string_representation(program.facts)

    normed_program = Program(
        program.declarations,
        [],
        [],
        normed_rules,
        normed_facts,
    )  # don't care about inputs and outputs

    # Prepare the data to be written
    data = pprint(normed_program)

    for i in range(0, len(data), 4096):
        chunk = data[i : i + 4096].encode()  # Encode chunk to bytes
        hash_obj.update(chunk)

    # Return the hexadecimal digest of the hash
    return hash_obj.hexdigest()


def compile_souffle(souffle_file, binary_file, *souffle_args):
    if os.path.exists(souffle_file):
        run(
            ["souffle", "-o", binary_file, souffle_file] + list(souffle_args),
            check=True,
            stdout=DEVNULL,
        )
    else:
        print(f"Souffle file {souffle_file} does not exist!")


def compile_if_changed(
    program, souffle_file, binary_file, hash_file_path, *souffle_args
):
    # Check if source file has been modified
    if os.path.exists(souffle_file):
        curr_hash = hash_program(program)
        prev_hash = None

        if os.path.exists(hash_file_path):
            with open(hash_file_path, "r") as file:
                prev_hash = file.read().strip()

        if curr_hash != prev_hash:
            compile_souffle(souffle_file, binary_file, *souffle_args)

            # Store current hash to file
            with open(hash_file_path, "w") as file:
                file.write(curr_hash)
    else:
        print(f"Souffle file {souffle_file} does not exist!")


def run_binary(binary_file, *args):
    if os.path.exists(binary_file):
        # Run the binary file
        run(
            [f"{binary_file}"] + list(args), check=True, stdout=DEVNULL
        )  # , stderr=DEVNULL)
    else:
        raise ValueError(f"Binary file {binary_file} does not exist!")


def run_program(program, facts):
    def run_cmd(cmd):
        try:
            run(cmd, check=True, stdout=DEVNULL)  # , stderr=DEVNULL)
        except CalledProcessError:
            print("----- error while solving: ----")
            print(pprint(program))
            print("---- on -----------------------")
            print("".join([pprint(fact) for fact in facts]))
            exit(1)

    with NamedTemporaryFile() as datalog_script:
        datalog_script.write(pprint(program).encode())
        datalog_script.flush()
        with TemporaryDirectory() as input_directory:
            write_facts(input_directory, facts)
            with TemporaryDirectory() as output_directory:
                cmd = [
                    "souffle",
                    datalog_script.name,
                    "-F",
                    input_directory,
                    "-D",
                    output_directory,
                    "-w",
                    "--jobs=auto",
                ]
                run_cmd(cmd)

                return load_facts(output_directory)
