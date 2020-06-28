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
from utils import get_node
from copy import deepcopy as cp

class NetListHierObject(object):
    ls_pyvmodule_def = []
    ls_module_def = []
    def __init__(self, ls_pyvmodule_def):
        NetListHierObject.ls_pyvmodule_def = ls_pyvmodule_def
        return
    def _input_output__init__(self, name, lsb, msb, parent):
        assert(isinstance(name, str)), name
        assert(isinstance(lsb, int)), lsb
        assert(isinstance(msb, int)), msb
        self.name = name
        self.parent = parent
        self.width = abs(msb - lsb) + 1
        ### self.bit[?] has a list of loader/driver
        self.bit = {}
        step = 1 if msb >= lsb else -1
        for itr in range(self.width):
            self.bit[lsb + step * itr] = Bit(name, lsb + step * itr, self)
        return
    def _dct_input_output__init__(self, node, mode="input"):
        ret = {}
        PyVInputOutput = PyVInput if mode == "input" else PyVOutput
        InputOutput = Input if mode == "input" else Output
        for i in get_node(node, lambda x: isinstance(x, PyVInputOutput)):
            msb = 0 if i.width == None else int(i.width.msb.value)
            lsb = 0 if i.width == None else int(i.width.lsb.value)
            ret[i.name] = InputOutput(i.name, lsb, msb, self)
        return cp(ret)
    def _chagen_parent_inputoutput_bit(self, dct_inputoutput, parent):
        for inputoutput in dct_inputoutput.values():
            inputoutput.parent = parent
            for inputoutput_bit in inputoutput.bit.values():
                inputoutput_bit.parent = inputoutput
        return

class ModuleDef(NetListHierObject):
    def __init__(self, node):
        assert(isinstance(node, PyVModuleDef))
        self.pvnd = node
        self.name = node.name
        self.dct_input = {}
        self.dct_output = {}
        self.dct_instance = {}
        self.dct_input = self._dct_input_output__init__(node, mode="input")
        self.dct_output = self._dct_input_output__init__(node, mode="output")
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
            if self._is_output_port_estimate(p, inst):
                self.dct_output[name] = Output(name, lsb, msb, self)
            else:
                self.dct_input[name] = Input(name, lsb, msb, self)
        return
    def _is_output_port_estimate(self, p, i):
        assert (isinstance(p, PyVPortArg))
        assert (isinstance(i, PyVInstance))

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

class Instance(NetListHierObject):
    def __init__(self, node, module_def):
        assert(isinstance(node, PyVInstance))
        assert(isinstance(module_def, ModuleDef)), module_def.name
        self.pvnd = node
        self.name = node.name
        self.module_def = module_def
        self.dct_input = cp(module_def.dct_input)
        self.dct_output= cp(module_def.dct_output)
        self._chagen_parent_inputoutput_bit(self.dct_input, self)
        self._chagen_parent_inputoutput_bit(self.dct_output, self)
        return

class Input(NetListHierObject):
    def __init__(self, name, lsb, msb, parent):
        self._input_output__init__(name, lsb, msb, parent)
        return

class Output(NetListHierObject):
    def __init__(self, name, lsb, msb, parent):
        self._input_output__init__(name, lsb, msb, parent)
        return

class Bit(NetListHierObject):
    def __init__(self, name, bit, parent):
        self.name = name
        self.bit = bit
        self.wire_name = None
        self.wire_bit = None
        self.ls_loader = []
        self.ls_driver= []
        self.parent = parent
        return

