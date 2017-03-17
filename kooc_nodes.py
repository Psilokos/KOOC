import copy
import itertools

from pyrser.parsing import node
from cnorm import nodes

import mangler

class Import(node.Node):
    def __init__(self, name, content):
        self.name = name
        self.body = content.body
        self.imports = content.imports
        self.modules = content.modules
        self.implems = content.implems
        self.brackets = content.brackets
        self.symTable = content.symTable
        self.types = content.types

class Module(node.Node):
    def __init__(self, name, rootBody, index):
        self.name = name
        self.rootBody = rootBody
        self.index = index
        self.declarations = {}
        self.privateDeclarations = {}
        self.definitions = {}

    def saveDeclarations(self, decl):
        for item in decl.body.body:
            if not item._name in self.declarations:
                self.declarations[item._name] = []
            saveDecl = True
            mangledName = mangler.mangle(self.name, item._name, item._ctype)
            for _,m in self.declarations[item._name]:
                if mangledName == m:
                    saveDecl = False
                    break
            if saveDecl is False:
                continue
            ctype = copy.deepcopy(item._ctype)
            if not isinstance(ctype, nodes.FuncType):
                ctype._storage = nodes.Storages.EXTERN
            self.declarations[item._name].append((ctype, mangledName))
            if type(item._ctype).__name__ != 'FuncType':
                self.definitions[mangledName] = item

    def saveDeclaration(self, decl):
        if not decl._name in self.declarations:
            self.declarations[decl._name] = []
        mangledName = mangler.mangle(self.name, decl._name, decl._ctype)
        for _,m in self.declarations[decl._name]:
            if mangledName == m:
                return
        ctype = copy.deepcopy(decl._ctype)
        if not isinstance(ctype, nodes.FuncType):
            ctype._storage = nodes.Storages.EXTERN
        self.declarations[decl._name].append((ctype, mangledName))
        if type(decl._ctype).__name__ != 'FuncType':
            self.definitions[mangledName] = decl

    def saveDefinition(self, decl):
        mangledName = mangler.mangle(self.name, decl._name, decl._ctype)
        if mangledName in self.definitions:
            raise Exception('error: "' + mangledName + '" has already been defined')
        if not len(list(filter((lambda tup: mangledName == tup[1]), list(itertools.chain.from_iterable(declList for _,declList in self.declarations.items()))))):
            decl._ctype._storage = nodes.Storages.STATIC
            if not decl._name in self.privateDeclarations:
                self.privateDeclarations[decl._name] = []
            self.privateDeclarations[decl._name].append((decl._ctype, mangledName))
        self.definitions[mangledName] = decl

    def saveDefinitions(self, decl):
        for item in decl.body.body:
            mangledName = mangler.mangle(self.name, item._name, item._ctype)
            if mangledName in self.definitions:
                raise Exception('error: "' + mangledName + '" has already been defined')
            if not len(list(filter((lambda tup: mangledName == tup[1]), list(itertools.chain.from_iterable(declList for _,declList in self.declarations.items()))))):
                item._ctype._storage = nodes.Storages.STATIC
                if not item._name in self.privateDeclarations:
                    self.privateDeclarations[item._name] = []
                self.privateDeclarations[item._name].append(item._ctype)
            self.definitions[mangledName] = item

class Implem(node.Node):
    def __init__(self, name, moduleRef, rootBody, index):
        self.name = name
        self.moduleRef = moduleRef
        self.rootBody = rootBody
        self.index = index

class Bracket(node.Node):
    def __init__(self, module, name, isVar, typeSpecifier, modules):
        self.decls = []
        if name in modules[module]().declarations:
            self.decls.extend([ (t,m) for t,m in modules[module]().declarations[name] if (isVar and not isinstance(t, nodes.FuncType)) or (not isVar and isinstance(t, nodes.FuncType)) ])
        if name in modules[module]().privateDeclarations:
            self.decls.extend([ (t,m) for t,m in modules[module]().privateDeclarations[name] if (isVar and not isinstance(t, nodes.FuncType)) or (not isVar and isinstance(t, nodes.FuncType)) ])
        if not len(self.decls):
            raise
        self.isVar = isVar
        if not isVar:
            self.params = []
        self.symTable = {}
        if isinstance(typeSpecifier, nodes.Decl):
            self._ctype = typeSpecifier._ctype

    def addParam(self, param):
        self.params.append(param)
