# Install

## Souffle
Install Souffle by the following commands:
```bash
wget -P /tmp https://github.com/souffle-lang/souffle/releases/download/2.2/x86_64-ubuntu-2104-souffle-2.2-Linux.deb
sudo dpkg -i /tmp/x86_64-ubuntu-2104-souffle-2.2-Linux.deb
sudo apt-get install -f
rm /tmp/x86_64-ubuntu-2104-souffle-2.2-Linux.deb
```

## Conda
Follow the instructions on the [official website](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html).


## Setup Python Environment
Create a conda environment with Python 3.10:
```bash
conda create --name myenv python=3.10
conda activate myenv
```

Install the project's dependencies:
```bash
pip install -r requirements.txt
pip install -e .
```

Note, all python dependencies are installed in `myenv`. If you want to use the project in another environment, you need to install the dependencies again.


# API Usage Example

```Python
from symlog.shortcuts import (
    SymbolicConstant,
    String,
    Literal,
    Variable,
    Rule,
    Fact,
    SymbolicSign,
    symex,
)
from symlog.souffle import SYM

# the reachability rules
edge_relation1 = Literal(
    "edge", [Variable("x"), Variable("y")]
)  # default sign is positive
reachable_relation1 = Literal("reachable", [Variable("x"), Variable("y")])

edge_relation2 = Literal("edge", [Variable("x"), Variable("y")])
reachable_relation2 = Literal("reachable", [Variable("x"), Variable("z")])
reachable_relation3 = Literal("reachable", [Variable("y"), Variable("z")])

rules = [
    Rule(reachable_relation1, [edge_relation1]),  # reachable(x, y) :- edge(x, y).
    Rule(
        reachable_relation2, [edge_relation2, reachable_relation3]
    ),  # reachable(x, z) :- edge(x, y), reachable(y, z).
]

# the edge facts
edge_fact1 = SymbolicSign(
    Fact("edge", [SymbolicConstant("alpha", type=SYM), String("b")])
)
edge_fact2 = SymbolicSign(Fact("edge", [String("b"), String("c")]))  # edge('b', 'c').
edge_fact3 = Fact("edge", [String("c"), String("b")])  # edge('c', 'b').
edge_fact4 = Fact("edge", [String("c"), String("d")])  # edge('c', 'd').

facts = [edge_fact1, edge_fact2, edge_fact3, edge_fact4]

interested_fact = Fact("reachable", [String("a"), String("b")])

# get constraints
constraints = symex(rules, facts, {interested_fact})

print(constraints)

# {reachable("a", "b").: And(alpha == "a", edge("a", "b").)}

```

