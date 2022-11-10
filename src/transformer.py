import common

def transform(node, f):

    def transform_inner(node, f):
        if isinstance(node, common.Variable) or \
           isinstance(node, common.String) or \
           isinstance(node, common.Number):
            return transform_term(node, f)
        if isinstance(node, common.Unification):
            return transform_unification(node, f)
        if isinstance(node, common.Literal):
            return transform_literal(node, f)
        if isinstance(node, common.Rule):
            return transform_rule(node, f)
        if isinstance(node, common.Program):
            return transform_program(node, f)
    
    def transform_term(t, f):
        return f(t)
    
    def transform_unification(u, f):
        return f(common.Unification(transform_term(u.left, f),
                             transform_term(u.right, f),
                             u.positive))
    
    def transform_literal(l, f):
        return f(common.Literal(l.name,
                         [transform_term(t, f) for t in l.args],
                         l.positive))

    def transform_rule(rule, f):
        return f(common.Rule(transform_literal(rule.head, f),
                      [transform_inner(n, f) for n in rule.body]))

    def transform_program(program, f):
        return f(common.Program(program.declarations,
                         program.inputs,
                         program.outputs,
                         [transform_rule(r, f) for r in program.rules]))
    
    return transform_inner(node, f)

