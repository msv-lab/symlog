import common
import itertools
from pathlib import Path
import csv
from itertools import count


def write_relations(directory, relations):
    for relation_name, tuples in relations.items():
        file = Path(directory) / (relation_name + '.facts')
        with file.open(mode='w') as file:
            writer = csv.writer(file, delimiter='\t')
            for tuple in tuples:
                writer.writerow(tuple)


def load_relations(directory):
    """returns mapping from relation name to a list of tuples"""
    relations = dict()
    for file in itertools.chain(Path(directory).glob('*.facts'), Path(directory).glob('*.csv')):
        relation_name = file.stem
        with open(file) as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            relations[relation_name] = list(reader)
    return relations

def pprint(program):
    def pprint_term(term):
        if isinstance(term, common.Variable):
            return term.name
        if isinstance(term, common.String):
            return "\"" + term.value + "\""
        else:
            return str(term.value)

    def pprint_literal(l):
        literal_result = ""
        if not l.positive:
            literal_result += "!"
        args_result = ", ".join([pprint_term(t) for t in l.args])
        literal_result += f"{l.name}({args_result})"
        return literal_result
        
    def pprint_unification(u):
        op = "=" if u.positive else "!="
        return f"{u.left} {op} {u.right}"
    
    result = ""

    for (name, types) in program.declarations.items():
        result += f".decl {name}("
        types_results = [f"v{i}:{t}" for i, t in enumerate(types)] 
        result += ", ".join(types_results) + ")\n"

    for name in program.inputs:
        result += f".input {name}\n"

    for name in program.outputs:
        result += f".output {name}\n"
        
    for rule in program.rules:
        result += pprint_literal(rule.head)
        if rule.body:
            result += " :- "
        body_results = []
        for el in rule.body:
            if isinstance(el, common.Unification):
                body_results.append(pprint_unification(el))
            else:
                body_results.append(pprint_literal(el))
        result += ", ".join(body_results) + ".\n"

    return result

current_id = count()
def get_id():
    next(current_id)
    return current_id