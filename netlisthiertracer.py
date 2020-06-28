from pyverilog.vparser.ast import  Source as PyVSource
from pyverilog.vparser.ast import  Node as PyVNode
from pyverilog.vparser.ast import  ModuleDef as PyVModuleDef
from pyverilog.vparser.ast import  PortArg as PyVPortArg
from utils import hasattr_parents
from utils import get_node
import sys
from showhiervisitor import ShowHierVisitor
from netlisthiertracevisitor import NetListHierTraceVisitor
from showtracevisitor import ShowTraceVisitor
from netlisthierobject import NetListHierObject
from netlisthierobject import ModuleDef

class NetListHier(object):
    def __init__(self, ast, top_module_name=False):
        assert(isinstance(ast, PyVSource))
        self.ast = ast

        ### [1] List of PyVModuleDef(s)
        ls_pyvmodule_def = get_node(self.ast, lambda x: isinstance(x, PyVModuleDef))
        _ = NetListHierObject(ls_pyvmodule_def)
        ### [2] top_module
        if top_module_name == False:
            top_module= ls_pyvmodule_def[0]
        else:
            emsg_multi_dec= "\n" \
                + "multiple declear of module `" + top_module_name + "` is detected.\n"
            emsg_dec_not_found = "\n" \
                + "the declear of module `" + top_module_name + "` is NOT found.\n"
            ll = [i for i in ls_pyvmodule_def if i.name == top_module_name]
            assert (len(ll) != 0), emsg_dec_not_found
            assert (len(ll) < 2), emsg_multi_dec
            top_module = self.ls_pyvmodule_def[0]
        ### [3] create Module Hier
        self.top_module = ModuleDef(top_module)
        return

    def show_hier(self, buf=sys.stderr, offset=0, showlineno=True):
        visitor = ShowHierVisitor()
        visitor.visit(self.top_module, offset=offset)
        return

    def trace(self):
        visitor = NetListHierTraceVisitor()
        visitor.visit(self.top_module)
        return

    def show_trace(self):
        visitor = ShowTraceVisitor()
        visitor.visit(self.top_module)
        visitor.show()
        return
