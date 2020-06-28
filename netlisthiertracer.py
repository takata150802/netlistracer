from pyverilog.vparser.ast import  Node as PyVNode
from pyverilog.vparser.ast import  Source as PyVSource
from pyverilog.vparser.ast import  Node as PyVNode
from pyverilog.vparser.ast import  ModuleDef as PyVModuleDef
from pyverilog.vparser.ast import  Instance as PyVInstance
from pyverilog.vparser.ast import  Input as PyVInput
from pyverilog.vparser.ast import  Output as PyVOutput
from pyverilog.vparser.ast import  PortArg as PyVPortArg
from pyverilog.vparser.ast import  Identifier as PyVIdentifier
from pyverilog.vparser.ast import  Partselect as PyVPartselect
from pyverilog.vparser.ast import  IntConst as PyVIntConst
from utils import hasattr_parents
from utils import get_node
import sys
from showhiervisitor import ShowHierVisitor
from netlisthiertracevisitor import NetListHierTraceVisitor

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

class NetListHierObject(object):
    ls_pyvmodule_def = []
    ls_module_def = []
    def __init__(self, ls_pyvmodule_def):
        NetListHierObject.ls_pyvmodule_def = ls_pyvmodule_def
        return
    def _input_output__init__(self, name, lsb, msb):
        assert(isinstance(name, str)), name
        assert(isinstance(lsb, int)), lsb
        assert(isinstance(msb, int)), msb
        self.name = name
        self.width = abs(msb - lsb) + 1
        ### self.bit[?] has a list of loader/driver
        self.bit = {}
        step = 1 if msb >= lsb else -1
        for itr in range(self.width):
            self.bit[lsb + step * itr] = Bit()
        return

class ModuleDef(NetListHierObject):
    def __init__(self, node):
        assert(isinstance(node, PyVModuleDef))
        self.pvnd = node
        self.name = node.name
        self.dct_input = {}
        self.dct_output = {}
        self.dct_instance = {}
        for i in get_node(node, lambda x: isinstance(x, PyVInput)):
            msb = 0 if i.width == None else int(i.width.msb.value)
            lsb = 0 if i.width == None else int(i.width.lsb.value)
            self.dct_input[i.name] = Input(i.name, lsb, msb)
        for i in get_node(node, lambda x: isinstance(x, PyVOutput)):
            msb = 0 if i.width == None else int(i.width.msb.value)
            lsb = 0 if i.width == None else int(i.width.lsb.value)
            self.dct_output[i.name] = Output(i.name, lsb, msb)
        for i in get_node(node, lambda x: isinstance(x, PyVInstance)):
            module_def = self.get_module_def(i)
            if module_def is None:
                module_def = self.create_dummy_module_def(i)
            self.dct_instance[i.name] = Instance(i, module_def)
        return

    def get_module_def(self, inst):
        assert (isinstance(inst, PyVInstance))
        emsg = "\n" \
             + "multiple declear of module `" + str(inst.module) + "` is detected.\n"
        """module_def is already created"""
        ls_module = NetListHierObject.ls_module_def
        ll = [i for i in ls_module if isinstance(i, ModuleDef) and i.name == inst.module]
        assert (len(ll) == 1 or len(ll) == 0), emsg
        if len(ll) == 1:
            return ll[0]

        """module_def is NOT created yet or not found"""
        ls_module = NetListHierObject.ls_pyvmodule_def
        ll = [i for i in ls_module if isinstance(i, PyVModuleDef) and i.name == inst.module]
        assert (len(ll) == 1 or len(ll) == 0), emsg
        if len(ll) == 1:
            m = ModuleDef(ll[0])
            NetListHierObject.ls_module_def.append(m)
            return m
        else :
            return None

    def create_dummy_module_def(self, inst):
        module_def = DummyModuleDef(inst)
        NetListHierObject.ls_module_def.append(module_def)
        return module_def

class DummyModuleDef(ModuleDef):
    def __init__(self, inst):
        assert(isinstance(inst, PyVInstance))
        self.pvnd = None
        self.name = inst.module
        self.dct_input = {}
        self.dct_output = {}
        self.dct_instance = {}
        ls_port = get_node(inst, lambda x: isinstance(x, PyVPortArg))
        for p in ls_port:
            name = p.portname
            lsb = msb = 0
            self.dct_input[name] = Input(name, lsb, msb)
            self.dct_output[name] = Output(name, lsb, msb)
        return

from copy import deepcopy as cp
class Instance(NetListHierObject):
    def __init__(self, node, module_def):
        assert(isinstance(node, PyVInstance))
        assert(isinstance(module_def, ModuleDef)), module_def.name
        self.pvnd = node
        self.name = node.name
        self.module_def = module_def
        self.dct_input = cp(module_def.dct_input)
        self.dct_output= cp(module_def.dct_output)
        self.dct_input_arg = {}
        self.dct_output_arg = {}
        return

class Input(NetListHierObject):
    def __init__(self, name, lsb, msb):
        self._input_output__init__(name, lsb, msb)
        return

class Output(NetListHierObject):
    def __init__(self, name, lsb, msb):
        self._input_output__init__(name, lsb, msb)
        return

class Bit(NetListHierObject):
    def __init__(self):
        self.wire_name = None
        self.wire_bit = None
        self.ls_loder = []
        self.ls_dirver = []
        return
