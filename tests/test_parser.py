from symlog.environment import Environment
from symlog.souffle import Rule, Literal, Variable
import pytest
from lark.exceptions import UnexpectedInput


def test_parse_relation_decl():
    with Environment() as env:
        parser = env.parser
        program_str = ".decl my_relation(x: number, y: string)"
        ast = parser.parse(program_str)
        assert ast.relation_decls == {"my_relation": ["number", "string"]}


def test_parse_rule():
    with Environment() as env:
        parser = env.parser
        program_str = "my_relation(x, y) :- other_relation(x, z), third_relation(z, y)."
        result = parser.parse(program_str)
        assert (
            str(result.rules[0])
            == "my_relation(x, y) :- other_relation(x, z), third_relation(z, y)."
        )


def test_parse_fact():
    with Environment() as env:
        parser = env.parser
        program_str = 'my_relation(1, "hello").'
        result = parser.parse(program_str)
        assert str(result.facts[0]) == 'my_relation(1, "hello").'


def test_parse_input():
    with Environment() as env:
        parser = env.parser
        program_str = ".input my_input"
        result = parser.parse(program_str)
        assert result.inputs == ["my_input"]


def test_parse_output():
    with Environment() as env:
        parser = env.parser
        program_str = ".output my_output"
        result = parser.parse(program_str)
        assert result.outputs == ["my_output"]


def test_program():
    program_str = """
        .decl edge(x: number, y: number)
        .input edge
        .output path

        path(x, y) :- edge(x, y).
        path(x, z) :- path(x, y), edge(y, z).
    """

    with Environment() as env:
        parser = env.parser
        ast = parser.parse(program_str)

        assert ast.relation_decls == {"edge": ["number", "number"]}
        assert ast.inputs == ["edge"]
        assert ast.outputs == ["path"]
        assert str(ast.rules) == str(
            [
                Rule(
                    Literal("path", [Variable("x"), Variable("y")], True),
                    [Literal("edge", [Variable("x"), Variable("y")], True)],
                ),
                Rule(
                    Literal("path", [Variable("x"), Variable("z")], True),
                    [
                        Literal("path", [Variable("x"), Variable("y")], True),
                        Literal("edge", [Variable("y"), Variable("z")], True),
                    ],
                ),
            ]
        )


def test_program_with_parse_error():
    program_str = """
        .decl edge(x: number, y: number)
        .input edge
        .output path

        path(x, y) :- edge(x, y), x < y.
        path(x, z) :- path(x, y), edge(y, z).
    """

    with Environment() as env:
        parser = env.parser
        parser.parse(program_str)
        with pytest.raises(UnexpectedInput):
            parser.parse(program_str)


if __name__ == "__main__":
    test_program_with_parse_error()
