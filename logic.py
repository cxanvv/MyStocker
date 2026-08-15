import json

def GetDictFromListWithKeyValue(l,key,value):
    for d in l:
        if d[key] == value: return d
    return False