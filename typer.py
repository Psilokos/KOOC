import re

from lib import pyjack

import cnorm.nodes
import kooc_nodes

getType = None

class TyperError(Exception):
    pass

class Ambiguous(TyperError):
    def __init__(self, expression = "", message = ""):
        self.expression = expression
        self.message = message

class Untypable(TyperError):
    def __init__(self, expression = "", message = ""):
        self.expression = expression
        self.message = message

class Unknown(TyperError):
    def __init__(self, expression = "", message = ""):
        self.expression = expression
        self.message = message

class getTypedef():
    def __init__(self, typedefs):
        self.typedefs = typedefs

    def __call__(self, ctype):
        for dic in self.typedefs.maps:
            if ctype._identifier in dic:
                return dic[ctype._identifier]()._ctype
        return ctype

def getNode(name, globs, locs = []):
    if name in locs:
        return locs[name]
    elif name in globs:
        return globs[name]
    else:
        raise Unknown("Can't find symbol", name)

def getLiteralType(lit, sign = '+'):
    rint = re.compile("^\d+$")
    rfloat = re.compile("^\d+\.\d*[fF]?$")
    if rint.match(lit):
        i = int(lit)
        if i <= 127 or (sign == '-' and i <= 128):
            node =  cnorm.nodes.PrimaryType("char")
        elif i <= 32767 or (sign == '-' and i <= 32768):
            node = cnorm.nodes.PrimaryType("int")
            node._specifier = 6
        elif i <= 2147483647 or (sign == '-' and i <= 2147483648):
            node = cnorm.nodes.PrimaryType("int")
        else:
            node = cnorm.nodes.PrimaryType("int")
            node._specifier = 4
    elif rfloat.match(lit):
        node = cnorm.nodes.PrimaryType("float")
    else:
        node = cnorm.nodes.PrimaryType("char")
        node._decltype = cnorm.nodes.PointerType()
    return node

def checkDeclType(n1, n2):
    if n1._decltype is None and n2._decltype is None:
        return True
    if hasattr(n1, "_decltype") and hasattr(n2, "_decltype") and isinstance(n1._decltype, cnorm.nodes.PointerType) and isinstance(n2._decltype, cnorm.nodes.PointerType):
        return True
    return False

## "Curryed" filter function. First take a list of all possible ctype
## then a decl to filter or remove from the bracket decl list.
## We send a list, because when filtering on a function, there is not only one
## matching case.
def varFilter(poss_list):
    def curry(var):
        if len(poss_list) == 0:
            return True
        for p in poss_list:
            if (getType(var[0])._identifier == getType(p)._identifier and var[0]._specifier == p._specifier):
                if hasattr(var[0], "_decltype"):
                    return checkDeclType(var[0], p)
                return True
        return False
    return curry

## This function use the var filter to type the l_node, which is a bracket Node.?
def varTyper(l_node, types, symbole, typedefs):
    try:
        ctype = l_node._ctype
        types = [ctype]
    except:
        try:
            ctype = l_node.ret
            types = [ctype]
        except:
            pass
    p = list(filter(varFilter(types), l_node.decls))
    if len(p) == 0:
        raise Untypable()
    if len(p) == 1:
        return (True, cnorm.nodes.Id(p[0][1]))
    elif len(p) < len(l_node):
        return (True, p)
    else:
        return (False, l_node)

## "Curryed" function. first take the bracket node to determine
## Then a decl to either select or remove from the list via a filter.
## Decls are stored into bracket.decls as a list of tuple (ctype, mangled_name).
## In function case, we assume that there won't be ambiguities on the function length. thus the unique
## arg.
def funcLenFilter(bracket):
    def curry(to_filter):
        p_len = len(bracket.params)
        f_len = len(to_filter[0]._params)
        if f_len < p_len:
            return False
        elif p_len == f_len:
            return True
        else:
            if f_len == 1 and p_len == 0 and getType(to_filter[0]._params[0]._ctype)._identifier == "void" and to_filter[0]._params[0]._ctype._decltype is None:
                return True
            try:
                return to_filter[0]._ellipsis
            except:
                return False
    return curry

## This function do both filtering and typing args of a given function, be it a ctype or a bracket node.
## The point is both to be able tou find out the best matching function AND/OR it's content.
## To have a certain level of absraction, the "function" will be in a list, on which this one
## will be called via the filter function.
## It will also be filtering inner var and try to type these.
def checkArgType(arg, ctype, typedefs):
    if (getType(arg)._identifier == getType(ctype)._identifier and arg._specifier == ctype._specifier):
        if hasattr(arg, "_decltype"):
            return checkDeclType(arg, ctype)
        return True
    return False

def resolveType(param, symbole, locs = {}):
    if isinstance(param, kooc_nodes.Bracket):
        return list(map(lambda x : x[0], param.decls))
    elif isinstance(param, cnorm.nodes.Binary) or isinstance(param, cnorm.nodes.Unary):
        return resolveType(param.params[0], symbole, locs)
    elif isinstance(param, cnorm.nodes.Literal):
        return getLiteralType(param.value)
    elif isinstance(param, cnorm.nodes.Id):
        return getNode(param.value, symbole, locs)
    elif isinstance(param, cnorm.nodes.CType):
        return param
    else:
        raise Unknown("Unknown Type : ", str(type(param)))


def funcArgsFilter(params, symbole, typedefs, locs):
    def curry(to_filter):
        i = 0
        for param in params:
            if i == len(to_filter[0]._params):
                try:
                    if to_filter[0]._ellipsis == True:
                        break
                except:
                    pass
            if isinstance(param, kooc_nodes.Bracket):
                try:
                    varTyper(param, [getType(to_filter[0]._params[i]._ctype)], symbole, typedefs)
                except:
                    return False
            else:
                typ = resolveType(param, symbole, locs)
                if isinstance(typ, list):
                    ret = False
                    for t in typ:
                        if checkArgType(to_filter[0].params[i]._ctype, t, typedefs):
                            ret = True
                            break
                    if not ret:
                        return False
                else:
                    if not checkArgType(to_filter[0]._params[i]._ctype, typ, typedefs):
                        return False
            i = i + 1

        if i < len(params):
            for param in param[i:]:
                if isinstance(param, kooc_nodes.Bracket):
                    ret = inner_type(param, [], symbole, typedefs)
                    if isinstance(ret[1], kooc_nodes.Bracket):
                        return False
        return True
    return curry

def funcRetFilter(poss_list):
    def curry(to_filter):
        if len(poss_list) == 0:
            return True
        for p in poss_list:
            if (getType(to_filter[0])._identifier == getType(p)._identifier and to_filter[0]._specifier == p._specifier):
                if hasattr(to_filter[0], "_decltype"):
                    if checkDeclType(to_filter[0], p):
                        return True
                    else:
                        continue
                return True
        return False
    return curry

def funcTyper(l_node, types, symbole, typedefs):
    filtered = list(filter(funcLenFilter(l_node), l_node.decls))
    try:
        ctype = l_node._ctype
        types = [ctype]
    except:
        try:
            ctype = l_node.ret
            types = [ctype]
        except:
            pass
    filtered = list(filter(funcRetFilter(types), filtered))
    filtered = list(filter(funcArgsFilter(l_node.params, symbole, typedefs, l_node.symTable), filtered))

    if len(filtered) == 1:
        ctype = filtered[0][0]
        i = 0
        for arg, param in zip(ctype._params, l_node.params):
            ret = inner_type(param, [arg._ctype], symbole, typedefs)
            if not isinstance(ret[1], cnorm.nodes.Expr):
                raise Ambiguous("Several matching types")
            else:
                l_node.params[i] = ret[1]
            i += 1
        ret = cnorm.nodes.Func(cnorm.nodes.Id(filtered[0][1]), l_node.params)
        return (True, ret)

    elif len(filtered) == 0:
        raise Untypable("No Matching Type")
    elif len(filtered) < len(l_node.decls):
        args = list()
        for i in range(len(l_node.params)):
            args[i] = list()
            for ctype, name in filtered:
                try:
                    args[i].append(ctype._params[i])
                except:
                    pass
        i = 0
        for arg, param in zip(args, l_node.params):
            ret = inner_type(param, arg, symbole, typedefs)
            l_node[i].params = ret[1]
        l_node.decls = filtered
        return (True, l_node)
    else:
        return (False, l_node)

def inner_type(node, types, symbole, typedefs):
    if isinstance(node, kooc_nodes.Bracket):
        if not node.isVar:
            ret = funcTyper(node, types, symbole, typedefs)
        else:
            return varTyper(node, types, symbole, typedefs)
        if isinstance(ret[1], kooc_nodes.Bracket):
            if ret[0]:
                return (True, inner_type(ret[1], types, symbole, typedefs)[1])
            return ret
        else:
            return ret
    elif isinstance(node, cnorm.nodes.Conditional):
        ret = inner_type(node.condition, [], symbole, typedefs)
        if isinstance(ret[1], kooc_nodes.Bracket):
            raise Ambiguous("Several matching types")
        node.condition = ret[1]
        return (True, node)

    elif isinstance(node, cnorm.nodes.Cast):
        ret = inner_type(node.params[1], [], symbole, typedefs)
        if isinstance(ret[1], kooc_nodes.Bracket):
            raise Ambiguous("Several matching types")
        node.params[1] = ret[1]
        return (True, node)

    elif isinstance(node, cnorm.nodes.Unary):
        ret = inner_type(node.params[0], [], symbole, typedefs)
        if isinstance(ret[1], kooc_nodes.Bracket):
            raise Ambiguous("Several matching types")
        node.params[0] = ret[1]
        return (True, node)

    elif isinstance(node, cnorm.nodes.Binary):
        left = False
        right = False
        if isinstance(node.params[0], kooc_nodes.Bracket):
            left = True
            if isinstance(node.params[1], kooc_nodes.Bracket):
                ntypes = list(map(lambda x : x[0], node.params[0].decls))
                ret = inner_type(node.params[1], ntypes, symbole, typedefs)
                node.params[1] = ret[1]
                if isinstance(node.params[1], kooc_nodes.Bracket):
                    right = True
            else:
                node.params[1] = inner_type(node.params[1], types, symbole, typedefs)[1]
        elif isinstance(node.params[0], cnorm.nodes.Cast):
            pass
        else:
            node.params[0] = inner_type(node.params[0], types, symbole, typedefs)[1]
            if isinstance(node.params[1], kooc_nodes.Bracket):
                try:
                    ntypes = [getNode(node.params[0].call_expr.value, symbole, node.params[1].symTable)]
                except:
                    try:
                        ntypes = [getNode(node.params[0].value, symbole, node.params[1].symTable)]
                    except:
                        ntypes = resolveType(node.params[0], symbole, node.params[1].symTable)
                        if not isinstance(ntypes, list):
                            ntypes = [ntypes]
                ret = inner_type(node.params[1], ntypes, symbole, typedefs)
                if isinstance(ret[1], kooc_nodes.Bracket):
                    raise Ambiguous("Several matching types")
                node.params[1] = ret[1]
            else:
                node.params[1] = inner_type(node.params[1], types, symbole, typedefs)[1]
        if left:
            if isinstance(node.params[1], kooc_nodes.Bracket):
                types = list(map(lambda x : x[0], node.params[1].decls))
                ret = inner_type(node.params[0], types, symbole, typedefs)
                node.params[0] = ret[1]
                if isinstance(node.params[0], kooc_nodes.Bracket):
                    raise Ambiguous("Several matching types")
                else:
                    return inner_type(node, types, kooc_nodes, typedefs)
            else:
                try:
                    ntypes = [getNode(node.params[1].call_expr.value, symbole, node.params[0].symTable)]
                except:
                    try:
                        ntypes = [getNode(node.params[1].value, symbole, node.params[0].symTable)]
                    except:
                        ntypes = resolveType(node.params[1], symbole, node.params[0].symTable)
                        if not isinstance(ntypes, list):
                            ntypes = [ntypes]
                ret = inner_type(node.params[0], ntypes, symbole, typedefs)
                if isinstance(ret[1], kooc_nodes.Bracket):
                    raise Ambiguous("Several matching types")
                node.params[0] = ret[1]

        return (True, node)

    elif isinstance(node, cnorm.nodes.Ternary):
        i = 1
        ret = inner_type(node.params[0], [], symbole, typedefs)
        if isinstance(ret[1], kooc_nodes.Bracket):
            raise Ambiguous("Several matching types")
        node.params[0] = ret[1]
        for param in node.params[1:]:
            param[i] = inner_type(param, types, symbole, typedefs)
            if isinstance(param[i], kooc_nodes.Bracket):
                raise Ambiguous("Several matching types")
            i += 1
        return (True, node)

    elif isinstance(node, cnorm.nodes.Func):
        ctype = getNode(node.call_expr.value, symbole)
        i = 0
        for param in node.params:
            if isinstance(param, kooc_nodes.Bracket):
                ret = inner_type(param, [ctype._params[i]._ctype], symbole, typedefs)
                if isinstance(ret[1], kooc_nodes.Bracket):
                    raise Ambiguous("Several matching types")
                else:
                    node.params[i] = ret[1]
            i += 1
        return (True, node)

    elif isinstance(node, cnorm.nodes.Decl):
        try:
            assign = node._assign_expr
        except:
            return (True, node)

        ret = inner_type(assign, [node._ctype], symbole, typedefs)
        if ret[0]:
            if isinstance(ret[1], kooc_nodes.Bracket):
                raise Ambiguous("Several matching types")
            node._assign_expr = ret[1]
            return (True, node)
        else:
            raise Ambiguous("Several matching types")
    elif isinstance(node, cnorm.nodes.ExprStmt) or isinstance(node, cnorm.nodes.Return):
        ret = inner_type(node.expr, [], symbole, typedefs)
        if isinstance(ret[1], kooc_nodes.Bracket):
            raise Untypable()
        node.expr = ret[1]
        return (True, node)
    elif isinstance(node, cnorm.nodes.Terminal):
        return (True, node)

    else:
        raise Unknown()

def typer(root, symbole, typedefs):
    global getType
    getType = getTypedef(typedefs)
    pyjack.replace_all_refs(root(), inner_type(root(), [], symbole, typedefs)[1])
    return True
