import objects
list = objects.List

def simple_wrap_tree(root):
    if type(root).__name__ != "list":
        return root
    return Node(root[0], [simple_wrap_tree(c) for c in root[1:]])

class MatchError(objects.object):
    pass

class Node(objects.List):
    def __pinit__(self, name=None, value=None, params=None):
        objects.List.__pinit__(self, value if value is not None else [])
        self.name = name
        self.params = params if params is not None else {}
        kw = {}
        for key, value in kw.items():
            setattr(self, key, value)

    def __repr__(self):
        return "%s%s" % (self.name, objects.List.__repr__(self))

    def pprint(self, indent=0):
        print " "*indent + self.name
        for child in self:
            if type(child).__name__ != "Instance":
                print " "*(indent + 1), type(child).__name__, repr(child)
            else:
                child.pprint(indent + 2)

