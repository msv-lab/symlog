from tempfile import TemporaryDirectory, NamedTemporaryFile
from pathlib import Path
from subprocess import run, DEVNULL, CalledProcessError
import itertools
import csv
from collections import namedtuple
import os
import hashlib
from typing import List, Union, Callable, Optional, Set, Dict
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


class ExtendedNamedTuple:
    def __repr__(self):
        return pprint(self).replace("\n", "")

    def __str__(self):
        return pprint(self).replace("\n", "")

    def __hash__(self):
        return hash(pprint(self).replace("\n", ""))


def namedtuple_with_methods(namedtuple_cls):
    return type(namedtuple_cls.__name__, (ExtendedNamedTuple, namedtuple_cls), {})


# relation_decls: name -> argument types
# output: list of names
# rules: list of rules

Variable = namedtuple("Variable", ["name"])
String = namedtuple("String", ["value"])
Number = namedtuple("Number", ["value"])
Underscore = namedtuple("UnderScore", [])


class SymbolicString(namedtuple("SymbolicString", ["name"])):
    _next_free_id = 1

    def __new__(cls, name=None):
        if name is None:
            name = f"{SYMBOLIC_CONSTANT_PREFIX}{cls._next_free_id}"
            cls._next_free_id += 1
        instance = super().__new__(cls, name)
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

    def __new__(cls):
        name = SYMLOG_NUM_POOL[cls._next_free_id]
        instance = super().__new__(cls, name)
        cls._next_free_id += 1
        return instance

    def __deepcopy__(self, memo):
        # ignore memo
        return super().__new__(self.__class__, self.name)

    def __repr__(self) -> str:
        return f"SymbolicNumber({self.name})"

    def __str__(self) -> str:
        return f"SymbolicNumber({self.name})"


SymbolicStringWrapper = namedtuple("SymbolicStringWrapper", ["name", "payload"])
SymbolicNumberWrapper = namedtuple("SymbolicNumberWrapper", ["name", "payload"])
Rule = namedtuple_with_methods(namedtuple("Rule", ["head", "body"]))
Literal = namedtuple_with_methods(namedtuple("Literal", ["name", "args", "positive"]))
Fact = namedtuple_with_methods(namedtuple("Fact", ["head", "body", "symbolic_sign"]))
Program = namedtuple_with_methods(
    namedtuple(
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
)

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
        raise NotImplementedError(
            "Negated atoms are not supported. Please convert them to positive atoms"
        )

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
    tmp_inner = transform_inner(node, f)
    if not isinstance(tmp_inner, Program):
        return tmp_inner

    rules = []
    facts = []
    for fact_rule in tmp_inner.facts + tmp_inner.rules:
        if isinstance(fact_rule, Rule):
            rules.append(fact_rule)
        elif isinstance(fact_rule, Fact):
            facts.append(fact_rule)
        else:
            assert False, f"unknown fact_rule {fact_rule}. Bug?"
    return Program(
        tmp_inner.declarations,
        tmp_inner.inputs,
        tmp_inner.outputs,
        rules,
        facts,
        tmp_inner.symbols,
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
    decl_type: str,
    check_func: Optional[Callable] = None,
) -> Union[String, Number]:
    def is_number(s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    if check_func:
        raw_arg = check_func(raw_arg)

    if decl_type == SYM:
        return String(raw_arg)
    elif decl_type == NUM:
        try:
            return Number(int(raw_arg))
        except ValueError:
            logger.error(
                f"Argument {raw_arg} is not a valid number for type {decl_type}.",
                exc_info=False,
            )
    else:
        raise ValueError(f"unknown type {type(raw_arg)}")


souffle_parser = Lark(souffle_grammar)


def parse(program_str):
    try:
        return ASTConstructor().transform(souffle_parser.parse(program_str))

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
    declarations: Dict[str, List[str]],
    fact_names: List[str],
    check_func: Optional[Callable] = None,
) -> Set[Fact]:
    facts_pattern = Path(directory).glob("*.facts")
    csv_pattern = Path(directory).glob("*.csv")

    facts = set()
    target_files = itertools.chain(facts_pattern, csv_pattern)
    for file in target_files:
        relation_name = file.stem

        if fact_names and relation_name not in fact_names:
            continue  # skip non-input facts

        with file.open() as csvfile:
            reader = csv.reader(csvfile, delimiter="\t")
            for row in reader:
                try:
                    facts.add(
                        Fact(
                            Literal(
                                relation_name,
                                [
                                    to_symlog_arg(
                                        ra,
                                        declarations[relation_name][idx],
                                        check_func,
                                    )
                                    for idx, ra in enumerate(row)
                                ],
                                True,
                            ),
                            [],
                            False,
                        )
                    )
                except KeyError:
                    logger.error(
                        f"Relation {relation_name} is not declared in the program.",
                        exc_info=False,
                    )
                    exit(1)
                except IndexError:
                    logger.error(
                        f"Too many arguments for relation {relation_name}.",
                        exc_info=False,
                    )
                    exit(1)
    return facts


def user_load_facts(
    directory: Union[str, Path], declarations: Dict[str, List[str]], inputs: List[str]
) -> Set[Fact]:
    return load_facts(directory, declarations, inputs, user_arg_check)


def write_facts(directory, facts):
    """write facts to directory"""
    Path(directory).mkdir(parents=True, exist_ok=True)

    # sort facts by their name
    sorted_facts = sorted(facts, key=lambda fact: fact.head.name)

    # group facts by their name
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


def compile_and_run(program, facts):
    # hash the content to create a unique identifier
    encoded_program = pprint(program).encode()
    hash_object = hashlib.sha256(encoded_program)
    hex_dig = hash_object.hexdigest()

    binary_name = f"binary_{hex_dig}"

    if not os.path.exists(binary_name):
        # if binary doesn't exist, write the content to a temp file, compile, and rename binary
        with NamedTemporaryFile(delete=False, suffix=".dl") as temp_file:
            temp_file.write(encoded_program)
            temp_file.flush()

        temp_binary_name = os.path.splitext(temp_file.name)[0]
        compile_command = ["souffle", "-o", temp_binary_name, temp_file.name]

        try:
            run(compile_command, check=True)
        except CalledProcessError:
            logger.error(
                "Error while compiling the program. Please check the program.",
                exc_info=False,
            )

        # rename compiled binary to our hashed name
        os.rename(temp_binary_name, binary_name)

        # cleanup temp file
        os.remove(temp_file.name)

    # execute the binary
    with TemporaryDirectory() as input_directory:
        write_facts(input_directory, facts)
        with TemporaryDirectory() as output_directory:
            cmd = [
                "./" + binary_name,
                "-F",
                input_directory,
                "-D",
                output_directory,
                "--jobs=auto",
            ]

            try:
                run(cmd, check=False, stdout=DEVNULL, stderr=DEVNULL)
            except Exception as e:
                logger.error(
                    f"Error while running the program: {e.stdout.decode()}",
                    exc_info=False,
                )
                exit(1)
            return load_facts(output_directory, program.declarations, program.outputs)


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

                return load_facts(
                    output_directory, program.declarations, program.outputs
                )
