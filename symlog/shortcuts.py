import symlog.environment
from symlog.souffle import SYM, user_load_facts


def get_env():
    """Returns the global environment.

    :returns: The global environment
    :rtype: Environment
    """
    return symlog.environment.get_env()


def reset_env():
    """Resets the global environment, and returns the new one.

    :returns: A new environment after resetting the global environment
    :rtype: Environment
    """
    return symlog.environment.reset_env()


def Number(value):
    """Returns a number with the given value."""
    return get_env().program_manager.Number(value)


def String(value):
    """Returns a string with the given value."""
    return get_env().program_manager.String(value)


def Variable(name):
    """Returns a variable with the given name."""
    return get_env().program_manager.Variable(name)


def Literal(name, args):
    """Returns a literal with the given name and args."""
    return get_env().program_manager.Literal(name, args)


def Rule(head, body):
    """Returns a rule with the given head and body literals."""
    return get_env().program_manager.Rule(head, body)


def InFact(name, args):
    """Returns a input fact with the given name and args."""
    return get_env().program_manager.Fact(name, args)


def OutFact(name, args):
    """Returns a output fact with the given name and args."""
    return get_env().program_manager.OutputFact(name, args)


def SymbolicSign(fact):
    """Returns a fact with symbolic sign."""
    return get_env().program_manager.SymbolicSign(fact)


def SymbolicConstant(name=None, type=SYM):
    """Returns a symbolic constant with the given name and type."""
    return get_env().program_manager.SymbolicConstant(name, type)


def parse(program_path):
    """Parses the given program.

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

    return get_env().parser.parse(program_str)


def load_facts(directory_path):
    """Loads the facts in the given directory.

    :param directory_path: The path of the directory containing the facts
    :type directory_path: str
    :returns: The loaded facts
    :rtype: list of Fact
    """
    return user_load_facts(directory_path)


def substitue_fact_const(facts, const_dict):
    """Substitues the constants in the given facts with the given constant dictionary.

    :param facts: The facts to be substitued
    :type facts: list of Fact
    :param const_dict: The constant dictionary to be substitued
    :type const_dict: dict
    :returns: The substitued facts
    :rtype: list of Fact
    """
    return get_env().program_manager.substitue_fact_const(facts, const_dict)


def symex(rules, facts, interested_output_facts=set()):
    """Symbolically executes the given rules and facts.

    :param rules: The rules to be symbolically executed
    :type rules: list of Rule
    :param facts: The facts to be symbolically executed
    :type facts: list of Fact
    :param interested_output_facts: The output facts that we are interested in, defaults to set()
    :type interested_output_facts: set, optional
    :returns: The constraints collected during symbolic execution
    :rtype: dict
    """
    return get_env().symbolic_executor.symex(
        rules, facts, interested_output_facts=interested_output_facts
    )


def repair(rules, facts, wanted_out_facts, unwanted_out_facts):
    """Repairs the given facts such that the given wanted output facts are generated, and the given unwanted output facts are removed.

    :param rules: The rules to be repaired
    :type rules: list of Rule
    :param facts: The facts to be repaired
    :type facts: list of Fact
    :param wanted_out_facts: The output facts that we want to generate
    :type wanted_out_facts: set of Fact
    :param unwanted_out_facts: The output facts that we want to remove
    :type unwanted_out_facts: set of Fact
    :returns: The raw patches in the form of a model
    :rtype: Program
    """
    return get_env().repairer.repair(rules, facts, wanted_out_facts, unwanted_out_facts)
