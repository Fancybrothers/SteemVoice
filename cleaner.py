def clean(str):
    newstr = str.replace("VESTS","")
    str = newstr
    newstr = str.replace(" ","")
    str = newstr
    newstr = str.replace(",","")
    str = newstr
    newstr = str.replace("STEEM","")
    str = newstr
    newstr = str.replace("SBD","")
    return(newstr)