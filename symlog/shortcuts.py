import symlog.souffle as souffle
import symlog.symbolic_executor as symbolic_executor
from symlog.program_builder import ProgramBuilder


def Number(value):
    """Returns a number with the given value."""
    return ProgramBuilder.Number(value)


def String(value):
    """Returns a string with the given value."""
    return ProgramBuilder.String(value)


def Variable(name):
    """Returns a variable with the given name."""
    return ProgramBuilder.Variable(name)


def Literal(name, args, sign=True):
    """Returns a literal with the given name and args."""
    return ProgramBuilder.Literal(name, args, sign)


def Rule(head, body):
    """Returns a rule with the given head and body literals."""
    return ProgramBuilder.Rule(head, body)


def Fact(name, args):
    """Returns a input fact with the given name and args."""
    return ProgramBuilder.Fact(name, args, False)


def SymbolicSign(fact):
    """Returns a fact with symbolic sign."""
    return ProgramBuilder.SymbolicSign(fact)


def SymbolicConstant(name=None, type=souffle.SYM):
    """Returns a SymbolicConstant with the given name and type."""
    return ProgramBuilder.SymbolicConstant(name, type)


def parse(program_path):
    """
    Parses the given program.

    :param program_path: The path of the program to be parsed
    :type program_path: str
    :returns: The parsed program
    :rtype: Program
    """
    try:
        with open(program_path) as file:
            program_str = file.read()
    except FileNotFoundError:
        raise ValueError(f"File not found: {program_path}")
    except PermissionError:
        raise ValueError(f"Permission denied: {program_path}")

    return souffle.parse(program_str)


def load_facts(directory_path, declarations, inputs=None):
    """Loads the facts in the given directory.

    :param directory_path: The path of the directory containing the facts
    :type directory_path: str
    :param declarations: The declarations of the facts
    :type declarations: dict
    :returns: The loaded facts
    :rtype: list of Fact
    """
    return souffle.user_load_facts(directory_path, declarations, inputs)


def substitute(source, subs_dict):
    """Substitutes the given dictionary in the given source.

    :param source: The source to be substituted
    :type source: Any
    :param subs_dict: The dictionary to be substituted
    :type subs_dict: dict
    """
    return ProgramBuilder.substitute(source, subs_dict)


def symex(rules, facts, interested_output_facts):
    """Symbolically executes the given rules and facts.

    :param rules: The rules to be symbolically executed
    :type rules: fronzenset of Rule
    :param facts: The facts to be symbolically executed
    :type facts: fronzenset of Fact
    :param interested_output_facts: The output facts that you are interested in
    :type interested_output_facts: fronzenset of Fact
    :returns: The constraints collected during symbolic execution
    :rtype: dict
    """
    return symbolic_executor.symex(rules, facts, interested_output_facts)
