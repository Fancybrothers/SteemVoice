import math

def rep_cal(rep):
    def log10(string):
        leading_digits = int(string[0:4])
        log = math.log10(leading_digits) + 0.00000001
        num = len(string) - 1
        return num + (log - int(log))

    rep = str(rep)
    if rep == "0":
        return 25

    sign = -1 if rep[0] == '-' else 1
    if sign < 0:
        rep = rep[1:]

    out = log10(rep)
    out = max(out - 9, 0) * sign  
    out = (out * 9) + 25       
    return round(out, 2)