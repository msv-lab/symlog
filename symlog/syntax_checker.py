from symlog.souffle import (
    Underscore,
    Variable,
    SymbolicNumber,
    SymbolicString,
    String,
    Number,
    Literal,
    Rule,
    Fact,
    SymbolicNumberWrapper,
    SymbolicStringWrapper,
    SYMLOG_NUM_POOL,
    walk,
)
from symlog.common import (
    SYMBOLIC_CONSTANT_PREFIX,
)
from itertools import chain
from typing import List, FrozenSet


class SyntaxChecker:
    __slots__ = [
        "literal_arg_num",
        "literal_constant_types",
        "user_defined_symbol_map",
    ]

    def __init__(self):
        self.literal_arg_num = {}
        self.literal_constant_types = {}
        self.user_defined_symbol_map = {}

    def check_literal(self, literal: Literal):
        # check if the number of args is consistent
        if self.literal_arg_num.get(literal.name, False):
            if len(literal.args) != self.literal_arg_num[literal.name]:
                raise TypeError(f"Number of arguments of {literal} is inconsistent.")
        else:
            self.literal_arg_num[literal.name] = len(literal.args)

        # check if the constant arg types are consistent
        constant_types = (SymbolicNumber, SymbolicString, String, Number)
        for idx, arg in enumerate(literal.args):
            if isinstance(arg, constant_types):
                loc = (literal.name, idx)
                if (
                    loc in self.literal_constant_types
                    and type(arg) != self.literal_constant_types[loc]
                ):
                    if type(arg) in (
                        SymbolicString,
                        String,
                    ) and self.literal_constant_types[loc] in (SymbolicString, String):
                        continue
                    if type(arg) in (
                        SymbolicNumber,
                        Number,
                    ) and self.literal_constant_types[loc] in (SymbolicNumber, Number):
                        continue
                    raise TypeError(
                        f"Type of argument {arg} in {literal} is inconsistent."
                    )
                self.literal_constant_types[loc] = type(arg)

    def check_rule(self, rule: Rule):
        # check if the head has underscore args
        if any(isinstance(arg, Underscore) for arg in rule.head.args):
            raise TypeError(f"Underscore cannot be used in the head of a rule: {rule}")

        # check if the head is negated
        if not rule.head.positive:
            raise TypeError(f"Negated head is not allowed: {rule}")

        # check if the rule has symbolic args
        all_args = (
            arg
            for arg in chain(rule.head.args, *(literal.args for literal in rule.body))
        )
        if any(isinstance(arg, (SymbolicNumber, SymbolicString)) for arg in all_args):
            raise TypeError(f"Symbolic constants cannot be used in a rule: {rule}")

        # check if the rule has non-empty body
        if len(rule.body) == 0:
            raise TypeError(f"Rule {rule} has an empty body. Please use Fact instead.")

        # check if the args of head are included in the body's args
        all_body_args = {arg for literal in rule.body for arg in literal.args}
        head_args = {
            arg for arg in rule.head.args if isinstance(arg, Variable)
        }  # ignore constants
        if not head_args.issubset(all_body_args):
            missing_args = head_args - all_body_args
            raise TypeError(f"Ungrounded variables {missing_args} in {rule}")

    def check_fact(self, fact: Fact):
        # check type
        if not (isinstance(fact, Fact)):
            raise TypeError(f"Illegal fact: {fact}. Please use Fact to create it.")

        # check if the fact has non-constant args
        constant_types = [
            SymbolicNumber,
            SymbolicString,
            String,
            Number,
            SymbolicNumberWrapper,
            SymbolicStringWrapper,
        ]
        if any(type(arg) not in constant_types for arg in fact.head.args):
            raise TypeError(f"Argument in fact: {fact} is not constant.")

    def check_string(self, string: String):
        if not isinstance(string.value, str) and not string == Underscore:
            raise TypeError(f"Value of {string} is not a string.")

    def check_number(self, number: Number):
        if not isinstance(number.value, int) and not number == Underscore:
            raise TypeError(f"Value of {number} is not an integer.")

    def check_variable(self, variable: Variable):
        if not isinstance(variable.name, str):
            raise TypeError(f"Name of {variable} is not a string.")

    def check_symbolic_number_wrapper(self, sym_num_wrapper: SymbolicNumberWrapper):
        if not isinstance(sym_num_wrapper.name, str):
            raise TypeError(f"Name for representing {sym_num_wrapper} is not a string.")

        if sym_num_wrapper.payload != self.user_defined_symbol_map.get(
            sym_num_wrapper.name, sym_num_wrapper.payload
        ):
            raise ValueError(f"Symbolic number {sym_num_wrapper.name} already used.")
        self.user_defined_symbol_map[sym_num_wrapper.name] = sym_num_wrapper.payload

        assert isinstance(
            sym_num_wrapper.payload, SymbolicNumber
        ), "Illegal value. Bug?"

    def check_symbolic_string_wrapper(self, sym_str_wrapper: SymbolicStringWrapper):
        if not isinstance(sym_str_wrapper.name, str):
            raise TypeError(f"Name for representing {sym_str_wrapper} is not a string.")

        if sym_str_wrapper.payload != self.user_defined_symbol_map.get(
            sym_str_wrapper.name, sym_str_wrapper.payload
        ):
            raise ValueError(f"Symbolic string {sym_str_wrapper.name} already used.")
        self.user_defined_symbol_map[sym_str_wrapper.name] = sym_str_wrapper.payload

        assert isinstance(
            sym_str_wrapper.payload, SymbolicString
        ), "Illegal value. Bug?"

    def check_symbolic_number(self, sym_num: SymbolicNumber):
        assert sym_num.name in SYMLOG_NUM_POOL, "Illegal value. Bug?"

    def check_symbolic_string(self, sym_str: SymbolicString):
        assert sym_str.name.startswith(SYMBOLIC_CONSTANT_PREFIX), "Illegal value. Bug?"

    def check_node(self, node):
        if isinstance(node, String):
            self.check_string(node)
        elif isinstance(node, Number):
            self.check_number(node)
        elif isinstance(node, Variable):
            self.check_variable(node)
        elif isinstance(node, SymbolicNumberWrapper):
            self.check_symbolic_number_wrapper(node)
        elif isinstance(node, SymbolicStringWrapper):
            self.check_symbolic_string_wrapper(node)
        elif isinstance(node, SymbolicNumber):
            self.check_symbolic_number(node)
        elif isinstance(node, SymbolicString):
            self.check_symbolic_string(node)
        elif isinstance(node, Literal):
            self.check_literal(node)
        elif isinstance(node, Rule):
            self.check_rule(node)
        elif isinstance(node, Fact):
            self.check_fact(node)

        else:
            raise TypeError(f"Unknown node type: {type(node)}")

    def check_syntax(self, rules: FrozenSet[Rule], facts: FrozenSet[Fact]):
        for rule_or_fact in chain(rules, facts):
            walk(rule_or_fact, self.check_node)
