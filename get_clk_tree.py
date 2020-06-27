from __future__ import absolute_import
from __future__ import print_function
import sys
import os
from optparse import OptionParser

# the next line can be removed after installation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyverilog.utils.version
from pyverilog.vparser.parser import parse

from pyverilog.vparser.ast import Source
from pyverilog.vparser.ast import Node
from pyverilog.vparser.ast import ModuleDef
from pyverilog.vparser.ast import Instance
from pyverilog.vparser.ast import Input
from pyverilog.vparser.ast import Output
from pyverilog.vparser.ast import PortArg
from pyverilog.vparser.ast import Identifier
from pyverilog.vparser.ast import Partselect
from pyverilog.vparser.ast import IntConst
from getnodevisitor import GetNodeVisitor
from showhiervisitor import ShowHierVisitor
from netlisttracevisitor import ModuleNetTraceVisitor

def debug(x):
    print(x, file=sys.stderr, end=' ')
    return

class NetlistHier(object):
    dev_null = open(os.devnull, 'w')
    def __init__(self, ast):
        assert(isinstance(ast, Source))
        self.ast = ast
        self._get_hier()

    def _get_hier(self):
        self.ls_module = self.get_node(self.ast, lambda x: isinstance(x, ModuleDef))
        self.top_module = self.ls_module[0]
        self._get_hier_module_def(self.top_module)

    def _get_hier_module_def(self, module_def):
        assert(isinstance(module_def, ModuleDef))
        module_def.ls_input = self.get_node(module_def, lambda x: isinstance(x, Input))
        module_def.ls_output = self.get_node(module_def, lambda x: isinstance(x, Output))
        module_def.ls_instance = self.get_node(module_def, lambda x: isinstance(x, Instance))
        for i in module_def.ls_instance:
            i.ls_port = []
            i.ls_port = self.get_node(i, lambda x: isinstance(x, PortArg))
            i.module_def = self.get_module_def(i)
            if i.module_def is None:
                i.module_def = self._create_dummy_module_def(i)
            else:
                self._get_hier_module_def(i.module_def)
        return

    def get_module_def(self, inst):
        assert (isinstance(inst, Instance))
        emsg = "\n" \
             + "multiple declear of module `" + str(inst.module) + "` is detected.\n" \
             + "but this check is NOT enough 'cause of TOP module multiple declear.\n"
        ll = [i for i in self.ls_module if isinstance(i, ModuleDef) and i.name == inst.module]
        assert (len(ll) == 1 or len(ll) == 0), emsg
        if len(ll) == 1:
            return ll[0]
        else :
            return None

    def _create_dummy_module_def(self, inst):
        assert (isinstance(inst, Instance))
        ret = ModuleDef(name=inst.module,
                        paramlist=None,
                        portlist=None,
                        items=None,
                        default_nettype='wire', lineno=-1)
        ret.ls_input = []
        ret.ls_output = []
        ret.ls_instance = []
        for p in inst.ls_port:
            if self._is_output_port_estimate(p, inst):
                ret.ls_output.append(Output(name=p.portname,
                                           width=None, 
                                           signed=False,
                                           dimensions=None,
                                           lineno=-1))
            else:
                ret.ls_input.append(Input(name=p.portname,
                                           width=None, 
                                           signed=False,
                                           dimensions=None,
                                           lineno=-1))
        ret.is_dummy_module_def = True
        return ret
     
    def _is_output_port_estimate(self, p, i):
        assert (isinstance(p, PortArg))
        assert (isinstance(i, Instance))

        """pがoutput_portだと推測できる条件"""
        portname = p.portname
        modulename = i.module
        if modulename == "dummy" and portname[0:2] == 'out':
            return True
        if portname[0] == 'o':
            return True
        if portname[0] == 'q':
            return True
        return False

    def get_node(self, node, fn):
        visitor = GetNodeVisitor(fn)
        visitor.visit(node)
        return visitor.get_result()


    def show_hier(self, buf=sys.stderr, offset=0, showlineno=True):
        visitor = ShowHierVisitor()
        visitor.visit(self.top_module, offset=0)
        return

    def trace(self):
        visitor = ModuleNetTraceVisitor()
        visitor.visit(self.top_module)
        return

def hasattr_parents(obj, attrs):
    assert (isinstance(attrs, str))
    ls_attr = attrs.split('.')
    for attr in ls_attr:
        if hasattr(obj, attr):
            obj = getattr(obj, attr)
        else:
            return False
    return True

def main():
    INFO = "Verilog code parser"
    VERSION = pyverilog.utils.version.VERSION
    USAGE = "Usage: python example_parser.py file ..."

    def showVersion():
        print(INFO)
        print(VERSION)
        print(USAGE)
        sys.exit()

    optparser = OptionParser()
    optparser.add_option("-v","--version",action="store_true",dest="showversion",
                         default=False,help="Show the version")
    optparser.add_option("-I","--include",dest="include",action="append",
                         default=[],help="Include path")
    optparser.add_option("-D",dest="define",action="append",
                         default=[],help="Macro Definition")
    (options, args) = optparser.parse_args()

    filelist = args
    if options.showversion:
        showVersion()

    for f in filelist:
        if not os.path.exists(f): raise IOError("file not found: " + f)

    if len(filelist) == 0:
        showVersion()

    ast, directives = parse(filelist,
                            preprocess_include=options.include,
                            preprocess_define=options.define)
    netlist_hier =  NetlistHier(ast)
    netlist_hier.show_hier()
    netlist_hier.trace()


if __name__ == '__main__':
    main()
