import copy
import itertools
import weakref

from lib import pyjack

from pyrser.parsing import node
from cnorm import nodes
from cnorm.parsing.declaration import Declaration

import kooc_nodes

def transformImport(self):
    name = self.name
    if (name.endswith(".kc")):
        name = name.replace('.kc', '.c')
    elif (name.endswith('.kh')):
        name = name.replace('.kh', '.h')
    pyjack.replace_all_refs(self, nodes.Raw('#include "' + name + '"\n'))

def transformModule(self):
    i = 1
    for _,declList in self.declarations.items():
        for ctype,name in declList:
            self.rootBody.insert(self.index + i, nodes.Decl(name, ctype))
            i += 1
    self.rootBody.pop(self.index)

def transformImplem(self):
    i = 1
    for name,decl in self.moduleRef().definitions.items():
        decl._name = name
        if decl._ctype._storage == nodes.Storages.STATIC:
            decl = copy.deepcopy(decl)
            if hasattr(decl, 'body'):
                delattr(decl, 'body')
            else:
                if hasattr(decl, '_assign_expr'):
                    delattr(decl, '_assign_expr')
            self.rootBody.insert(self.index + i, decl)
            i += 1
    for _,decl in self.moduleRef().definitions.items():
        self.rootBody.insert(self.index + i, decl)
        i += 1
    self.rootBody.pop(self.index)

kooc_nodes.Import.transform = transformImport
kooc_nodes.Module.transform = transformModule
kooc_nodes.Implem.transform = transformImplem
