def hasattr_parents(obj, attrs):
    assert (isinstance(attrs, str))
    ls_attr = attrs.split('.')
    for attr in ls_attr:
        if hasattr(obj, attr):
            obj = getattr(obj, attr)
        else:
            return False
    return True

from getnodevisitor import GetNodeVisitor
def get_node(node, fn):
    visitor = GetNodeVisitor(fn)
    visitor.visit(node)
    return visitor.get_result()
