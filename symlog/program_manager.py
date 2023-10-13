from symlog.souffle import (
    String,
    Number,
    Variable,
    SymbolicString,
    SymbolicNumber,
    Literal,
    Rule,
    Program,
    SYM,
    NUM,
    transform,
)
from symlog.common import SYMLOG_NUM_POOL, SYMBOLIC_CONSTANT_PREFIX
from typing import List
from symlog.utils import is_sublist, recursive_flatten, divide_set_by_subset
from collections.abc import Iterable


class ProgramManager:
    def __init__(self, env=None):
        self.env = env
        self.syntax_checker = env.syntax_checker
        self.type_analyser = env.type_analyser
        self._symbols = {}
        self._symbolic_sign_facts = []
        self._next_free_id = 1

        self._relation_declarations = {}
        self._rules = []
        self._facts = []
        self._inputs = []
        self._outputs = []

    def create_subprogram_copy(
        self, rules: List[Rule], facts: List[Rule], skip_fact_check=False
    ):
        assert is_sublist(
            rules, self._rules
        ), "Rules are inconsistent with the current managed program."

        if not skip_fact_check:
            assert is_sublist(
                facts, self._facts
            ), "Facts are inconsistent with the current managed program."

        rule_head_names = set(map(lambda x: x.head.name, rules))
        rule_body_names = set([l.name for r in rules for l in r.body])
        hb_names = rule_head_names | rule_body_names
        edb_names = rule_body_names - rule_head_names
        idb_names = rule_head_names
        program = Program(
            {},
            {
                k: v for k, v in self.declarations.items() if k in hb_names
            },  # declare relations that are in the rules or facts
            {},
            [inp for inp in self.inputs if inp in edb_names],
            [
                oup for oup in self.outputs if oup in idb_names
            ],  # only keep the outputs that are in the rules
            rules,
            facts,
        )

        return program

    def substitue_fact_const(self, source_facts, subs: dict):
        source_tuple = self._polymorph_to_tuple(source_facts)
        # check if each element in the source tuple is a Fact.
        for element in source_tuple:
            if not (isinstance(element, Rule) and not (element.body)):
                raise ValueError(f"{type(element)} is not a Fact.")

        # check if the subs is a legal dict
        for key, value in subs.items():
            if not (isinstance(key, (String, Number))):
                raise ValueError(
                    f"{type(key)} is not a legal Constant. Legal constants are String"
                    " and Number."
                )
            if not (
                isinstance(value, (String, Number, SymbolicNumber, SymbolicString))
            ):
                raise ValueError(
                    f"{type(value)} is not a legal Constant. Legal constants are"
                    " String, Number, SymbolicConstant."
                )

        assert is_sublist(
            source_facts, self._facts
        ), "Facts are inconsistent with the current managed program. Bug?"

        non_source_facts, new_source_facts = divide_set_by_subset(
            self._facts, source_facts
        )

        # substitute the new source facts
        def atom_substitute(atom, subs):
            if atom in subs:
                return subs[atom]
            else:
                return atom

        new_source_facts = [
            transform(new_source_fact, lambda x: atom_substitute(x, subs))
            for new_source_fact in new_source_facts
        ]

        # update the facts
        self._facts = non_source_facts + new_source_facts

        # trigger type inference once facts are updated
        self._relation_declarations = self.type_analyser.infer_declarations(
            self._rules, self._facts
        )

    def _polymorph_to_tuple(self, source):
        if len(source) == 1 and isinstance(source[0], Iterable):
            return tuple(recursive_flatten(source))

        return tuple([source])

    def _get_symbolic_string(self, name=None):
        if name is not None and name in self._symbols:
            raise ValueError(f"Symbolic string {name} already exists.")
        real_sym_str = f"{SYMBOLIC_CONSTANT_PREFIX}{self._next_free_id}"
        self._next_free_id += 1
        if name is None:
            name = real_sym_str

        n = SymbolicString(real_sym_str)
        self._symbols[name] = n
        return n

    def _get_symbolic_number(self, name=None):
        if name is not None and name in self._symbols:
            raise ValueError(f"Symbolic number {name} already exists.")
        real_sym_num = SYMLOG_NUM_POOL[self._next_free_id]
        self._next_free_id += 1
        if name is None:
            name = real_sym_num

        n = SymbolicNumber(real_sym_num)
        self._symbols[name] = n
        return n

    # Node definitions start here

    def String(self, value):
        n = String(value)
        self.syntax_checker.check_string(n)
        return n

    def Number(self, value):
        n = Number(value)
        self.syntax_checker.check_number(n)
        return n

    def Variable(self, name):
        n = Variable(name)
        self.syntax_checker.check_variable(n)
        return n

    def SymbolicConstant(self, name, type):
        if type == SYM:
            return self._get_symbolic_string(name)
        elif type == NUM:
            return self._get_symbolic_number(name)
        else:
            raise ValueError(f"Unknown symbolic constant type: {type}")

    def Literal(self, name, args, sign=True):
        n = Literal(name, args, sign)
        self.syntax_checker.check_literal(n)
        return n

    def Fact(self, name, args):
        n = Rule(Literal(name, args, True), [])
        self.syntax_checker.check_fact(n)
        self._facts.append(n)

        # trigger type inference once a new fact is added
        self._relation_declarations = self.type_analyser.infer_declarations(
            self._rules, self._facts
        )
        return n

    def Rule(self, head, body):
        n = Rule(head, body)
        self.syntax_checker.check_rule(n)
        self._rules.append(n)

        # trigger type inference once a new rule is added
        self._relation_declarations = self.type_analyser.infer_declarations(
            self._rules, self._facts
        )
        return n

    def SymbolicSign(self, fact):
        self.syntax_checker.check_fact(fact)
        self._symbolic_sign_facts.append(fact)
        return fact

    def OutputFact(self, name, args):
        # no need to manage output facts
        n = Rule(Literal(name, args, True), [])
        self.syntax_checker.check_fact(n)
        return n

    @property
    def program(self):
        return Program(
            {},
            self.declarations,
            {},
            self.inputs,
            self.outputs,
            self.rules,
            self.facts,
        )

    @property
    def symbols(self):
        return self._symbols

    @property
    def symbolic_sign_facts(self):
        return self._symbolic_sign_facts

    @property
    def declarations(self):
        return self._relation_declarations

    @declarations.setter
    def declarations(self, decls):
        self._relation_declarations = decls

    @property
    def outputs(self):
        if not self._outputs:
            self._outputs = [rule.head.name for rule in self._rules]
        return self._outputs

    @outputs.setter
    def outputs(self, outputs):
        self._outputs = outputs

    @property
    def inputs(self):
        if not self._inputs:
            # default input is EDB set
            head_names = set([rule.head.name for rule in self._rules])
            body_names = set(
                [literal.name for rule in self._rules for literal in rule.body]
            )
            self._inputs = list(body_names - head_names)
        return self._inputs

    @inputs.setter
    def inputs(self, inputs):
        self._inputs = inputs

    @property
    def rules(self):
        return self._rules

    @property
    def facts(self):
        return self._facts
