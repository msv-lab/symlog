import common

def collect(node, p):
    result = []

    def collect_inner(node, p):
        if isinstance(node, common.Variable) or \
           isinstance(node, common.String) or \
           isinstance(node, common.Number):
            collect_term(node, p)
        if isinstance(node, common.Unification):
            collect_unification(node, p)
        if isinstance(node, common.Literal):
            collect_literal(node, p)
        if isinstance(node, common.Rule):
            collect_rule(node, p)
        if isinstance(node, common.Program):
            collect_program(node, p)

    def collect_term(t, p):
        if p(t):
            result.append(t)
    
    def collect_unification(unification, p):
        collect_term(unification.left, p)
        collect_term(unification.right, p)
        if p(unification):
            result.append(unification)
    
    def collect_literal(literal, p):
        for a in literal.args:
            collect_term(a, p)
        if p(literal):
            result.append(literal)

    def collect_rule(rule, p):
        for el in rule.body:
            collect_inner(el, p)
        if p(rule):
            result.append(rule)

    def collect_program(program, p):
        for r in program.rules:
            collect_rule(r, p)
        if p(program):
            result.append(program)

    collect_inner(node, p)
    return result