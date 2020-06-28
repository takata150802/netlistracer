import sys

class NetListHierTraceVisitor(object):
    def __init__(visitor):
        pass
        return
    def visit(visitor, node):
        visitor1st = InstanceGetPortArgWireVisitor()
        visitor2nd = DummyModuleDefTraceVisitor()
        visitor3rd = ModuleOutputTraceVisitor()
        visitor1st.visit(node)
        visitor2nd.visit(node)
        visitor3rd.visit(node)
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
        wire_name = node.var
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
                b.ls_driver = all_outputs
        return

class ModuleOutputTraceVisitor(BaseTraceVisitor):
    def visit_ModuleDef(visitor, node):
        for mod_o in node.dct_output.values():
            for mod_o_bitnum in mod_o.bit.keys():
                for i in node.dct_instance.values():
                    for inst_o in i.dct_output.values():
                        for inst_o_b in inst_o.bit.values():
                            if mod_o.name == inst_o_b.wire_name and \
                               mod_o_bitnum == inst_o_b.wire_bit:
                               mod_o.bit[mod_o_bitnum].ls_driver.append(inst_o_b)
                               inst_o_b.ls_loader.append(mod_o.bit[mod_o_bitnum])
        return

