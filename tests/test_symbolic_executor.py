from symlog.environment import Environment
from symlog.utils import check_equality
from symlog.symbolic_executor import OutputCondition, AtomicCondition
from symlog.souffle import NUM, pprint, SYM


def test_symex_with_sym_sign():
    with Environment() as env:
        manager = env.program_manager
        executor = env.symbolic_executor

        Rule = manager.Rule
        Literal = manager.Literal
        Fact = manager.Fact
        Variable = manager.Variable
        String = manager.String
        SymbolicSign = manager.SymbolicSign
        OutputFact = manager.OutputFact

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

        constraints = executor.symex([rule], facts)
        constraints = {k: v for k, v in sorted(constraints.items())}

        answer = {
            OutputFact("t", [String("b"), String("d")]): OutputCondition(
                [
                    OutputCondition(
                        [AtomicCondition([], [Fact("s", [String("c"), String("d")])])]
                    )
                ]
            ),
            OutputFact("t", [String("a"), String("c")]): OutputCondition(
                [
                    OutputCondition(
                        [AtomicCondition([], [Fact("r", [String("a"), String("b")])])]
                    )
                ]
            ),
        }
        answer = {k: v for k, v in sorted(answer.items())}

        assert check_equality(constraints, answer, ignore_order=True)


def test_symex_with_interested_output_facts():
    with Environment() as env:
        manager = env.program_manager
        executor = env.symbolic_executor
        Rule = manager.Rule
        Literal = manager.Literal
        Fact = manager.Fact
        Variable = manager.Variable
        String = manager.String
        SymbolicSign = manager.SymbolicSign
        OutputFact = manager.OutputFact

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

        interested_output_facts = set([OutputFact("t", [String("a"), String("c")])])

        constraints = executor.symex([rule], facts, interested_output_facts)

        print(constraints)

        answer = {
            OutputFact("t", [String("a"), String("c")]): OutputCondition(
                [
                    OutputCondition(
                        [AtomicCondition([], [Fact("r", [String("a"), String("b")])])]
                    )
                ]
            ),
        }

        print(answer)

        assert str(constraints) == str(answer)

        # assert check_equality(constraints, answer, ignore_order=True)


def test_symex_with_sym_const_and_sign():
    with Environment() as env:
        manager = env.program_manager
        executor = env.symbolic_executor
        Rule = manager.Rule
        Literal = manager.Literal
        Fact = manager.Fact
        Variable = manager.Variable
        String = manager.String
        SymbolicSign = manager.SymbolicSign
        OutputFact = manager.OutputFact
        SymbolicConstant = manager.SymbolicConstant

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

        constraints = executor.symex([rule], facts)
        print(constraints)

        # answer = {
        #     OutputFact("t", [String("b"), String("d")]): OutputCondition(
        #         [OutputSubCondition([], [Fact("s", [String("c"), String("d")])])]
        #     ),
        #     OutputFact("t", [String("a"), String("c")]): OutputCondition(
        #         [OutputSubCondition([], [Fact("r", [String("a"), String("b")])])]
        #     ),
        # }

        # assert check_equality(constraints, answer, ignore_order=True)


def test_symex_with_sym_const_sign_target_outputs():
    with Environment() as env:
        manager = env.program_manager
        executor = env.symbolic_executor
        Rule = manager.Rule
        Literal = manager.Literal
        Fact = manager.Fact
        Variable = manager.Variable
        String = manager.String
        SymbolicSign = manager.SymbolicSign
        OutputFact = manager.OutputFact
        SymbolicConstant = manager.SymbolicConstant

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

        target_outputs = {OutputFact("t", [String("a"), String("c")])}

        constraints = executor.symex([rule], facts, target_outputs)

        print(constraints)
        # answer_str = '{t("a", "c").: (and (= symlog_symbolic_1 "a") |s("c", "d").|)}'

        # assert str(constraints) == answer_str


def test_symex_with_multiple_target_outputs():
    with Environment() as env:
        manager = env.program_manager
        executor = env.symbolic_executor
        Rule = manager.Rule
        Literal = manager.Literal
        Fact = manager.Fact
        Variable = manager.Variable
        String = manager.String
        SymbolicSign = manager.SymbolicSign
        OutputFact = manager.OutputFact
        SymbolicConstant = manager.SymbolicConstant

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
            OutputFact("t", [String("a"), String("c")]),
            OutputFact("t", [String("e"), String("c")]),
        }

        constraints = executor.symex([rule], facts, target_outputs)

        print(constraints)

        # answer_str = '{t("a", "c").: (and (= symlog_symbolic_1 "a") |s("c", "d").|)}'

        # assert str(constraints) == answer_str


if __name__ == "__main__":
    test_symex_with_interested_output_facts()
    test_symex_with_sym_sign()
    test_symex_with_sym_const_and_sign()
    # test_symex_with_sym_const_sign_target_outputs()
    # test_symex_with_multiple_target_outputs()
