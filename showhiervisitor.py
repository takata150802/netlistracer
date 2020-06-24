import sys
from pyverilog.vparser.ast import Node

class ShowHierVisitor(object):
    def __init__(self, indent=2, buf=sys.stderr, attrnames=False, showlineno=True):
        self.indent = indent
        self.buf = buf
        self.attrnames = attrnames
        self.showlineno = showlineno
        return

    def visit(self, node, offset=0):
        assert(isinstance(node, Node))
        getattr(self, 'visit_' + node.__class__.__name__)(node, offset)
        return

    def visit_ModuleDef(self, node, offset):
        self._visit_xxx(node, offset)
        """recursive call"""
        for i in node.ls_input:
            self.visit(i, offset + self.indent)
        for i in node.ls_output:
            self.visit(i, offset + self.indent)
        for i in node.ls_instance:
            self.visit(i, offset + self.indent)
        return

    def visit_Input(self, node, offset):
        self._visit_xxx(node, offset)
        """recursive call"""
        pass
        return

    def visit_Output(self, node, offset):
        self._visit_xxx(node, offset)
        """recursive call"""
        pass
        return

    def visit_Instance(self, node, offset):
        self._visit_xxx(node, offset)
        """recursive call"""
        for i in node.ls_port:
            self.visit(i, offset + self.indent)
        if node.module_def is not None:
            self.visit(node.module_def, offset + self.indent)
        return

    def visit_PortArg(self, node, offset):
        self._visit_xxx(node, offset)
        """recursive call"""
        """NOTE: PortArg.show() is a Pyverilog's method"""
        for c in node.children():
            c.show(self.buf, offset + self.indent, self.attrnames, self.showlineno)
        return

    def _visit_xxx(self, node, offset):
        lead = ' ' * offset
    
        self.buf.write(lead + node.__class__.__name__ + ': ')
    
        if node.attr_names:
            if self.attrnames:
                nvlist = [(n, getattr(node, n)) for n in node.attr_names]
                attrstr = ', '.join('%s=%s' % (n, v) for (n, v) in nvlist)
            else:
                vlist = [getattr(node, n) for n in node.attr_names]
                attrstr = ', '.join('%s' % v for v in vlist)
            self.buf.write(attrstr)
    
        if self.showlineno:
            self.buf.write(' (at %s)' % node.lineno)
    
        self.buf.write('\n')
        return
