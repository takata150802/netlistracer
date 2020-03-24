from __future__ import absolute_import
from __future__ import print_function
import sys
import os
from optparse import OptionParser

# the next line can be removed after installation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyverilog.utils.version
from pyverilog.vparser.parser import parse

from pyverilog.vparser.ast import Node
from pyverilog.vparser.ast import ModuleDef
from pyverilog.vparser.ast import Instance
from pyverilog.vparser.ast import Input
from pyverilog.vparser.ast import Output
from pyverilog.vparser.ast import PortArg
from pyverilog.vparser.ast import Identifier
from pyverilog.vparser.ast import Partselect
from pyverilog.vparser.ast import IntConst
def debug(x):
    print(x, file=sys.stderr, end=' ')
    return

def module_tree(self, buf=sys.stdout, offset=0, showlineno=True):
    indent = 2
    lead = ' ' * offset

    if (self.__class__.__name__== 'ModeleDef'
     or self.__class__.__name__== 'ModuleDef'
      ):
        buf.write(lead + self.__class__.__name__ + ': ')

        if self.attr_names:
            if True:
                nvlist = [(n, getattr(self, n)) for n in self.attr_names]
                attrstr = ', '.join('%s=%s' % (n, v) for (n, v) in nvlist)
            buf.write(attrstr)

        if showlineno:
            buf.write(' (at %s)' % self.lineno)

        buf.write('\n')

    for c in self.children():
        c.module_tree(buf, offset + indent, showlineno)


def get_node(self, fn, buf=sys.stderr, offset=0, showlineno=True, ret=[]):

    indent = 2
    lead = ' ' * offset
    
    if (fn(self)):
        ret.append(self)
        buf.write(lead + self.__class__.__name__ + ': ')
        if self.attr_names:
            nvlist = [(n, getattr(self, n)) for n in self.attr_names]
            attrstr = ', '.join('%s=%s' % (n, v) for (n, v) in nvlist)
            buf.write(attrstr)
        if showlineno:
            buf.write(' (at %s)' % self.lineno)
        buf.write('\n')
        return

    for c in self.children():
        c.get_node(fn, buf, offset + indent, showlineno, ret)
    return ret

gen_dot_header = \
"""
digraph {
    rankdir="LR";
    overlap = false;
    splines = true;
    node [shape = box, height=0.1];
    edge [labelfloat=false];
"""
#   node[width=0.0, height=0.0, label="" shape=point];
gen_dot_footer = "}"
Instance.id_ = 0
def gen_dot(self, ls_module, prefix=''):
    """
    TODO: visitorパターンにrefactorする
    ↓ 2つを分離する点がvisitor patternを知ってる人にはわかりやすいかも
    - selfに対するdot生成処理
    - ls_instanceやportを呼び出す部分
    """
    debug("gen_dot:")
    debug(self)
    debug('\n')
    debug("ls_module:")
    debug(ls_module)
    debug('\n')

    def get_module_def(inst, ls_module):
        assert (inst, Instance)
        emsg = "\n" \
             + "multiple declear of module `" + str(inst.module) + "` is detected.\n" \
             + "but this check is NOT enough 'cause of TOP module multiple declear.\n"
        ll = [i for i in ls_module if isinstance(i, ModuleDef) and i.name == inst.module]
        assert (len(ll) == 1 or len(ll) == 0), emsg
        if len(ll) == 1:
            return ll[0]
        else :
            return None

    def is_output_port_estimate(p, i, module_def=None):
        assert (isinstance(p, PortArg))
        assert (isinstance(i, Instance))
        assert (module_def == None)

        """pがoutput_portだと推測できる条件"""
        portname = p.portname
        if portname[0] == 'o':
            return True
        if portname[0] == 'q':
            return True
        return False

    def is_output_port_with_module_def(p, i, module_def):
        assert (isinstance(p, PortArg))
        assert (isinstance(i, Instance))
        assert (isinstance(module_def, ModuleDef))

        portname = p.portname
        for o in module_def.ls_output:
            if o.name == portname:
                return True
        return False

    def print_connect(src_node_name, prefix, instance, port, wire_name=" "):
        d_prefix = prefix + "_" + instance.name
        d_node_name = d_prefix + "_" + port.portname
        print ("%s -> %s[label = \"%s\"];"%(src_node_name, d_node_name, wire_name)) 

    if isinstance(self, ModuleDef):
        """
        下位モジュール
        """
        for i in self.ls_instance:
            i.gen_dot(ls_module, prefix)
        """
        入力ポート/出力ポートを全てdot_lang:nodeとして表現する
        """
        for i in self.ls_input + self.ls_output:
            node_name = prefix + "_" + i.name
            node_label = i.name
            if hasattr_parents(i, 'width.msb') \
                and hasattr_parents(i, 'width.lsb'):
                msb = i.width.msb.value
                lsb = i.width.lsb.value
                node_label += "[%s:%s]"%(msb,lsb)
            print ("%s[label = \"%s\", style = \"rounded,filled\"];"%(node_name, node_label))
        """
        self(Moduledef) input port(s) dummy node(branch)
        """
        for i in self.ls_input:
            s_node_name = prefix + "_" + i.name
            br_node_name = s_node_name + "_input_br"
            print ("%s[width=0.01, height=0.01, shape=point];"%br_node_name)
            print ("%s -> %s[dir = none];"%(s_node_name, br_node_name))

        """
        [課題]
        下位モジュールが提供されない場合がある(セルライブラリなど)
        下位モジュールの出力ポートであることを判定できない
        あるoutput_portがoutput_portだと認識されるまで
        そのoutput_portの対向input_portは、edgeを定義できなくなる

        [解決]
        - ModuleDef.gen_dot()でoutput_portを特定し、outport用のbranch_nodeをprint()済み
          - output_portの特定方法は以下の通り
            - 下位モジュールが提供されている場合:  impl:is_output_port_with_module_def()
              ModuleDef.ls_outputを逆引きする
            - 下位モジュールが提供されていない場合: impl:is_output_port_estimate()
               アドホックな条件(あるポートがoutput_portと推測できる条件)を列挙しておき、
               その条件を満たすならoutput_port
                満たさないならinput_portと推測することにする
              [例]
              if instanceのモジュール名 == CLKINV && port名 == x:
                  -> 判定：output_port, branch_nodeをprint()してcontinue, edgeはprint()しない
                  ...
              elif instanceのモジュール名 == SRFF && port名 == q:
                  -> 判定：output_port, branch_nodeをprint()してcontinue, edgeはprint()しない
              else:
                  pass
        - Instance.gen_dot()ではoutput_port/input_portは特定済みなので
          loader/dirver 配線関係のtraceが容易

        [擬似コード]
          for loader in (parent_module,output):
            if driver is sub_module.output?:
                -> edgeをprint()

          for loader in (submodule.input):
            if driver is Constant?:
            if driver is parent_module.input?:
            if driver is sub_module.output?:
                -> edgeをprint()
        """

        """for loader in (parent_module,output):"""
        for o in self.ls_output:
            """if driver is sub_module.output?:"""
            for i in self.ls_instance:
                module_def = get_module_def(i, ls_module)
                if module_def == None:
                    is_output_port = is_output_port_estimate
                else:
                    is_output_port = is_output_port_with_module_def
                for p in i.portlist:
                    assert(hasattr(p, 'argname'))
                    if is_output_port(p, i, module_def):
                        assert(isinstance(p.argname, Identifier) or isinstance(p.argname, Partselect))
                        arg_wire_name = p.argname.name if isinstance(p.argname, Identifier) else p.argname.var.name
                        if o.name == arg_wire_name:
                            s_node_name = prefix + "_" + i.name + "_" + p.portname + "_output_br"
                            d_node_name = prefix + "_" + o.name
                            print ("%s -> %s[label = \"%s\"];"%(s_node_name, d_node_name, "")) 

        """for loader in (submodule.input):"""
        for i in self.ls_instance:
            module_def = get_module_def(i, ls_module)
            if module_def == None:
                is_output_port = is_output_port_estimate
            else:
                is_output_port = is_output_port_with_module_def
            for p in i.portlist:
                assert(hasattr(p, 'argname'))
                if not is_output_port(p, i, module_def):
                    if isinstance(p.argname, IntConst):
                        """if driver is Constant?:"""
                        ### TODO:bit幅チェック
                        const_value = p.argname.value
                        const_node_name = prefix + "_const_" + i.name + p.portname
                        print ("%s[label = \"%s\"];"%(const_node_name, const_value))
                        print_connect(const_node_name, prefix, i, p)
                        continue
                    elif isinstance(p.argname, Identifier) or isinstance(p.argname, Partselect):
                        """if driver is parent_module.input?:"""
                        arg_wire_name = p.argname.name if isinstance(p.argname, Identifier) else p.argname.var.name
                        ll = [i for i in self.ls_input if i.name == arg_wire_name]
                        assert (len(ll) == 1 or len(ll) == 0), "fuck"
                        if (len(ll) == 1):
                            br_node_name = prefix + "_" + ll[0].name + "_input_br"
                            print_connect(br_node_name, prefix, i, p)
                            continue
                        """if driver is sub_module.output?:"""
                        for ii in self.ls_instance:
                            if i is ii:
                                continue
                            module_def = get_module_def(ii, ls_module)
                            if module_def == None:
                                is_output_port = is_output_port_estimate
                            else:
                                is_output_port = is_output_port_with_module_def
                            for pp in ii.portlist:
                                assert(hasattr(pp, 'argname'))
                                if is_output_port(pp, ii, module_def) \
                                   and ( \
                                       isinstance(pp.argname, Identifier) or isinstance(pp.argname, Partselect) \
                                   ):
                                    s_arg_wire_name = pp.argname.name if isinstance(pp.argname, Identifier) else pp.argname.var.name
                                    if s_arg_wire_name == arg_wire_name:
                                        br_node_name = prefix + "_" + ii.name + "_" + pp.portname + "_output_br"
                                        print_connect(br_node_name, prefix, i, p, arg_wire_name)
                    else:
                        pass
                else:
                    pass
        return

    elif isinstance(self, Instance):
        print ('subgraph cluster%d {'%Instance.id_)
        print ("  graph [label = \"%s:%s\"];"%(self.module, self.name))
        print ("tmp%d[width=0.0, height=0.0, shape=point];"%Instance.id_)

        Instance.id_ += 1
        module_def = get_module_def(self, ls_module)
        if module_def is None:
            for p in self.portlist:
                assert(hasattr(p, 'argname'))
                node_label = p.portname
                node_name = prefix + "_" + self.name + "_" + node_label
                print ("%s[label = \"%s\", style = \"rounded,filled\"];"%(node_name, node_label))
            is_output_port = is_output_port_estimate
        else:
            module_def.gen_dot(ls_module, prefix + "_" + self.name)
            is_output_port = is_output_port_with_module_def
        print ('}')

        for p in self.portlist:
            assert(hasattr(p, 'argname'))
            if is_output_port(p, self, module_def):
                s_node_name = prefix + "_" + self.name + "_" + p.portname
                br_node_name = s_node_name + "_output_br"
                print ("%s[width=0.01, height=0.01, shape=point];"%br_node_name)
                print ("%s -> %s[dir = none];"%(s_node_name, br_node_name))
        return

    else:
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

    Node.get_node= get_node
    Node.gen_dot = gen_dot
    ast, directives = parse(filelist,
                            preprocess_include=options.include,
                            preprocess_define=options.define)
    ls_module = []
    ast.get_node(lambda x: isinstance(x, ModuleDef), ret=ls_module)
    for m in ls_module:
        m.ls_input = []
        m.ls_output = []
        m.ls_instance = []
        m.get_node(lambda x: isinstance(x, Input), ret=m.ls_input)
        m.get_node(lambda x: isinstance(x, Output), ret=m.ls_output)
        m.get_node(lambda x: isinstance(x, Instance), ret=m.ls_instance)
        for i in m.ls_instance:
            i.ls_port = []
            i.get_node(lambda x: isinstance(x, PortArg), ret=i.ls_port)
    print (gen_dot_header)
    ls_module[0].gen_dot(ls_module)
    for i in ls_module[0].ls_input:
        print ("{rank = min; _%s;}"%i.name)
    for i in ls_module[0].ls_output:
        print ("{rank = max; _%s;}"%i.name)
    print (gen_dot_footer)
    
if __name__ == '__main__':
    main()
