# Symlog

Symlog is a symbolic executor of Datalog programs. It computes dependencies between the input and the output of a query by executing the query on a symbolic database. Please check more details in our publication:

[Program Repair Guided by Datalog-Defined Static Analysis](https://mechtaev.com/files/fse23.pdf)<br>
Liu Yu, Sergey Mechtaev, Pavle Subotic, Abhik Roychoudhury<br>
FSE 2023


## Installation

**Setting up Souffle**.
To install Souffle, execute the following commands in the terminal:

```bash
wget -P /tmp https://github.com/souffle-lang/souffle/releases/download/2.2/x86_64-ubuntu-2104-souffle-2.2-Linux.deb
sudo dpkg -i /tmp/x86_64-ubuntu-2104-souffle-2.2-Linux.deb
sudo apt-get install -f
rm /tmp/x86_64-ubuntu-2104-souffle-2.2-Linux.deb
```


**Setting up Python Environment**.
First, ensure you have virtualenv installed. If not, you can install it using pip:

```bash
pip install virtualenv
```

Create and activate a virtual environment with Python 3.10:

```bash
virtualenv myenv --python=python3.10
source myenv/bin/activate
```

Install the required dependencies within the environment:

```bash
pip install -r requirements.txt
pip install -e .
```

*Note*: All Python dependencies are localized to the `myenv` environment. If you work in a different one, you will need to reinstall the dependencies.

To deactivate the virtual environment:
    
```bash
deactivate
```

## Docker Image
To build the image:
```bash
sudo docker build -t symlog . 
```
To run the container:
```bash
sudo docker run -it symlog
```

## Usage Example
**Creating Datalog Rules and Facts in Python**

Use the following Python script to define Datalog rules and facts:

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

**Loading Datalog Rules and Facts from Files**

Alternatively, Datalog rules and facts can be loaded from file sources:

```Python
from symlog.shortcuts import (
    SymbolicConstant,
    String,
    Fact,
    SymbolicSign,
    symex,
    load_facts,
    parse,
    substitute,
)
from symlog.souffle import SYM

# the reachability rules
rules = parse("example/reachability.dl")

# the edge facts
facts = load_facts("example/", rules.declarations)

alpha = SymbolicConstant("alpha")

facts = set(
    map(lambda fact: SymbolicSign(substitute(fact, {String("a"): alpha})), facts)
)

facts = {SymbolicSign(f) if str(f) == 'edge("b", "c").' else f for f in facts}

interested_fact = Fact("reachable", [String("a"), String("b")])

# get constraints
constraints = symex(rules, facts, {interested_fact})

print(constraints)

# {reachable("a", "b").: And(alpha == "a", edge("a", "b").)}
```

## Patches
Generated patches: https://drive.google.com/file/d/1PY6AY_jrVVVQuCFg9bpwdPNM5AOlqMw1/view?usp=drive_link

## Limitations
1. Symlog supports only basic Souffle syntax. Features such as aggregation, arithmetic operations, and components are not supported.
2. Currently, Symlog supports only positive Datalog. If you wish to use semi-positive Datalog, you must first convert it to positive Datalog, if possible. Support for stratified negation will be added in the future.

## Acknowledgements
This work was partially supported by a Singapore Ministry of Education (MoE) Tier 3 grant “Automated Program Repair”, MOE-MOET32021-0001, and by a gift from Oracle.
