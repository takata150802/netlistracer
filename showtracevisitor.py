import sys

class BaseTraceVisitor(object):
    def __init__(visitor):
        pass
        return

    def visit(visitor, node):
        return getattr(visitor, 'visit_' + node.__class__.__name__)(node)

    def visit_ModuleDef(visitor, node):
        """recursive call"""
        for i in node.dct_instance.values():
            visitor.visit(i)
        return

    def visit_DummyModuleDef(visitor, node):
        pass
        return

    def visit_Instance(visitor, node):
        """recursive call"""
        visitor.visit(node.module_def)
        return

from pyverilog.vparser.ast import  PortArg as PyVPortArg
from pyverilog.vparser.ast import  ModuleDef as PyVModuleDef
from pyverilog.vparser.ast import  Instance as PyVInstance
from pyverilog.vparser.ast import  ModuleDef as PyVModuleDef
from pyverilog.vparser.ast import  Identifier as PyVIdentifier
from pyverilog.vparser.ast import  Partselect as PyVPartselect
from pyverilog.vparser.ast import  IntConst as PyVIntConst
from pyverilog.vparser.ast import  Concat as PyVConcat
from pyverilog.vparser.ast import  Pointer as PyVPoiner
from netlisthierobject import ModuleDef
from netlisthierobject import DummyModuleDef
from netlisthierobject import Instance
from netlisthierobject import Input
from netlisthierobject import Output

from copy import deepcopy as cp

class ShowTraceVisitor(BaseTraceVisitor):
    def __init__(visitor):
        visitor.trace_result= []
        return
    def show(visitor):
        for i in visitor.trace_result:
            i.show()
        return

    def visit_trace(visitor, node, tracing_path):
        return getattr(visitor, 'visit_' + node.__class__.__name__)(node, tracing_path)

    def visit_ModuleDef(visitor, node):
        for module_input in node.dct_input.values():
            for module_input_bit in module_input.bit.values():
                tracing_path = TracingPath(node, module_input_bit)
                visitor.visit_trace(module_input_bit, tracing_path)
        return

    def visit_Bit(visitor, node, tracing_path):
        ## debug ### tracing_path.show()
        if len(node.ls_loader) == 0:
           visitor.trace_result.append(cp(tracing_path))
           return
        """
        [1] ModuleDef.input -> Instance.input
        [2] Instance.output -> Instance.input
        [3] DummyModuleDef.input -> DummyModuleDef.output -> Instance.output
        [4] Instance.output -> ModuleDef.output -> Instance.output
        [5] Instance.output -> ModuleDef.output(top_module)
        """
        for module_input_bit_loader in node.ls_loader:
            src_mod_inst = node.parent.parent
            src_input_output = node.parent
            dst_mod_inst = module_input_bit_loader.parent.parent
            dst_input_output = module_input_bit_loader.parent
            if isinstance(src_mod_inst, ModuleDef) and \
               isinstance(src_input_output, Input) and \
               isinstance(dst_mod_inst, Instance) and \
               isinstance(dst_input_output, Input):
                tracing_path2 = tracing_path.fork_path()
                tracing_path2.push_hier(dst_mod_inst)
                tracing_path2.append_trace(module_input_bit_loader)
                name = module_input_bit_loader.name
                bit  = module_input_bit_loader.bit
                loader = dst_mod_inst.module_def.dct_input[name].bit[bit]
                visitor.visit_trace(loader, tracing_path2)
            elif isinstance(src_mod_inst, Instance) and \
               isinstance(src_input_output, Output) and \
               isinstance(dst_mod_inst, Instance) and \
               isinstance(dst_input_output, Input):
                tracing_path2 = tracing_path.fork_path()
                tracing_path2.pop_hier()
                tracing_path2.push_hier(dst_mod_inst)
                tracing_path2.append_trace(module_input_bit_loader)
                name = module_input_bit_loader.name
                bit  = module_input_bit_loader.bit
                loader = dst_mod_inst.module_def.dct_input[name].bit[bit]
                visitor.visit_trace(loader, tracing_path2)
            elif isinstance(src_mod_inst, DummyModuleDef) and \
               isinstance(src_input_output, Input) and \
               isinstance(dst_mod_inst, DummyModuleDef) and \
               isinstance(dst_input_output, Output):
                tracing_path2 = tracing_path.fork_path()
                inst = tracing_path2.get_currnet_hier()
                name = module_input_bit_loader.name
                bit = module_input_bit_loader.bit
                loader = inst.dct_output[name].bit[bit]
                tracing_path2.append_trace(loader)
                visitor.visit_trace(loader, tracing_path2)
            elif isinstance(src_mod_inst, Instance) and \
               isinstance(src_input_output, Output) and \
               isinstance(dst_mod_inst, ModuleDef) and \
               isinstance(dst_input_output, Output):
                if tracing_path.is_top_hier():
                    tracing_path.append_trace(module_input_bit_loader)
                    visitor.trace_result.append(cp(tracing_path))
                    continue
                tracing_path2 = tracing_path.fork_path()
                tracing_path2.pop_hier()
                inst = tracing_path2.get_currnet_hier()
                name = module_input_bit_loader.name
                bit  = module_input_bit_loader.bit
                loader = inst.dct_output[name].bit[bit]
                tracing_path2.append_trace(loader)
                visitor.visit_trace(loader, tracing_path2)
            else:
                assert False

class TracingPath(object):
    def __init__(self, top_module, bit):
        self.trace = [{"hier": [top_module], "bit": bit}] ### [{"hier": [class ModuleDef, class Instance, class Instance,...], "bit": class Bit}]
        self.hier = [top_module] ### [class ModuleDef, class Instance, class Instance,...]
        self.top_module = top_module
        return
    def show(self):
        print ("<<<<<")
        for t in self.trace:
            h = t["hier"]
            for inst in h:
                if isinstance(inst.pvnd, PyVInstance):
                    inst_name = inst.name
                    module_name = inst.module_def.name
                    print("%s(%s)/"%(inst_name, module_name), end="")
                elif isinstance(inst.pvnd, PyVModuleDef):
                    inst_name = ""
                    module_name = inst.name
                    print("top_module(%s)/"%(module_name), end="")
                else:
                    assert False
            bit = t["bit"]
            port_name = bit.name
            port_bit = bit.bit
            print ("%s[%d]"%(port_name, port_bit))
        print (">>>>>")
        return
    def push_hier(self, inst):
        self.hier.append(inst)
    def pop_hier(self):
        self.hier.pop()
        return
    def append_trace(self, bit):
        d = {"hier" : cp(self.hier),
             "bit"  : bit}
        self.trace.append(d)
    def fork_path(self):
        return cp(self)
    def is_top_hier(self):
        return self.hier == [self.top_module]
    def get_currnet_hier(self):
        return self.hier[-1]
