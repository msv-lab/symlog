from symlog.souffle import NUM, SYM
from symlog.shortcuts import (
    Rule,
    Fact,
    String,
    Variable,
    Literal,
    SymbolicSign,
    SymbolicConstant,
    symex,
)
from z3 import And, Or, Not, Bool, Const, StringSort, IntSort, simplify, BoolVal


def test_symex_with_sym_sign():
    rule = Rule(
        Literal("t", [Variable("X"), Variable("Z")], True),
        [
            Literal("r", [Variable("X"), Variable("Y")], True),
            Literal("s", [Variable("Y"), Variable("Z")], True),
        ],
    )

    facts = [
        SymbolicSign(Fact("r", [String("a"), String("b")])),
        Fact("r", [String("b"), String("c")]),
        Fact("s", [String("b"), String("c")]),
        SymbolicSign(Fact("s", [String("c"), String("d")])),
    ]

    interested_output_facts = set([Fact("t", [String("a"), String("c")])])

    constraints = symex([rule], facts, interested_output_facts)
    constraints = {k: v.to_z3() for k, v in constraints.items()}

    answer = {Fact("t", [String("a"), String("c")]): simplify(Bool('r("a", "b").'))}

    assert constraints == answer


def test_symex_with_sym_const_sign():
    rule = Rule(
        Literal("t", [Variable("X"), Variable("Z")], True),
        [
            Literal("r", [Variable("X"), Variable("Y")], True),
            Literal("s", [Variable("Y"), Variable("Z")], True),
        ],
    )

    facts = [
        Fact("r", [SymbolicConstant("alpha", type=SYM), String("b")]),
        Fact("r", [String("b"), String("c")]),
        Fact("s", [String("b"), String("c")]),
        SymbolicSign(Fact("s", [String("c"), String("d")])),
    ]

    target_outputs = {Fact("t", [String("b"), String("d")])}

    constraints = symex([rule], facts, target_outputs)

    constraints = {k: v.to_z3() for k, v in constraints.items()}

    answer = {
        Fact("t", [String("b"), String("d")]): simplify(
            Or(
                And(Const("alpha", StringSort()) == "b", Bool('s("c", "d").')),
                And(
                    Const("alpha", StringSort()) == "symlog_symbolic_1",
                    Bool('s("c", "d").'),
                ),
            )
        )
    }

    assert constraints == answer


def test_symex_with_multiple_sym_sign():
    rule = Rule(
        Literal("t", [Variable("X"), Variable("Z")], True),
        [
            Literal("r", [Variable("X"), Variable("Y")], True),
            Literal("s", [Variable("Y"), Variable("Z")], True),
        ],
    )

    facts = [
        SymbolicSign(Fact("r", [SymbolicConstant("alpha", type=SYM), String("b")])),
        Fact("r", [String("b"), String("c")]),
        Fact("s", [String("b"), String("c")]),
        SymbolicSign(Fact("s", [String("c"), String("d")])),
    ]

    target_outputs = {Fact("t", [String("a"), String("c")])}

    constraints = symex([rule], facts, target_outputs)
    constraints = {k: v.to_z3() for k, v in constraints.items()}
    answer = {
        Fact("t", [String("a"), String("c")]): simplify(
            And(
                [
                    Const("alpha", StringSort()) == "a",
                    Bool('r("a", "b").'),
                ]
            )
        )
    }

    assert constraints == answer


def test_symex_with_multiple_target_outputs():
    rule = Rule(
        Literal("t", [Variable("X"), Variable("Z")], True),
        [
            Literal("r", [Variable("X"), Variable("Y")], True),
            Literal("s", [Variable("Y"), Variable("Z")], True),
        ],
    )

    facts = [
        Fact("r", [SymbolicConstant("alpha", type=SYM), String("b")]),
        Fact("r", [String("b"), String("c")]),
        Fact("s", [String("b"), String("c")]),
        SymbolicSign(Fact("s", [String("c"), String("d")])),
    ]

    target_outputs = {
        Fact("t", [String("a"), String("c")]),
        Fact("t", [String("e"), String("c")]),
    }

    constraints = symex([rule], facts, target_outputs)

    updated_constraints = {k: v.to_z3() for k, v in constraints.items()}

    answer = {
        Fact("t", [String("a"), String("c")]): simplify(
            Const("alpha", StringSort()) == "a"
        ),
        Fact("t", [String("e"), String("c")]): simplify(
            Const("alpha", StringSort()) == "e"
        ),
    }

    assert updated_constraints == answer


def test_symex_with_nothing():
    rule = Rule(
        Literal("t", [Variable("X"), Variable("Z")], True),
        [
            Literal("r", [Variable("X"), Variable("Y")], True),
            Literal("s", [Variable("Y"), Variable("Z")], True),
        ],
    )

    facts = [
        Fact("r", [String("a"), String("b")]),
        Fact("r", [String("b"), String("c")]),
        Fact("s", [String("b"), String("c")]),
        Fact("s", [String("c"), String("d")]),
    ]

    target_outputs = {
        Fact("t", [String("a"), String("c")]),
        Fact("t", [String("e"), String("c")]),
    }

    constraints = symex([rule], facts, target_outputs)

    updated_constraints = {k: v.to_z3() for k, v in constraints.items()}

    answer = {
        Fact("t", [String("a"), String("c")]): BoolVal(True),
    }

    assert updated_constraints == answer
