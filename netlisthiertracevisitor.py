import sys

class NetListHierTraceVisitor(object):
    def __init__(visitor):
        pass
        return
    def visit(visitor, node):
        visitor1st = InstanceGetPortArgWireVisitor()
        visitor2nd = DummyModuleDefTraceVisitor()
        visitor3rd = ModuleOutputTraceVisitor()
        visitor4th = SubModuleInputTraceVisitor()
        visitor1st.visit(node)
        visitor2nd.visit(node)
        visitor3rd.visit(node)
        visitor4th.visit(node)
        return

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
from pyverilog.vparser.ast import  Identifier as PyVIdentifier
from pyverilog.vparser.ast import  Partselect as PyVPartselect
from pyverilog.vparser.ast import  IntConst as PyVIntConst
from pyverilog.vparser.ast import  Concat as PyVConcat
from pyverilog.vparser.ast import  Pointer as PyVPoiner
from copy import deepcopy as cp
class InstanceGetPortArgWireVisitor(BaseTraceVisitor):

    def visit_Instance(visitor, node):
        pyveri_inst = node.pvnd
        for p in pyveri_inst.portlist:
            dct_wire_name_bit = visitor.visit(p)
            portname = p.portname
            if portname in node.dct_input:
                dct_xxx = node.dct_input
            elif portname in node.dct_output:
                dct_xxx = node.dct_output
            else:
                continue
            for i in range(len(dct_wire_name_bit)):
                dst = dct_xxx[portname].bit[i]
                src = dct_wire_name_bit[i]
                dst.wire_name = src["name"]
                dst.wire_bit  = src["bit"]
        """recursive call"""
        visitor.visit(node.module_def)
        return

    def visit_PortArg(visitor, node):
        assert(isinstance(node, PyVPortArg))
        portname = node.portname
        visitor.cnt_found_bit = 0
        visitor.dct_wire_name_bit = {}

        if isinstance(node.argname, PyVConcat):
            visitor.visit(node.argname)
        if isinstance(node.argname, PyVPartselect):
            visitor.visit(node.argname)
        if isinstance(node.argname, PyVPoiner):
            visitor.visit(node.argname)
        if isinstance(node.argname, PyVIdentifier):
            visitor.visit(node.argname)
        if node.argname == None:
            visitor.visit(node.argname)

        ret = {}
        for i in range(visitor.cnt_found_bit):
            j = (visitor.cnt_found_bit - 1) - i
            ret[i] = cp(visitor.dct_wire_name_bit[j])
        visitor.cnt_found_bit = 0
        visitor.dct_wire_name_bit = {}
        return ret
        
    def visit_Concat(visitor, node):
        assert(isinstance(node, PyVConcat))
        """NOTE: node.list[0]から順にMSB側から並んでいるので、
                 visit_PortArg()return時にLSB側になるよう逆順にする
        """
        for i in node.list:
            visitor.visit(i)
        return

    def visit_Partselect(visitor, node):
        assert(isinstance(node, PyVPartselect))
        lsb = int(node.lsb.value)
        msb = int(node.msb.value)
        wire_name = node.var
        """NOTE: Concat.listの関係で、visit_PortArg()return時にLSB側になるよう逆順にするので
        　　　　 ここではmsb側から順にvisitor.dct_wire_name_bit[]に格納する
        """
        width = abs(msb - lsb) + 1
        step = -1 if msb >= lsb else 1
        for itr in range(width):
            bit = msb + step * itr
            visitor.dct_wire_name_bit[visitor.cnt_found_bit] = { "name" : wire_name, "bit" : bit}
            visitor.cnt_found_bit += 1
        return

    def visit_Pointer(visitor, node):
        assert(isinstance(node, PyVPoiner))
        wire_name = node.var.name
        bit = int(node.ptr.value)
        visitor.dct_wire_name_bit[visitor.cnt_found_bit] = { "name" : wire_name, "bit" : bit}
        visitor.cnt_found_bit += 1
        return

    def visit_Identifier(visitor, node):
        assert(isinstance(node, PyVIdentifier))
        visitor.dct_wire_name_bit[visitor.cnt_found_bit] = { "name" : node.name, "bit" : 0}
        visitor.cnt_found_bit += 1
        return
        
    def visit_NoneType(visitor, node):
        visitor.dct_wire_name_bit[visitor.cnt_found_bit] = { "name" : None, "bit" :  0}
        visitor.cnt_found_bit += 1
        return
        
class DummyModuleDefTraceVisitor(BaseTraceVisitor):
    def visit_DummyModuleDef(visitor, node):
        all_inputs = []
        all_outputs = []
        for p in node.dct_input.values():
            for b in p.bit.values():
                all_inputs.append(b)
        for p in node.dct_output.values():
            for b in p.bit.values():
                all_outputs.append(b)
        for p in node.dct_input.values():
            for b in p.bit.values():
                b.ls_loader = all_outputs
        for p in node.dct_output.values():
            for b in p.bit.values():
                b.ls_driver = all_inputs
        return

class ModuleOutputTraceVisitor(BaseTraceVisitor):
    def visit_ModuleDef(visitor, node):
        for module_output in node.dct_output.values():
            for module_output_bit in module_output.bit.values():
                for instance in node.dct_instance.values():
                    for instance_output in instance.dct_output.values():
                        for instance_output_bit in instance_output.bit.values():
                            if module_output_bit.name == instance_output_bit.wire_name and \
                               module_output_bit.bit  == instance_output_bit.wire_bit:
                               module_output_bit.ls_driver.append(instance_output_bit)
                               instance_output_bit.ls_loader.append(module_output_bit)
        """recursive call"""
        for i in node.dct_instance.values():
            visitor.visit(i)
        return

class SubModuleInputTraceVisitor(BaseTraceVisitor):
    def visit_ModuleDef(visitor, node):
        for instance in node.dct_instance.values():
            for instance_input in instance.dct_input.values():
                for instance_input_bit in instance_input.bit.values():
                    """module.inputport -> submodule.inputport"""
                    for module_input in node.dct_input.values():
                        for module_input_bit in module_input.bit.values():
                            if module_input_bit.name == instance_input_bit.wire_name and \
                               module_input_bit.bit  == instance_input_bit.wire_bit:
                               module_input_bit.ls_loader.append(instance_input_bit)
                               instance_input_bit.ls_driver.append(module_input_bit)
                    """submodule.outputport -> submodule.inputport"""
                    for instance2 in node.dct_instance.values():
                        if instance is instance2:
                            continue
                        for instance2_output in instance2.dct_output.values():
                            for instance2_output_bit in instance2_output.bit.values():
                                if instance2_output_bit.wire_name == instance_input_bit.wire_name and \
                                   instance2_output_bit.wire_bit  == instance_input_bit.wire_bit:
                                    instance2_output_bit.ls_loader.append(instance_input_bit)
                                    instance_input_bit.ls_driver.append(instance2_output_bit)
        """recursive call"""
        for i in node.dct_instance.values():
            visitor.visit(i)
        return
