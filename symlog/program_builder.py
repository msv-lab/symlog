from symlog.souffle import (
    String as SouffleString,
    Number as SouffleNumber,
    Variable as SouffleVariable,
    SymbolicString,
    SymbolicNumber,
    Literal as SouffleLiteral,
    Rule as SouffleRule,
    Fact as SouffleFact,
    Program,
    SymbolicNumberWrapper,
    SymbolicStringWrapper,
    Underscore,
    SYM,
    NUM,
    transform,
    collect,
)
from symlog.type_analyser import TypeAnalyser
from symlog.syntax_checker import SyntaxChecker
from symlog.utils import recursive_flatten
from symlog.common import SYMBOLIC_CONSTANT_MAX_NUM

from collections.abc import Iterable
from more_itertools import unique_everseen
from typing import List, FrozenSet
from copy import deepcopy
from itertools import chain


class ProgramBuilder:
    """A class that provides a set of methods to build a program."""

    @staticmethod
    def String(value: str) -> SouffleString:
        return SouffleString(value)

    @staticmethod
    def Number(value: int) -> SouffleNumber:
        return SouffleNumber(value)

    @staticmethod
    def Variable(name: str) -> SouffleVariable:
        if name == "_":
            return Underscore()
        return SouffleVariable(name)

    @staticmethod
    def SymbolicConstant(name: str, type: str):
        if type == SYM:
            return SymbolicStringWrapper(name, SymbolicString())
        elif type == NUM:
            return SymbolicNumberWrapper(name, SymbolicNumber())
        else:
            raise ValueError(f"Unknown symbolic constant type: {type}")

    @staticmethod
    def Literal(name, args, sign):
        return SouffleLiteral(name, args, sign)

    @staticmethod
    def Fact(name, args, symbolic_sign):
        return SouffleFact(SouffleLiteral(name, args, True), [], symbolic_sign)

    @staticmethod
    def Rule(head, body):
        return SouffleRule(head, body)

    @staticmethod
    def SymbolicSign(fact):
        return ProgramBuilder.Fact(fact.head.name, fact.head.args, True)

    @staticmethod
    def infer_whole_program(
        rules: FrozenSet[SouffleRule],
        facts: FrozenSet[SouffleFact],
        inputs: List[str] = None,
        outputs: List[str] = None,
    ) -> Program:
        """Infers the whole program from the given rules and facts.

        :param rules: The rules of the program
        :type rules: FrozenSet[souffle.Rule]
        :param facts: The facts of the program
        :type facts: FrozenSet[souffle.Fact]
        :param inputs: The names of the input relations
        :type inputs: List[str]
        :param outputs: The names of the output relations
        :type outputs: List[str]
        :raises ValueError:
        :raises TypeError:
        :return: The inferred program
        :rtype: Program
        """

        # check syntax of rules and facts
        syntax_checker = SyntaxChecker()
        syntax_checker.check_syntax(rules, facts)

        # infer the declarations of the program
        type_analyser = TypeAnalyser()
        declarations = type_analyser.infer_declarations(rules, facts)

        # get the list of symbols
        symbol_list = ProgramBuilder.extract_symbols_from_facts(facts)

        # drop wrapper of the symbols
        updated_facts = ProgramBuilder.drop_symbol_wrappers(facts)

        # get the names of the input and output relations
        rule_head_names = set(map(lambda x: x.head.name, rules))
        rule_body_names = set([l.name for r in rules for l in r.body])
        edb_names = rule_body_names - rule_head_names
        idb_names = rule_head_names

        if inputs is not None:
            edb_names = inputs
        if outputs is not None:
            idb_names = outputs

        program = Program(
            declarations=declarations,
            inputs=edb_names,
            outputs=idb_names,
            rules=rules,
            facts=updated_facts,
            symbols=symbol_list,
        )
        return program

    @staticmethod
    def drop_symbol_wrappers(facts: FrozenSet[SouffleFact]):
        """Drop wrapper of the symbols."""
        updated_facts = frozenset(
            transform(
                f,
                lambda x: (
                    x.payload
                    if isinstance(x, (SymbolicStringWrapper, SymbolicNumberWrapper))
                    else x
                ),
            )
            for f in facts
        )
        return updated_facts

    @staticmethod
    def extract_symbols_from_facts(facts: FrozenSet[SouffleFact]):
        """Extract the symbols from the given facts."""
        symbol_list = list(
            unique_everseen(
                chain.from_iterable(
                    collect(
                        f,
                        lambda x: isinstance(
                            x, (SymbolicStringWrapper, SymbolicNumberWrapper)
                        ),
                    )
                    for f in facts
                )
            )
        )

        return symbol_list

    @staticmethod
    def update_program(
        ori_program: Program,
        declarations=None,
        inputs=None,
        outputs=None,
        rules=None,
        facts=None,
        symbols=None,
    ):
        """Updates the given program with the given declarations, inputs, outputs, rules, symbolic sign facts, non symbolic sign facts and symbols."""

        declarations = (
            ori_program.declarations if declarations is None else declarations
        )
        inputs = ori_program.inputs if inputs is None else inputs
        outputs = ori_program.outputs if outputs is None else outputs
        rules = ori_program.rules if rules is None else rules
        facts = ori_program.facts if facts is None else facts
        symbols = ori_program.symbols if symbols is None else symbols

        new_program = Program(
            declarations=declarations,
            inputs=inputs,
            outputs=outputs,
            rules=rules,
            facts=facts,
            symbols=symbols,
        )

        return new_program

    @staticmethod
    def preprocess_parsed_program(parsed_program, input_facts, outputs):
        # check syntax of rules and facts NOTE: must be done before dropping wrappers
        syntax_checker = SyntaxChecker()
        syntax_checker.check_syntax(parsed_program.rules, input_facts)

        symbol_list = ProgramBuilder.extract_symbols_from_facts(input_facts)
        updated_facts = ProgramBuilder.drop_symbol_wrappers(input_facts)
        program = ProgramBuilder.update_program(
            parsed_program, facts=updated_facts, outputs=outputs, symbols=symbol_list
        )

        return program

    @staticmethod
    def substitute(source, subs: dict):
        """Substitute the input object with the given subs."""

        source = deepcopy(source)

        # substitute the new source facts
        def atom_substitute(atom, subs):
            if atom in subs:
                return subs[atom]
            else:
                return atom

        updated = transform(source, lambda x: atom_substitute(x, subs))

        return updated

    @staticmethod
    def _polymorph_to_tuple(source):
        if len(source) == 1 and isinstance(source[0], Iterable):
            return tuple(recursive_flatten(source))

        return tuple([source])
