from objects import List, Dict
import simple_ast

# Doesn't work because some of the recursive calls create lists
# Namely, ["testlist", "listmaker", "exprlist"] from unpack_assign!
def listmaker(*values):
    if len(values) > 0 and values[0].name == "listcomp":
        result = List()
        result.append(evaluate(values[0]))
        return result
    result = List()
    for value in values:
        result.append(evaluate(value))
    return result

simple_ast.listmaker = listmaker
