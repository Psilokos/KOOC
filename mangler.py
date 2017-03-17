import sys
from cnorm.parsing.declaration import Declaration
from cnorm.passes import to_c
from cnorm import nodes

def     mangle(moduleName, itemName, ctypeNode):
    value = ""
    value += fct_mangler(moduleName, itemName, ctypeNode)
    if (not value):
        value += variableMangler(moduleName, itemName, ctypeNode)
    if (not value):
        value += composedTypesMangler(moduleName, itemName, ctypeNode)
    return value

def     primaryTypesValue(ctypeNode):
    value = ""
    value += valueSize(ctypeNode)
    if (value != "v" and value):
        value += valueSignedness(ctypeNode)
    return value

def     valueSize(ctypeNode):
    value = ""
    if (ctypeNode._identifier == "double"):
        if(ctypeNode._specifier == 4):
            value += "f16"
        else:
            value += "f8"
    elif(ctypeNode._identifier == "int"):
        if (ctypeNode._specifier == 6):
            value += "i2"
        elif(ctypeNode._specifier == 4 or ctypeNode._specifier == 5):
            value += "i8"
        else:
            value += "i4"
    elif(ctypeNode._identifier == "char"):
        value += "i1"
    elif(ctypeNode._identifier == "float"):
        value += "f4"
    elif(ctypeNode._identifier == "void"):
        value += "v"
    return value

def     valueSignedness(ctypeNode):
    value = ""
    if (hasattr(ctypeNode, "_sign")):
        value += 'u'
    else:
        value += 's'
    return value

def     isPrimaryType(identifier):
    value = ""
    var_types = {
        "void",
        "int",
        "float",
        "char",
        "double"
    }
    for i in var_types:
        if (i == identifier):
            return True
    return False


def     addClassName(className):
    value = ""
    if className:
        value += '_' + className
    return value

def     addFctName(functionName):
    value = ""
    if functionName:
        value += '_' + functionName
    return value

def     pointerFunctionPointerReturn(ctypeNode):
    value = ""
    if (hasattr(ctypeNode, "_decltype") and isinstance(ctypeNode._decltype, nodes.PointerType)):
        value += "p"
    return value

def     functionPointerMangle(node, tmp):
    value = tmp

    if (hasattr(node, "_decltype") and isinstance(node._decltype, nodes.PointerType) and
        hasattr(node._decltype, "_decltype") and
        isinstance(node._decltype._decltype, nodes.ParenType)):
        value += "pF_"  + pointerFunctionPointerReturn(node._decltype._decltype)
        value += getTypes("", node) + var_param_types("", node._decltype._decltype) + '_E'
    elif (hasattr(node, "_decltype") and isinstance(node._decltype, nodes.ParenType)):
        raise Exception("Can't be a function pointer")
    return value

def     mangling_point(node, value):
    tmp = value
    if (hasattr(node, "_decltype") and (isinstance(node._decltype, nodes.PointerType)
        or isinstance(node._decltype, nodes.ArrayType))):
        tmp += "p"
        if (hasattr(node._decltype , "_decltype") and
            (isinstance(node._decltype._decltype, nodes.PointerType) or
            isinstance(node._decltype._decltype, nodes.ArrayType))):
            tmp = mangling_point(node._decltype, tmp)
    return tmp

def     getTypes(className, ctypeNode):
    value = ''
    composedType = ""
    value += primaryTypesValue(ctypeNode)
    composedType += composedTypesMangle(ctypeNode)
    if not composedType:
        value += classMangle(ctypeNode._identifier, ctypeNode)
    else:
        value += composedType
    return value

def     composedTypesMangle(ctypeNode):
    value = ""

    if (isinstance(ctypeNode, nodes.ComposedType)):
        value += "S_" + ctypeNode._identifier + "_E"
    elif(ctypeNode._identifier and ctypeNode._specifier == 1):
        value += "S_" + ctypeNode._identifier + "_E"
    return value

def     classMangle(className, ctypeNode):
    value = ""

    if (className and not isPrimaryType(ctypeNode._identifier)):
        value += 'U_' + ctypeNode._identifier + "_E"
    return value

def    var_param_types(className, ctypeNode):
    value = ""
    fctPointer = ""
    if (hasattr(ctypeNode, "_params") and len(ctypeNode._params)):
        for i in ctypeNode._params:
            value += '_'
            if (hasattr(i, "_ctype")):
                if (i._ctype._identifier == "void" and len(ctypeNode._params) > 1 and
                (not isinstance(i._ctype._decltype, nodes.PointerType) or
                 not isinstance(i._ctype._decltype, nodes.ArrayType))):
                    raise Exception("You can't put a parameter after a void parameter")
                fctPointer += functionPointerMangle(i._ctype, "")
                if not fctPointer:
                    value += mangling_point(i.ctype, "")
                    value += getTypes(className, i._ctype)
                else:
                    value += fctPointer
    else:
        value += "_v"
    return value

def     fct_mangler(className, functionName, ctypeNode):
    mangled = ""
    if type(ctypeNode).__name__ == "FuncType":
        mangled += "__kfct"
        mangled += addClassName(className)
        mangled += addFctName(functionName) + '_'
        mangled += mangling_point(ctypeNode, "")
        mangled += getTypes(className, ctypeNode)
        mangled += var_param_types(className, ctypeNode)
        return mangled
    return mangled

def     variableMangler(className, variableName, ctypeNode):
    value = ""
    pointerMangle = ""
    if type(ctypeNode).__name__  == "PrimaryType":
        value += "__kvar_" + className + '_' + variableName
        pointerMangle += functionPointerMangle(ctypeNode, "")
        if not pointerMangle:
            value += '_' + mangling_point(ctypeNode, "")
            value += primaryTypesValue(ctypeNode)
            value += classMangle(className, ctypeNode)
        else:
            value += '_' + pointerMangle;
    elif type(ctypeNode).__name__ == "FuncType":
        value += fct_mangle(className, variableName, ctypeNode)
    return value

def     composedTypesMangler(className, variableName, ctypeNode):
    value = ""
    if type(ctypeNode).__name__ == "ComposedType":
        value += "__kvar_" + className
        if (variableName):
             value += '_' + variableName
        value += "_" + mangling_point(ctypeNode, "")
        value += composedTypesMangle(ctypeNode)
    return value;
