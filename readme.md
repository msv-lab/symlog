
# API Usage Example

```Python
from symlog.shortcuts import (
    SymbolicConstant,
    Number,
    String,
    Literal,
    Variable,
    Rule,
    Fact,
    SymbolicSign,
    repair,
    substitue_fact_const,
    symex   
)

from symlog.souffle import NUM, SYM

# the reachability rules
edge_relation1 = Literal(
    "edge", [Variable("x"), Variable("y")]
)  # default sign is positive
reachable_relation1 = Literal("reachable", [Variable("x"), Variable("y")])

edge_relation2 = Literal("edge", [Variable("x"), Variable("y")])
reachable_relation2 = Literal("reachable", [Variable("x"), Variable("z")])
reachable_relation3 = Literal("reachable", [Variable("y"), Variable("z")])

rules = [
    Rule(reachable_relation1, [edge_relation1]), # reachable(x, y) :- edge(x, y).
    Rule(reachable_relation2, [edge_relation2, reachable_relation3]), # reachable(x, z) :- edge(x, y), reachable(y, z).
]

# alternatively, rules can be loaded from a file
rules = parse('path/to/reachability/rules/file')

# the edge facts
edge_fact1 = Fact("edge", [String("a"), String("b")]) # edge('a', 'b').
edge_fact2 = Fact("edge", [String("b"), String("c")]) # edge('b', 'c').
edge_fact3 = Fact("edge", [String("c"), String("b")]) # edge('c', 'b').
edge_fact4 = Fact("edge", [String("c"), String("d")]) # edge('c', 'd').

facts = [edge_fact1, edge_fact2, edge_fact3, edge_fact4]

# alternatively, facts can be loaded from disk
facts = load_facts('/path/to/edge/facts/')

# create a symbolic constant
const_a = String("a")
sym_const = SymbolicConstant() # default type is 'symbol'

substitue_fact_const(facts, {const_a: sym_const})  # substitue all const_a with sym_const

# set symbolic sign
edge_fact1 = SymbolicSign(edge_fact1)
edge_fact2 = SymbolicSign(edge_fact2)

# update facts
facts = [edge_fact1, edge_fact2, edge_fact3, edge_fact4]

# get constraints of symbolic execution of datalog
constraints = symex(rules, facts)

print(constraints)


# tuples want to be generated
wanted_tuples = [Fact("reachable", [String("e"), String("d")])] # [reachable('e', 'd')]

raw_patches = repair(rules, facts, wanted_tuples)  # The 3rd argument, unwanted_tuples, defaults to []

```

