import cnorm.nodes
from math import ceil

def getUSigned(ctype):
    return (hasattr(ctype, "_sign") and ctype._sign == 2)

def getSize(ctype):
    identifier = {
        "char": 1,
        "int": 4,
        "float": 4,
        "double": 8
    }

    size = 0
    if (type(ctype) == cnorm.nodes.PrimaryType):
        size = identifier[ctype]

    if (ctype._specifier == 6):
        size = ceil(size / 2)
    elif (ctype._specifier == 4):
        size *= 2
    elif (ctype._specifier == 5):
        size *= 4

    return size

def predicate(d, s):
    ssize = getSize(s)
    dsize = getSize(d)
    if (dsize < ssize or
        (ssize == dsize and
         getUSigned(s) and not getUSigned(d))):
        return False
    return True

def Filter(val, l, l2):
    Flag = False
    for elem in l:
        if (predicate(val, elem)):
            Flag = True
    if (not Flag):
        l2.remove(val)

def inference(dest, src):
    for elem in dest:
        Filter(elem, src, dest)
    for elem in src:
        Filter(elem, dest, src)
    return (dest, src)
