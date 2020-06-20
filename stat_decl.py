import parser_v as p
d=open("decl_all.txt").read().splitlines()
dd=[l[57:-1].replace("\\n", "\n") for l in d]



res = []
for decl in dd:
    try:
        subtype = p.parse_declaration(decl)[2]['subtype']
    except:
        subtype = "unknown"

    res.append(subtype)
