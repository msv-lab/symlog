from symlog.souffle import (
    Underscore,
    Variable,
    SymbolicNumber,
    SymbolicString,
    String,
    Number,
    Literal,
    Rule,
    SYM,
    NUM,
)
from symlog.common import (
    SYMBOLIC_CONSTANT_PREFIX,
    BINDING_VARIABLE_PREFIX,
    DOMAIN_PREDICATE_PREFIX,
)


class SyntaxChecker:
    def __init__(self, env=None):
        self.env = env
        self.literal_arg_num = {}
        self.literal_constant_types = {}

    def check_literal(self, literal: Literal):
        # check if the arg types are legal
        for arg in literal.args:
            if not isinstance(
                arg,
                (Variable, String, Number, SymbolicNumber, SymbolicString, Underscore),
            ):
                raise TypeError(f"Type of {arg} is illegal in {literal}")

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
                    raise TypeError(
                        f"Type of argument {arg} in {literal} is inconsistent."
                    )
                self.literal_constant_types[loc] = type(arg)

    def check_rule(self, rule: Rule):
        # check literals in the rule
        for literal in rule.body:
            self.check_literal(literal)
        self.check_literal(rule.head)

        # check if the head has underscore args
        if any(isinstance(arg, Underscore) for arg in rule.head.args):
            raise TypeError(f"Underscore cannot be used in the head of a rule: {rule}")

        # check if the head is negated
        if not rule.head.positive:
            raise TypeError(f"Negated head is not allowed: {rule}")

        # check if the head has symbolic args
        if any(
            isinstance(arg, (SymbolicNumber, SymbolicString)) for arg in rule.head.args
        ):
            raise TypeError(
                f"Symbolic constants cannot be used in the head of a rule: {rule}"
            )

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

    def check_fact(self, fact: Rule):
        # check type
        if not (isinstance(fact, Rule) and len(fact.body) == 0):
            raise TypeError(f"Illegal fact: {fact}. Please use Fact to create it.")

        # check if the fact has non-constant args
        constant_types = [SymbolicNumber, SymbolicString, String, Number]
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

    def check_output_fact(self, output_fact: Rule):
        # check type
        if not (isinstance(output_fact, Rule) and len(output_fact.body) == 0):
            raise TypeError(
                f"Illegal output fact: {output_fact}. Please use OutputFact to create it."
            )

        # check if the fact has non-constant args
        constant_types = [String, Number]
        if any(type(arg) not in constant_types for arg in output_fact.head.args):
            raise TypeError(f"Argument in output fact: {output_fact} is not constant.")

        # check if the argument has conflicting keywords
        for arg in output_fact.head.args:
            if any(
                [
                    arg.startswith(SYMBOLIC_CONSTANT_PREFIX),
                    arg.startswith(BINDING_VARIABLE_PREFIX),
                    arg.startswith(DOMAIN_PREDICATE_PREFIX),
                ]
            ):
                raise ValueError(f"conflict with keyword {arg}")
