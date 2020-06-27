import sys

class ShowHierVisitor(object):
    def __init__(self, indent=2, buf=sys.stderr):
        self.indent = indent
        self.buf = buf
        return

    def visit(self, node, offset=0):
        getattr(self, 'visit_' + node.__class__.__name__)(node, offset)
        return

    def visit_ModuleDef(self, node, offset):
        self._visit_xxx(node, offset)
        """recursive call"""
        for i in node.dct_input.values():
            self.visit(i, offset + self.indent)
        for i in node.dct_output.values():
            self.visit(i, offset + self.indent)
        for i in node.dct_instance.values():
            self.visit(i, offset + self.indent)
        return

    def visit_DummyModuleDef(self, node, offset):
        self._visit_xxx(node, offset)
        """recursive call"""
        for i in node.dct_input.values():
            self.visit(i, offset + self.indent)
        for i in node.dct_output.values():
            self.visit(i, offset + self.indent)
        return

    def visit_Input(self, node, offset):
        self._visit_xxx(node, offset, attr_names=["name", "width"])
        """recursive call"""
        pass
        return

    def visit_Output(self, node, offset):
        self._visit_xxx(node, offset, attr_names=["name", "width"])
        """recursive call"""
        pass
        return

    def visit_Instance(self, node, offset):
        self._visit_xxx(node, offset)
        """recursive call"""
        for i in node.dct_input.values():
            self.visit(i, offset + self.indent)
        for i in node.dct_output.values():
            self.visit(i, offset + self.indent)
        self.visit(node.module_def, offset + self.indent)
        return

#    def visit_PortArg(self, node, offset):
#        self._visit_xxx(node, offset)
#        """recursive call"""
#        """NOTE: PortArg.show() is a Pyverilog's method"""
#        for c in node.children():
#            c.show(self.buf, offset + self.indent)
#        return

    def _visit_xxx(self, node, offset, attr_names=["name"]):
        lead = ' ' * offset
    
        self.buf.write(lead + node.__class__.__name__ + ': ')
        vlist = [getattr(node, n) for n in attr_names]
        attrstr = ', '.join('%s' % v for v in vlist)
        self.buf.write(attrstr)
    
        self.buf.write('\n')
        return
