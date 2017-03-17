import os
import subprocess
from weakref import ref

from lib import pyjack

import pyrser
from pyrser import meta
from pyrser.grammar import Grammar

from cnorm.parsing.declaration import Declaration
from cnorm.parsing.expression import Expression
from cnorm import nodes

from kooc_nodes import Import
from kooc_nodes import Module
from kooc_nodes import Implem
from kooc_nodes import Bracket

class Parser(Grammar, Declaration):
    entry = 'translation_unit'
    grammar = """
        translation_unit =
                [
                        @ignore("C/C++")
                        [
                                __scope__:current_block
                                #new_root(_, current_block)
                                [
                                        #tryInit(_)
                                        "@import" Base.string:n #importKoocFile(_, n) |
                                        [ "@module" Base.id:n #createModule(_, n, current_block) | "@implementation" Base.id:n #createImplem(_, n, current_block) ]
                                        '{' [ Declaration.declaration #saveDecl(_, current_block) ]* '}' #stopSavingDecls(current_block) |
                                        Declaration.declaration
                                ]*
                        ]
                        Base.eof
                ]

        primary_expression =
                [
                        '(' expression:expr ')' #new_paren(_, expr)
                        | [ Literal.literal | identifier ]:>_
                        | bracket:>_
                ]

        bracket = [ [ type_specifier:>_ ]? '[' identifier:m ['.'?]:s identifier:n #createBracket(_, m, s, n) [ ':' assignement_expression:p #saveParam(_, p) ]* ']' ]

        type_specifier = [ "@!(" type_name:>_ ')' ]

    """

    def init(self, filename):
        array = filename.split('/')
        self.tmp_filename = '/tmp/kooc-' + array[len(array) - 1]
        tmp_file = open(self.tmp_filename, 'w')
        completedProcess = subprocess.run(['/usr/bin/cpp', filename], stdout = tmp_file)
        tmp_file.close()
        completedProcess.check_returncode()

    def delete(self):
        os.remove(self.tmp_filename)

    def parse(self):
        self.AST = self.parse_file(self.tmp_filename)
    def buildSymTables(self):
        if not hasattr(self.AST, 'symTable'):
            self.AST.symTable = {}
        for item in self.AST.body:
            if isinstance(item, nodes.Decl) and item._ctype._storage != nodes.Storages.TYPEDEF:
                self.AST.symTable[item._name] = item._ctype
                if hasattr(item, 'body'):
                    self.paramList = item._ctype._params
                    self.buildLocalSymTables(item.body.body)
        for _,moduleRef in self.AST.modules.items():
            for _,declList in moduleRef().declarations.items():
                for ctype,mangledName in declList:
                    self.AST.symTable[mangledName] = ctype
                for _,decl in moduleRef().definitions.items():
                    if hasattr(decl, 'body'):
                        self.paramList = decl._ctype._params
                        self.privDecls = moduleRef().privateDeclarations
                        self.buildLocalSymTables(decl.body.body)

    def buildLocalSymTables(self, curItem):
        declList = []
        bracketList = []
        if isinstance(curItem, Bracket):
            bracketList.append(curItem)
            if not curItem.isVar:
                for item in curItem.params:
                    bracketList.extend(self.buildLocalSymTables(item))
        elif isinstance(curItem, list):
            for item in curItem:
                if isinstance(item, nodes.Decl):
                    declList.append(item)
                else:
                    bracketList.extend(self.buildLocalSymTables(item))
        elif hasattr(curItem, '__dict__') and len(curItem.__dict__):
            for _,item in curItem.__dict__.items():
                bracketList.extend(self.buildLocalSymTables(item))
        for bracket in bracketList:
            for decl in declList:
                if decl._name not in bracket.symTable:
                    bracket.symTable[decl._name] = decl._ctype
            for decl in self.paramList:
                bracket.symTable[decl._name] = decl._ctype
            if hasattr(self, 'privDecls'):
                for _,decls in self.privDecls.items():
                    for ctype,mangledName in decls:
                        bracket.symTable[mangledName] = ctype
        return bracketList

    def saveBracketsExprRef(self):
        for item in self.AST.body:
            if isinstance(item, Implem):
                for _,definition in item.moduleRef().definitions.items():
                    startNodes = []
                    if hasattr(definition, 'body'):
                        for attr in definition.body.body:
                            startNodes.extend(self.getStartNodes(attr))
                        for node in startNodes:
                            if isinstance(node, nodes.Return):
                                self.ret = definition._ctype
                            bracketRef = self.getShallowest(self.findBracket(node, None, 0))[1]
                            if hasattr(self, 'ret'):
                                delattr(self, 'ret')
                            if bracketRef is not None and (len(self.AST.brackets) == 0 or bracketRef() is not self.AST.brackets[len(self.AST.brackets) - 1]()):
                                self.AST.brackets.append(bracketRef)
            elif isinstance(item, nodes.Decl) and hasattr(item, 'body'):
                startNodes = []
                for attr in item.body.body:
                    startNodes.extend(self.getStartNodes(attr))
                for node in startNodes:
                    if isinstance(node, nodes.Return):
                        self.ret = item._ctype
                    bracketRef = self.getShallowest(self.findBracket(node, None, 0))[1]
                    if bracketRef is not None and (len(self.AST.brackets) == 0 or bracketRef() is not self.AST.brackets[len(self.AST.brackets) - 1]()):
                        self.AST.brackets.append(bracketRef)

    def getStartNodes(self, curItem):
        startNodes = []
        if isinstance(curItem, nodes.Decl) or isinstance(curItem, nodes.ExprStmt) or isinstance(curItem, nodes.Return) or isinstance(curItem, nodes.Unary):
            startNodes.append(curItem)
        elif isinstance(curItem, nodes.BlockStmt):
            for item in curItem.body:
                startNodes.extend(self.getStartNodes(item))
        elif isinstance(curItem, nodes.Do) or isinstance(curItem, nodes.Switch) or isinstance(curItem, nodes.While):
            startNodes.append(curItem)
            startNodes.extend(self.getStartNodes(curItem.body))
        elif isinstance(curItem, nodes.If):
            startNodes.append(curItem)
            startNodes.extend(self.getStartNodes(curItem.elsecond))
            startNodes.extend(self.getStartNodes(curItem.thencond))
        elif isinstance(curItem, nodes.For):
            startNodes.extend(self.getStartNodes(curItem.body))
            startNodes.extend(self.getStartNodes(curItem.condition))
            startNodes.extend(self.getStartNodes(curItem.increment))
            startNodes.extend(self.getStartNodes(curItem.init))
        return startNodes

    def findBracket(self, attr, parentAttr, depth):
        for _,subAttr in attr.__dict__.items():
            if isinstance(subAttr, Bracket):
                if hasattr(self, 'ret'):
                    subAttr.ret = self.ret
                    delattr(self, 'ret')
                yield (depth, ref(attr))
            elif isinstance(subAttr, pyrser.parsing.node.Node):
                yield self.getShallowest(self.findBracket(subAttr, attr, depth + 1))
            elif isinstance(subAttr, list): # and len(subAttr)
                for i in range(len(subAttr)):
                    if isinstance(subAttr[i], Bracket):
                        yield (depth, ref(attr))
                    else:
                        yield self.getShallowest(self.findBracket(subAttr[i], attr, depth + 1))
            else:
                yield (-1, None)

    def getShallowest(self, gen):
        minDepth = -1
        shallowParentRef = None
        for depth,parentRef in gen:
            if depth != -1 and (minDepth == -1 or depth < minDepth):
                minDepth = depth
                shallowParentRef = parentRef
        return (minDepth, shallowParentRef)

@meta.hook(Parser)
def tryInit(self, root):
    self.root = root
    if hasattr(self, 'imports') and hasattr(self, 'modules') and hasattr(self, 'implems'):
        root.imports = self.imports
        root.modules = self.modules
        root.implems = self.implems
        root.types = self.types
        delattr(self, 'imports')
        delattr(self, 'modules')
        delattr(self, 'implems')
        delattr(self, 'types')
    if not hasattr(root, 'imports'):
        root.imports = {}
    if not hasattr(root, 'modules'):
        root.modules = {}
    if not hasattr(root, 'implems'):
        root.implems = {}
    if not hasattr(root, 'brackets'):
        root.brackets = []
    return True

@meta.hook(Parser)
def importKoocFile(self, root, filename):
    filename = self.value(filename)[1:len(self.value(filename))-1]
    if not filename in root.imports:
        root.imports[filename] = None
        parser = Parser()
        parser.init(filename)
        parser.imports = root.imports
        parser.modules = root.modules
        parser.implems = root.implems
        parser.types = root.types
        parser.parse()
        parser.buildSymTables()
        parser.saveBracketsExprRef()
        importNode = Import(filename, parser.AST)
        parser.delete()
        root.imports.update({ k:v for k,v in importNode.imports.items() if k not in root.imports })
        root.modules.update({ k:v for k,v in importNode.modules.items() if k not in root.modules })
        root.implems.update({ k:v for k,v in importNode.implems.items() if k not in root.implems })
        root.brackets.extend(importNode.brackets)
        if not hasattr(root, 'symTable'):
            root.symTable = {}
        root.symTable.update(importNode.symTable)
        root.types = importNode.types
        delattr(importNode, 'imports')
        delattr(importNode, 'modules')
        delattr(importNode, 'implems')
        delattr(importNode, 'brackets')
        delattr(importNode, 'types')
        root.body.append(importNode)
        root.imports[filename] = ref(importNode)
    return True

# @module handling
@meta.hook(Parser)
def createModule(self, root, name, current_block):
    name = self.value(name)
    if name in root.modules.items():
        print('error: module or class "' + name + '" has already been declared')
        return False
    moduleNode = Module(name, root.body, len(root.body))
    root.body.append(moduleNode)
    root.modules[name] = ref(moduleNode)
    current_block.nextDeclLoc = ref(moduleNode)
    return True

# @implementation handling
@meta.hook(Parser)
def createImplem(self, root, name, current_block):
    name = self.value(name)
    moduleRef = root.modules.get(name)
    if moduleRef is None:
        print('error: module or class "' + name + '" has not been declared')
        return False
    if not name in root.implems.items():
        implemNode = Implem(name, moduleRef, root.body, len(root.body))
        root.body.append(implemNode)
        root.implems[name] = ref(implemNode)
    current_block.nextDefLoc = moduleRef
    return True

# save @{module,implem} content
@meta.hook(Parser)
def saveDecl(self, root, current_block):
    if hasattr(current_block, 'nextDeclLoc') and current_block.nextDeclLoc is not None:
        current_block.nextDeclLoc().saveDeclaration(root.body.pop())
    elif hasattr(current_block, 'nextDefLoc') and current_block.nextDefLoc is not None:
        current_block.nextDefLoc().saveDefinition(root.body.pop())
    return True

@meta.hook(Parser)
def stopSavingDecls(self, current_block):
    current_block.nextDeclLoc = None
    current_block.nextDefLoc = None
    return True

# Brackets handling

@meta.hook(Parser)
def createBracket(self, node, module, separator, name):
    pyjack.replace_all_refs(node, Bracket(self.value(module), self.value(name), self.value(separator) == '.', node, self.root.modules))
    return True

@meta.hook(Parser)
def saveParam(self, bracketNode, param):
    bracketNode.addParam(param)
    return True
