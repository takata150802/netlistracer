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
    node [shape = box];
    edge [labelfloat=false];
"""
gen_dot_footer = "}"
Instance.id_ = 0
def gen_dot(self, ls_module):
    debug("gen_dot:")
    debug(self)
    debug('\n')
    debug("ls_module:")
    debug(ls_module)
    debug('\n')

    if isinstance(self, ModuleDef):
        for i in self.ls_instance:
            i.gen_dot(ls_module)
        return

    elif isinstance(self, Instance):
        """
        TODO: visitorパターンにrefactorする
              ↓ 2つを分離する点がvisitor patternを知ってる人にはわかりやすいかも
              - selfに対するdot生成処理
              - ls_instanceやportを呼び出す部分
        """
        print ('subgraph cluster%d {'%Instance.id_)
        print ("  graph [label = \"%s:%s\"];"%(self.module, self.name))
        print ("tmp%d;"%Instance.id_)

        Instance.id_ += 1
        ll = [i for i in ls_module if isinstance(i, ModuleDef) and i.name == self.module]
        debug("ll = [i for i in ls_module if isinstance(i, ModuleDef) and i.name == self.module]:")
        debug(ll)
        debug(self.module)
        debug('\n')
        emsg = "\n" \
             + "multiple declear of module `" + str(self.module) + "` is detected.\n" \
             + "but this check is NOT enough 'cause of TOP module multiple declear.\n"
        assert (len(ll) == 1 or len(ll) == 0), emsg
        if len(ll) == 1:
            ll[0].gen_dot(ls_module)
        else :
            pass
        print ('}')
        return

    else:
        for c in self.children():
            c.gen_dot(ls_module)
        return
    assert (False), "Unreachable."

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
    print (gen_dot_footer)
    
if __name__ == '__main__':
    main()
