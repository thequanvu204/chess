def negateTuple(a : tuple) -> tuple:
    return((-(a[0]),-(a[1])))

def sumTuple(a,b) -> tuple:
    return (a[0]+b[0],a[1]+b[1])

def compareTuple(a,b):
    if (a[0] == b[0] and a[1] == b[1]):
        return 0
    if (a[0] <= b[0] and a[1] <= b[1]):
        return -1
    if (a[0] < b[0] and a[1] < b[1]):
        return 1  
    if (a[0] >= b[0] and a[1] >= b[1]):
        return -2
    if (a[0] > b[0] and a[1] > b[1]):
        return 2
    
    return None