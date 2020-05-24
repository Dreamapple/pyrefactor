

DEBUG_MACRO = 1


import re
from pprint import pprint


class Source:
    def __init__(self, file, pos, line_no, line_pos):
        self.file = file
        self.pos = pos
        self.line_no = line_no
        self.line_pos = line_pos


class Symbol(dict):
    def __init__(self, name, sources=[], origins=[]):
        self.name = name
        self.sources = sources
        self.origins = origins


class SymbolTable(dict):
    def __init__(self, parent):
        self.parent = parent

class SymbolTableTree:
    def __init__(self):
        self.symtab = SymbolTable(None)

    def create(self, name, source, origin):
        s = self.symtab[name] = Symbol(name, source, origin)
        return s

    def push(self):
        self.symtab = SymbolTable(parent=self.symtab)

    def pop(self):
        self.symtab = self.symtab.parent

    def __getitem__(self, name):
        symtab = self.symtab
        while symtab:
            if name in symtab:
                return symtab[name]
            symtab = symtab.parent
    def __setitem__(self, name, value):
        return self.symtab.__setitem__(name, value)


g_source = Source("", 0, 0, 0)
m_symtab = SymbolTableTree()

g_symtab = {
    "bool" : [],
    "void" : None,
    "char" : None,
    "auto" : None,
    "long" : None,
    "short": None,
    "int"  : None,
    "T"    : None,
    "unsigned": None,
    "double": None,
    "float": None,
    "signed": None,
    "__int128": None,
    "__float128": None,
    "wchar_t": None,
    "char16_t": None,
    "char32_t": None,
    # "__float128": None,
    # "__float128": None,
    # "__float128": None,
}

def dump_g_symtab():
    with open("__temp_g_symtab.py", 'w') as f:
        pprint(g_symtab, stream=f)

def load_g_symtab():
    global g_symtab
    with open("__temp_g_symtab.py") as f:
        g_symtab = eval(f.read())


def read_identifier(s, pos):
    m = re.match(r"[\w_][\w\d_]*", s[pos:])
    assert m
    token = m.group()
    return pos + m.end(), token


# https://stackoverflow.com/questions/15679756/g-e-option-output
# "# linenum filename flags"

# The linenum specifies that the following line originated in filename at that line number. 
# Then there are four flags:

# 1 - Start of a new file
# 2 - Returning to a file
# 3 - System header file
# 4 - Treat as being wrapped in extern "C"
# So let's interpret your linemarker:

# # 91 "/usr/include/stdint.h" 3 4
# The following line originated from line 91 of /usr/include/stdint.h. 
# It is a system header file and should be treated as wrapped in extern "C".


def parse_macro(s, qualname="<anonymous>", pos=0, line=1):
    assert s[pos] == '#'
    pos_t = s.find('\n', pos)
    m = re.match(r'\# (\d+) "([^"]*?)"', s[pos:pos_t])
    if m:
        line = int(m.group(1))
        qualname = m.group(2)
        return pos_t, line, s[pos:pos_t]
    m = re.match(r'\#\s*([\w_][\w\d_]*)', s[pos:pos_t])
    if m:
        return pos_t, line + 1, s[pos:pos_t]
    
    raise Exception(s[pos:pos_t])


def parse_comment(s, qualname="<anonymous>", pos=0, line=1):
    if s[pos:pos+2] == '//':
        pos_t = s.find('\n', pos) + 1
        line += 1
    elif s[pos:pos+2] == '/*':
        pos_t = s.find('*/', pos) + 2
        line += s[pos:pos_t].count('\n')
    return pos_t, line, ["comment", s[pos:pos_t]]

def parse_typedef(s, qualname="<anonymous>", pos=0, line=1, decorate=[]):
    pos_t = find(s, ';', pos) + 1
    # assert pos_t == s.find(';', pos+1) + 1, s[pos:pos_t]
    origin = s[pos:pos_t]
    line += origin.count('\n')
    name = origin[:-1].split()[-1]
    # todo!!
    if not re.fullmatch(r"[\w_][\w\d_]*", name):
        for k in re.findall(r"[\w_][\w\d_]*", origin):
            if k not in g_symtab:
                name = k
    g_symtab[name] = []
    source = Source("<anonymous file>", pos, line, 0)
    symbol = m_symtab.create(name, source, origin)

    print("[#] parse_typedef", 'result line:', origin)
    print("[#] parse_typedef", 'result name:', name)
        # while pos_t < len(s):
        #     if s[pos_t] in ' \t\n':
        #         pos_t += 1
        #     elif s[pos_t] == ';':
        #         pos_t += 1
        #         break
        #     else:
        #         p_end = s.find(';', pos_t)
        #         decl_names = re.findall(r"[\w_][\w\d_]*", s[pos_t:p_end])
        #         for name in decl_names:
        #             g_symtab[name] = None
        #         pos_t = p_end

    return (pos_t, line, {"type": "typedef", "namespace": qualname + '::' + '<name>', "decorate": decorate, "origin": s[pos:pos_t]})

def parse_using(s, qualname="<anonymous>", pos=0, line=1, decorate=[]):
    pos_t = s.find(';', pos+1) + 1
    line += s[pos:pos_t].count('\n')
    name = s[pos+5:pos_t-1].split('=', 1)[0].strip()
    g_symtab[name] = []
    print("[#]parse_typedef", 'line:', s[pos:pos_t])
    print("[#]parse_typedef", 'name:', name)
    return (pos_t, line, {"type": "using", "namespace": qualname + '::' + '<name>', "decorate": decorate, "origin": s[pos:pos_t]})

def split(s, sep=','):
    r = []
    l = p = 0
    while p < len(s):
        pp = find(s, sep, p)
        if pp != -1:
            r.append(s[l:pp])
            l = p = pp + 1
        else:
            break
    r.append(s[l:])        
    return r

DEBUG = 0
def find(s, sub_token, pos, care_angle_brackets=False):
    """
    寻找符号
    但是跳过()、[]、{}、字符串、注释
    如果care_angle_brackets为True，那么考虑<>作为括号的情况
    """
    if DEBUG: print("find(s=%r, sub_token=%r)"%(s[pos:pos+200], sub_token))
    stack = []  # synbol stack
    p = pos   # pos of now
    if isinstance(sub_token, (list, tuple)):
        sub_token_t = '|'.join("(%s)"%re.escape(k) for k in sub_token)
    else:
        sub_token_t = "(%s)"%re.escape(sub_token)
    match = re.compile(sub_token_t).match

    while p < len(s):
        if DEBUG: print(stack, p, repr(s[p]))
        if s[p] in '({[':
            if not stack and s[p] in sub_token:
                return p
            stack.append(s[p])
        elif s[p] in ')}]':
            if not stack and s[p] in sub_token:
                return p
            assert stack.pop() + s[p] in ['()', '{}', '[]']
        elif s[p] in ['"', "'"]:
            pp = p + 1
            while pp < len(s):
                if DEBUG: print("        ", repr(s[pp]))
                if s[pp] == s[p]:
                    break
                if s[pp] == '\\':
                    pp += 1
                pp += 1
            if DEBUG: print("""------> (s[p]  in ['"', "'"]) is True, skip %r""" % s[p:pp])
            p = pp
        elif s[p] == '/':
            if s[p+1] == '/':
                p = s.find('\n', p+2)
            elif s[p+1] == '*':
                p = s.find('*/', p+2) + 1
        elif s[p] in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_":
            m = re.match(r"[\w_][\w\d_]*", s[p:])
            token = m.group()
            p += m.end()
            if token == "operator":
                if s[p:p+2] in ['==', '<=', '>=', '!=', "+=", "-=", "()", "|=", "&=", "^="]:
                    p += 2
                if s[p] in ['=', '<', '>', '!', "+", "-", "|", "&", "~", "^"]:
                    p += 1

            p -= 1
        elif care_angle_brackets and s[p] == '<':
            if s[p] in sub_token:
                return p
            pp = p - 1
            while s[pp] in ' \n\t\r':
                pp -= 1
            ppp = pp
            while s[ppp] in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_1234567890":
                ppp -= 1
            if s[ppp+1] in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_":
                token = s[ppp+1:pp+1]
                if token == 'operator':
                    p += 1
                    continue
                print("[#] g_find check %r in g_symtab -> %s"%(token, token in g_symtab))
                if token == 'template' or token in g_symtab:
                    stack.append('<')
        elif care_angle_brackets and s[p] == '>':
            if not stack and s[p] in sub_token:
                return p
            if stack and stack[-1] == '<':
                stack.pop()
        elif not stack and match(s[p:]):
            return p
        p += 1
    return -1

def parse_template_decl(d):
    c = split(d, ',')
    for decl_item in c:
        dd = decl_item.strip()
        print("[#]    parse_template_decl", "template_decl:", dd)
        if dd.startswith('class'):
            name = dd[5:].strip().split('=', 1)[0].strip()
            g_symtab[name] = None
            print("[#]    parse_template_decl", "name:", name)
        elif dd.startswith('typename'):
            name = dd[8:].strip().split('=', 1)[0].strip()
            g_symtab[name] = None
            print("[#]    parse_template_decl", "name:", name)
        else:
            # todo
            pass
        


def parse_template(s, qualname="<anonymous>", pos=0, line=1, decorate=[]):
    template_decl_beg = find(s, '<', pos, care_angle_brackets=True)
    template_decl_end = find(s, '>', template_decl_beg + 1, care_angle_brackets=True)
    assert template_decl_beg != -1
    assert template_decl_end != -1
    pos_t = template_decl_end + 1
    line += s[pos:pos_t].count('\n')
    # re.match(r"")
    # g_symtab[name] = {}
    print("[#] parse_template:", s[pos:pos_t])
    decl = s[template_decl_beg+1:template_decl_end]
    parse_template_decl(decl)
    return (pos_t, line, {"type": "template", "namespace": qualname, "decorate": decorate, "origin": s[pos:pos_t]})
    # if s[pos_t:].strip().startswith('class'):
    #     parse_class(s, qualname, pos, line, decorate + ['template'])
    # else:
    #     assert False, s[pos_t:pos_t+20]

def parse_alignas(s, qualname="<anonymous>", pos=0, line=1, decorate=[]):
    beg = find(s, '(', pos)
    end = find(s, ')', beg + 1)
    assert beg != -1
    assert end != -1
    pos_t = end + 1
    line += s[pos:pos_t].count('\n')

    print("[#] parse_alignas:", s[pos:pos_t])

    return (pos_t, line, {"type": "alignas", "namespace": qualname, "origin": line})

def consume_class_init_list(s, p):
    """
    1. val(some)
    2. val{some}
    3. val{ }, val{ } \n { }
    """
    while True:
        p = find(s, ['{', ';'], p)
        if s[p] == ';': return p
        pp = find(s, '}', p+1) + 1
        while s[pp] in "\t \n\r\f\v":
            pp += 1
        # val{ } \n { }
        if s[pp] == '{':
            return pp
        # val{ } , ...
        if s[pp] == ',':
            p = pp
            continue
        return p




def parse_declaration(s, qualname="<anonymous>", pos=0, line=1, decorate=[], is_constructor=False, class_name=None):
    """
    如果遇到一个"类型"token，说明接下来是一个声明
    这个声明有以下几种情况：
    1. TYPE value;
    2. TYPE value = (1<2);
    3. char *(*next)();
    4. const char *str[10];
    5. char *(* test[10])(int p);
    6. TYPE<TYPE> (*signal(int sig, void(*func)(int)))(int);
    7. TYPE value();
    """
    print(f"[#] parse_declaration, is_constructor={is_constructor}, meet line: {s[pos:pos+200]!r}")
    # step 1. 确定声明部分边界
    # '=' : TYPE value = ...;
    if is_constructor:
        p_mid = find(s, ['=', '{', ';', ':'], pos, care_angle_brackets=True)
        if s[p_mid] == ':':
            p_mid = consume_class_init_list(s, p_mid+1)

    else:
        p_mid = find(s, ['=', '{', ';'], pos, care_angle_brackets=True)
    assert p_mid != -1
    print("[#] parse_declaration", "decl line:", s[pos:p_mid])

    if not is_constructor:
        names = re.findall(r"[\w_][\w\d_]*", s[pos:p_mid])
        func_name = None
        for name in names:
            if name not in g_symtab and name not in ["operator", "const", "noexcept"]:
                break
        g_symtab[name] = s[pos:p_mid]
        print("[#] parse_declaration", "decl name:", name)
    else:
        name = class_name

    if s[p_mid] == '=':
        s_end = find(s, ';', p_mid+1)
    elif s[p_mid] == '{':
        s_end = find(s, '}', p_mid+1)
    elif s[p_mid] == ';':
        s_end = p_mid
    else:
        assert False, (s[p_mid], s[p_mid:p_mid+20])
    assert s_end != -1

    line += s[pos:s_end+1].count("\n")
    pos_t = s_end+1
    print("[#] parse_declaration", "body:", s[p_mid:s_end+1])
    return (pos_t, line, {"type": "declaration", "namespace": qualname + '::' + name, "decorate": decorate, "origin": s[pos:s_end+1]})

def find_pair_brace(s, pos, c):
    assert s[pos] == c
    c_pair = {'{':'}', '[':']', '(':')'}[c]
    st = 1
    po = pos + 1
    while st:
        if s[po] == c:
            st += 1
            po += 1
        elif s[po] == c_pair:
            st -= 1
            po += 1
        elif s[po:po+1] == '//':
            po = s.find('\n', po)
            if po == -1:
                raise Exception
        elif s[po:po+1] == '/*':
            po = s.find('*/', po)
            if po == -1:
                raise Exception
        else:
            po += 1
    return po

def parse_class(s, qualname="<anonymous>", pos=0, line=1, decorate=[]):
    # pos_t0 = find(s, ';', pos)
    m = re.match(r'(class|struct|union)\s+(__attribute\ \(\(__abi_tag__\ \("cxx11"\)\)\)\ )?([\w_][\w\d_]*)?\s*([^{;]*)({|;)', s[pos:])
    assert m, s[pos:pos+200]
    class_or_struct = m.group(1)
    name = m.group(3)
    if name is None:
        name = "<anonymous>"
    qualname_t = qualname + '::' + name
    assert m.end() == len(m.group())
    pos_t = pos + m.end()
    line += m.group().count('\n')
    g_symtab[name] = None
    print(f"[#] [parse_class] {name!r} class_or_struct={class_or_struct}")
    print(f"[#]     g_symtab add {name!r}")

    if m.group()[-1] == '{':
        pos_t, line, node = parse_scope(s, qualname_t, pos_t, line, is_class=True, class_name=name)
        while pos_t < len(s):
            if s[pos_t] in ' \t\n':
                pos_t += 1
            elif s[pos_t] == ';':
                pos_t += 1
                break
            else:
                p_end = s.find(';', pos_t)
                decl_names = re.findall(r"[\w_][\w\d_]*", s[pos_t:p_end])
                for name in decl_names:
                    g_symtab[name] = None
                pos_t = p_end

    else:
        node = None
    return (pos_t, line, {"type": class_or_struct, "namespace": qualname_t, "decorate": decorate, "origin": node})


def parse_namespace(s, qualname="<anonymous>", pos=0, line=1, decorate=[]):
    m = re.match(r"namespace\s+([\w_][\w\d_]*)([^{]*){", s[pos:])
    assert m, s[pos:pos+20]
    name = m.group(1)
    g_symtab[name] = "namespace"
    qualname_t = qualname + '::' + m.group(1)
    assert m.end() == len(m.group())
    pos_t = pos + m.end()
    line += m.group().count('\n')
    pos_t, line, root = parse_scope(s, qualname_t, pos_t, line)
    return (pos_t, line, {"type": "namespace", "namespace": qualname_t, "decorate": decorate, "origin": root})


def parse_extern(s, qualname="<anonymous>", pos=0, line=1, decorate=[]):
    # extern "C++" { ... }
    m = re.match(r'extern\s+"[^"]+?"[\s\n]*{', s[pos:], re.I)
    if m:
        assert m.end() == len(m.group())
        pos_t = pos + m.end()
        line += m.group().count('\n')
        pos_t, line, root = parse_scope(s, qualname, pos_t, line)
        return (pos_t, line, {"type": "extern", "namespace": qualname, "decorate": decorate, "origin": root})

    # extern "C++" int a;
    m = re.match(r'extern\s+"[^"]+?"', s[pos:], re.I)
    if m:
        assert m.end() == len(m.group())
        pos_t = pos + m.end()
        line += m.group().count('\n')
        pos_t, line, root = parse_declaration(s, qualname, pos_t, line)
        return (pos_t, line, {"type": "extern", "namespace": qualname, "decorate": decorate, "origin": root})

    # extern "C++" int a;
    m = re.match(r'extern ', s[pos:], re.I)
    if m:
        assert m.end() == len(m.group())
        pos_t = pos + m.end()
        line += m.group().count('\n')
        pos_t, line, root = parse_declaration(s, qualname, pos_t, line)
        return (pos_t, line, {"type": "extern", "namespace": qualname, "decorate": decorate, "origin": root})
    raise
    

def parse_enum(s, qualname="<anonymous>", pos=0, line=1, decorate=[]):
    # m = re.match(r'enum\s+([^\s]+?)\s*{', s[pos:])
    # assert m, s[pos:pos+20]
    # qualname_t = qualname + '::' + m.group(1)
    # assert m.end() == len(m.group())
    pos_t = find(s, ';', pos) + 1
    assert pos_t > pos
    origin = s[pos:pos_t]
    name = origin.split('{', 1)[0][4:].strip()
    if name:
        if name.startswith('class '):
            name = name[6:]
        name = re.match(r"[\w_][\w\d_]*", name).group()
        g_symtab[name] = None
    print("[#] parse_enum", name)

    line += origin.count('\n')
    return (pos_t, line, {"type": "enum", "namespace": "<enum>", "decorate": decorate, "origin": s[pos:pos_t]})

def parse_static_assert(s, qualname="<anonymous>", pos=0, line=1, decorate=[]):
    pos_t = s.find(';', pos) + 1
    line += s[pos:pos_t].count('\n')
    return (pos_t, line, {"type": "static_assert", "namespace": qualname, "decorate": decorate, "origin": s[pos:pos_t]})

# enum scope_type:
#     kFile,
#     kNamespace,
#     kClass,
#     kFunction,
#     kMethod,
#
def parse_scope(s, qualname="<anonymous>", pos=0, line=1, decorate=[], is_class=False, class_name=None, scope_type=kFile):
    print(f"[#] parse_scope, is_class={is_class}, class_name={class_name!r}")
    root = []
    decorate_t = []
    while pos < len(s):
        if s[pos] == '}':
            pos += 1
            print("[#] parse_scope", "meet '}', return", "pos=%s, line=%s, content=%s"%(pos, line, s[pos:pos+200]))
            # raise
            return pos, line, root
        if s[pos] == '\n':
            line += 1
            pos += 1
        
        elif s[pos] == ' ':
            pos += 1
        elif s[pos] == '#':
            pos_t, line, node = parse_macro(s, qualname, pos, line)
            pos = pos_t
            root.append(node)
        elif s[pos:pos+2] in ['//', '/*']:
            pos_t, line, node = parse_comment(s, qualname, pos, line)
            pos = pos_t
            root.append(node)
        elif s[pos] in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_":
            pos_t1, token = read_identifier(s, pos)
            # 关键字的优先级最高
            if token == "namespace":
                pos_t, line, node = parse_namespace(s, qualname, pos, line, decorate_t)
                root.append(node)
                decorate_t = []
            elif token in ['class', 'struct', 'union']:
                pos_t, line, node = parse_class(s, qualname, pos, line, decorate_t)
                decorate_t = []
                root.append(node)
            elif token == "extern":
                pos_t, line, node = parse_extern(s, qualname, pos, line, decorate_t)
                root.append(node)
                decorate_t = []
            elif token == "enum":
                pos_t, line, node = parse_enum(s, qualname, pos, line, decorate_t)
                root.append(node)
                decorate_t = []
            elif token == "template":
                pos_t, line, node = parse_template(s, qualname, pos, line, decorate_t)
                decorate_t.append(node)
            elif token == "alignas":
                pos_t, line, node = parse_alignas(s, qualname, pos, line, decorate_t)
                decorate_t.append(node)
            elif token == "typedef":
                pos_t, line, node = parse_typedef(s, qualname, pos, line, decorate_t)
                decorate_t = []
                root.append(node)
            elif token == "using":
                pos_t, line, node = parse_using(s, qualname, pos, line, decorate_t)
                decorate_t = []
                root.append(node)
            elif token in ["mutable", "inline", "constexpr", "static", "typename", "const", "explicit", "friend", "virtual"]:
                decorate_t.append(token)
                pos_t = pos + len(token)
            elif token in ["__inline", "__extension__"]:
                decorate_t.append(token)
                pos_t = pos + len(token)
            elif token == "__attribute":
                if s[pos:].startswith('__attribute ((__abi_tag__ ("cxx11")))'):
                    pos_t = pos + len('__attribute ((__abi_tag__ ("cxx11")))')
                    decorate_t.append('__attribute ((__abi_tag__ ("cxx11")))')
                else:
                    assert False, s[pos:pos+200]
            elif is_class and token == class_name:
                pos_t, line, node = parse_declaration(s, qualname, pos, line, decorate_t, is_constructor=True, class_name=class_name)
                decorate_t = []
                root.append(node)
            elif token in ["operator"] or token in g_symtab:
                pos_t, line, node = parse_declaration(s, qualname, pos, line, decorate_t)
                decorate_t = []
                root.append(node)
            elif token in ["static_assert"]:
                pos_t, line, node = parse_static_assert(s, qualname, pos, line, decorate_t)
                decorate_t = []
                root.append(node)
            elif token in ["public", "private", "protected"]:
                node = {"type": "class_specifier", "origin": token}
                pos_t = pos + len(token)
                while s[pos_t] in ' \t\n\r':
                    pos_t += 1
                if s[pos_t] == ':':
                    pos_t += 1

            else:
                raise ValueError("Token %r not know, line is %r"%(token, s[pos:pos+200]))
            assert pos < pos_t, (pos, pos_t, s[pos], s[pos:pos+200])
            pos = pos_t

        elif s[pos] == '~':
            decorate_t.append('~')
            pos += 1
        elif s[pos] == '[':
            if s[pos:].startswith("[["):
                pos_t = s.find(']]', pos+2)+2
                origin = s[pos:pos_t]
                decorate_t.append(origin)
                pos = pos_t
            else:
                assert False, (s[pos], s[pos:pos+200])
        elif s[pos] == ';':
            pos += 1
            assert not decorate_t
        else:
            assert False, (s[pos], s[pos:pos+200])

    return pos, line, root


def parse_file(s, qualname="<anonymous>", pos=0, line=1):
    return parse_scope(s, qualname, pos, line)


content = r"""


"""
if 1:
    import sys
    if content.strip():
        load_g_symtab()
    elif len(sys.argv) > 1:
        content = sys.argv[1]
        print("[#]parse_file content:", content)
    else:
        content = open("file.c++").read()

    try:
        t = parse_file(content, "file.c++")
    except:
        dump_g_symtab()
        raise

    pprint(t[-1])

if __name__ == '__main__':
    t = parse_file(content, "file.c++")
    pprint(t)