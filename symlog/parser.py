from lark import Lark, Transformer, v_args, UnexpectedInput, LarkError, UnexpectedEOF
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


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

    def __init__(self, env):
        self.env = env
        self.mgr = env.program_manager

        self.relation_decls = {}
        self.inputs = []
        self.outputs = []

    def number(self, n):
        return self.mgr.Number(int(n))

    def string(self, s):
        return self.mgr.String(s[1:-1])

    def var(self, v):
        return self.mgr.Variable(v)

    def directive(self, d, v):
        raise NotImplementedError("directives are not supported")

    def relation_decl(self, name, *attrs):
        self.relation_decls[name] = [x for _, x in attrs]

    def output(self, name):
        self.outputs.append(name)

    def input(self, name):
        self.inputs.append(name)

    def typed_var(self, v, t):
        return (v, t)

    def atom(self, name, *args):
        return self.mgr.Literal(name, args, True)

    def negated_atom(self, name, *args):
        return self.mgr.Literal(name, args, False)

    def body(self, *args):
        return args

    def rule(self, head, body):
        return self.mgr.Rule(head, body)

    def fact(self, fact):
        return self.mgr.Fact(fact.name, fact.args)

    def start(self, *_):
        self.mgr.declarations = self.relation_decls
        self.mgr.inputs = self.inputs
        self.mgr.outputs = self.outputs
        return self.mgr.program


class Parser:
    def __init__(self, env=None):
        self.env = env
        self.parser = Lark(
            souffle_grammar, parser="lalr", transformer=ASTConstructor(env)
        )

    def parse(self, program_str):
        try:
            return self.parser.parse(program_str)

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
