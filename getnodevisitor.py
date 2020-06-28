from pyverilog.vparser.ast import Node

class GetNodeVisitor(object):
    def __init__(self, fn, debug=False):
        self.fn = fn
        self.ret= []
        return

    def visit(self, node):
        assert(isinstance(node, Node)), node
        ### getattr(self, 'visit_' + node.__class__.__name__)(node, offset)
        self._visit_xxx(node)
        self._visit_xxx_recursive_call(node)
        return

    def _visit_xxx(self, node):
        if (self.fn(node)):
            self.ret.append(node)
        return

    def _visit_xxx_recursive_call(self, node):
        for c in node.children():
            self.visit(c)
        return

    def get_result(self):
        ### WANING: THIS IS NOT DEEP COPY
        from copy import copy as cp
        ret = cp(self.ret)
        self.ret = []
        return ret
