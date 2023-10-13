from tempfile import TemporaryDirectory, NamedTemporaryFile
from pathlib import Path
from subprocess import run, DEVNULL, CalledProcessError
import itertools
import csv
from collections import namedtuple
import os
import hashlib
from dotenv import load_dotenv
from typing import List, Union, Callable, Optional

from symlog.common import (
    SYMBOLIC_CONSTANT_PREFIX,
    BINDING_VARIABLE_PREFIX,
    DOMAIN_PREDICATE_PREFIX,
)

load_dotenv()

# relation_decls: name -> argument types
# output: list of names
# rules: list of rules
Program = namedtuple(
    "Program",
    [
        "type_decls",
        "relation_decls",
        "functor_decls",
        "inputs",
        "outputs",
        "rules",
        "facts",
    ],
)
_Rule = namedtuple("Rule", ["head", "body"])
_Literal = namedtuple("Literal", ["name", "args", "positive"])
Unification = namedtuple("Unification", ["left", "right", "positive"])
BinaryExpression = namedtuple("BinaryExpression", ["left", "right", "op"])
Aggregator = namedtuple("Aggregator", ["op", "atom"])
IntrisicFunctionCall = namedtuple("IntrisicFunctionCall", ["functor", "args"])
UserDefFunctionCall = namedtuple("UserDefFunctionCall", ["functor", "args"])
Variable = namedtuple("Variable", ["name"])
String = namedtuple("String", ["value"])
Number = namedtuple("Number", ["value"])
SymbolicConstant = namedtuple("SymbolicConstant", ["value", "fixed"])
Term = Union[Variable, String, Number]
FunctorTypes = namedtuple("FunctorTypes", ["arg_types", "ret_type"])
Record = namedtuple("Record", ["args"])
BaseType = namedtuple("BaseType", ["type_name"])
EquivelenceType = namedtuple("EquivelenceType", ["type_names"])
RecordType = namedtuple("RecordType", ["attrs"])
Comparision = namedtuple("Comparision", ["left", "right", "op"])
SymbolicString = namedtuple("SymbolicString", ["name"])
SymbolicNumber = namedtuple("SymbolicNumber", ["name"])
Underscore = namedtuple("UnderScore", [])


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


Rule = namedtuple_with_methods(_Rule)
Literal = namedtuple_with_methods(_Literal)


# types
SYM = "symbol"
NUM = "number"


def pprint(node):
    def pprint_inner(node):
        if isinstance(node, Program):
            return pprint_program(node)
        if isinstance(node, Rule):
            return pprint_rule(node)
        if isinstance(node, Literal):
            return pprint_literal(node)
        if isinstance(node, Unification):
            return pprint_unification(node)
        if isinstance(node, Comparision):
            return pprint_comparision(node)
        if isinstance(node, Variable):
            return pprint_term(node)
        if isinstance(node, String):
            return pprint_term(node)
        if isinstance(node, BinaryExpression):
            return pprint_term(node)
        if isinstance(node, Aggregator):
            return pprint_term(node)
        if isinstance(node, IntrisicFunctionCall):
            return pprint_term(node)
        if isinstance(node, UserDefFunctionCall):
            return pprint_term(node)
        if isinstance(node, Record):
            return pprint_term(node)
        if isinstance(node, Number):
            return pprint_term(node)
        raise NotImplementedError(f"pprint for {type(node)} is not implemented")

    def pprint_term(term):
        if isinstance(term, Variable):
            return term.name
        if isinstance(term, String):
            return '"' + term.value.replace('"', "") + '"'
        if isinstance(term, BinaryExpression):
            return f"{pprint_term(term.left)} {term.op} {pprint_term(term.right)}"
        if isinstance(term, Aggregator):
            return f"{term.op}" + ": {" + f"{pprint_literal(term.atom)}" + "}"
        if isinstance(term, IntrisicFunctionCall):
            args_result = ", ".join([pprint_term(t) for t in term.args])
            return f"{term.functor}({args_result})"
        if isinstance(term, UserDefFunctionCall):
            args_result = ", ".join([pprint_term(t) for t in term.args])
            return f"@{term.functor}({args_result})"
        if isinstance(term, Record):
            args_result = ", ".join([pprint_term(t) for t in term.args])
            return f"[{args_result}]"
        if isinstance(term, SymbolicString):
            return '"' + term.name + '"'
        if isinstance(term, SymbolicNumber):
            return str(term.name)
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

    def pprint_comparision(c):
        return f"{pprint_term(c.left)} {c.op} {pprint_term(c.right)}"

    def pprint_rule(rule):
        result = ""
        if rule.head.name:
            result += pprint_literal(rule.head)
        if rule.body:
            result += " :- "
        body_results = []
        if rule.body:
            for el in rule.body:
                if isinstance(el, Unification):
                    body_results.append(pprint_unification(el))
                elif isinstance(el, Comparision):
                    body_results.append(pprint_comparision(el))
                elif isinstance(el, Literal):
                    body_results.append(pprint_literal(el))
                else:
                    raise ValueError(f"unknown body element {el}")
        result += ", ".join(body_results) + ".\n"
        return result

    def pprint_program(program):
        result = ""

        for name, type_ in program.type_decls.items():
            result += f".type {name}"
            if isinstance(type_, BaseType):
                result += f" <: {type_.type_name}\n"
            elif isinstance(type_, EquivelenceType):
                types = "|".join(type_.type_names)
                result += f" = {types}\n"
            elif isinstance(type_, RecordType):
                attrs = ", ".join([f"{x}:{y}" for x, y in type_.attrs])
                result += f" = [{attrs}]\n"
            else:
                raise ValueError(f"unknown type {type_}")

        for name, types in program.relation_decls.items():
            result += f".decl {name}("
            types_results = [f"v{i}:{t}" for i, t in enumerate(types)]
            result += ", ".join(types_results) + ")\n"

        for name, functor_types in program.functor_decls.items():
            result += f".functor {name}("
            types_results = [f"v{i}:{t}" for i, t in enumerate(functor_types.arg_types)]
            result += ", ".join(types_results) + ") : " + functor_types.ret_type + "\n"

        for name in program.inputs:
            result += f".input {name}\n"

        for name in program.outputs:
            result += f".output {name}\n"

        for rule in program.rules:
            result += pprint_rule(rule)

        for fact in program.facts:
            result += pprint_rule(fact)

        return result

    return pprint_inner(node)


def transform(node, f):
    def transform_inner(node, f):
        if (
            isinstance(node, Variable)
            or isinstance(node, String)
            or isinstance(node, Number)
        ):
            return transform_term(node, f)
        if isinstance(node, Unification):
            return transform_unification(node, f)
        if isinstance(node, Comparision):
            return transform_comparision(node, f)
        if isinstance(node, Literal):
            return transform_literal(node, f)
        if isinstance(node, Rule):
            return transform_rule(node, f)
        if isinstance(node, Program):
            return transform_program(node, f)

    def transform_term(t, f):
        return f(t)

    def transform_unification(u, f):
        return f(
            Unification(
                transform_term(u.left, f), transform_term(u.right, f), u.positive
            )
        )

    def transform_comparision(c, f):
        return f(
            Comparision(transform_term(c.left, f), transform_term(c.right, f), c.op)
        )

    def transform_literal(l, f):
        return f(Literal(l.name, [transform_term(t, f) for t in l.args], l.positive))

    def transform_rule(rule, f):
        return f(
            Rule(
                transform_literal(rule.head, f),
                [transform_inner(n, f) for n in rule.body] if rule.body else [],
            )
        )

    def transform_program(program, f):
        return f(
            Program(
                program.type_decls,
                program.relation_decls,
                program.functor_decls,
                program.inputs,
                program.outputs,
                [transform_rule(r, f) for r in program.rules],
                [transform_rule(fact, f) for fact in program.facts],
            )
        )

    return transform_inner(node, f)


def collect(node, p):
    result = []

    def collect_inner(node, p):
        if (
            isinstance(node, Variable)
            or isinstance(node, String)
            or isinstance(node, Number)
        ):
            collect_term(node, p)
        if isinstance(node, Unification):
            collect_unification(node, p)
        if isinstance(node, Literal):
            collect_literal(node, p)
        if isinstance(node, Comparision):
            collect_comparison(node, p)
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

    def collect_comparison(comparison, p):
        collect_term(comparison.left, p)
        collect_term(comparison.right, p)
        if p(comparison):
            result.append(comparison)

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
        for fact in program.facts:
            collect_rule(fact, p)
        if p(program):
            result.append(program)

    collect_inner(node, p)
    return result


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


def load_facts(
    directory: Union[str, Path],
    type_check_func: Optional[Callable[[Union[str, int]], Union[str, int]]] = None,
) -> List[Rule]:
    facts_pattern = Path(directory).glob("*.facts")
    csv_pattern = Path(directory).glob("*.csv")

    facts = []
    for file in itertools.chain(facts_pattern, csv_pattern):
        relation_name = file.stem
        with file.open() as csvfile:
            reader = csv.reader(csvfile, delimiter="\t")
            for row in reader:
                facts.append(
                    Rule(
                        Literal(
                            relation_name,
                            [to_symlog_arg(ra, type_check_func) for ra in row],
                            True,
                        ),
                        [],
                    )
                )
    return facts


def user_load_facts(directory: Union[str, Path]) -> List[Rule]:
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
        program.type_decls,
        program.relation_decls,
        program.functor_decls,
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
