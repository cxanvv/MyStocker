from datetime import datetime

def GetDictFromListWithKeyValue(l,key,value):
    for d in l:
        if d[key] == value: return d
    return False

def DeltaDateInDays(start,end):
    start_date = datetime.strptime(start, "%d/%m/%Y")
    end_date = datetime.strptime(end, "%d/%m/%Y")
    delta = end_date - start_date
    return delta.days
