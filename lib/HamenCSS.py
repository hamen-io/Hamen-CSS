import os
import re
import inspect

flip_bracket = lambda bracket : "(" if bracket == ")" else "[" if bracket == "]" else "{" if bracket == "}" else None

class Match:
    VARIABLE = r"[a-zA-Z_][a-zA-Z_0-9]*"

class Token:
    def __init__(self):
        self.real = None
        self.value = None
        self.globals = dict()

    @staticmethod
    def match(value: str):
        return False

    @staticmethod
    def new(value: str):
        return Token()

class Tokens:
    class Selector(Token):
        def __init__(self, selector, validate, _type, globals: dict = dict()):
            self.globals = globals

    class Property(Token):
        def __init__(self, css_property, validate, _type, globals: dict = dict()):
            self.globals = globals

    class FontFace(Token):
        def __init__(self, info, globals: dict = dict()):
            self.globals = globals

    class StyleSheet(Token):
        def __init__(self, styles, globals: dict = dict()):
            self.globals = globals
            print(styles.value)

    class Type(Token):
        def __init__(self, match_regex, globals: dict = dict()):
            self.globals = globals

    class String(Token):
        def __init__(self, string: str, globals: dict = dict()):
            self.value = string
            self.real = string
            self.globals = globals

        def __str__(self):
            return str(self.value)

        @staticmethod
        def new(value: str, globals: dict = dict()):
            value = value.strip()
            assert Tokens.String.match(value, globals)
            value = value[1:-1]

            return Tokens.String(value, globals)

        @staticmethod
        def match(value: str, globals: dict = dict()):
            return re.match(r"^\"(.*)\"$", value)

    class Array(Token):
        def __init__(self, array: list, globals: dict = dict()):
            self.value = array
            self.real = array
            self.globals = globals

        def __str__(self):
            return str(self.value)

        @staticmethod
        def new(value: str, globals: dict = dict()):
            value = value.strip()
            assert Tokens.Array.match(value, globals)

            def parse_level(code: str) -> list:
                assert re.findall(r"^\[.*\]$", code)
                code = code[1:-1]
                is_str = False
                depth = {"{": 0, "[": 0}
                depth_size = lambda depth : sum([depth[k] for k in depth])
                array = [""]
                for i,char in enumerate(code):
                    if char == "\"":
                        if is_str and code[i-1] != "\\": is_str = False
                        else: is_str = True

                    if not is_str:
                        if char in "{[":
                            depth[char] += 1
                        elif char in "}]":
                            depth[flip_bracket(char)] -= 1
                        elif char in [",", "\n"] and depth_size(depth) == 0:
                            array.append("")
                            continue

                    array[-1] += char

                new_list = list()
                for value in array:
                    new_list.append(Tokens.parse_token(value.strip(), globals))

                array = new_list
                return array

            return Tokens.Array(parse_level(value), globals)

        @staticmethod
        def match(value: str, globals: dict = dict()):
            return re.match(r"^\[.*\]$", value)

    class Object(Token):
        def __init__(self, obj: dict, globals: dict = dict()):
            self.value = obj
            self.real = obj
            self.globals = globals

        def __str__(self):
            return str(self.value)

        @staticmethod
        def new(value: str, globals: dict = dict()):
            value = value.strip()
            assert Tokens.Object.match(value, globals)

            def parse_level(code: str) -> dict:
                assert re.findall(r"^\{.*\}$", code)
                code = code[1:-1]
                is_str = False
                depth = {"{": 0, "[": 0}
                depth_size = lambda depth : sum([depth[k] for k in depth])
                obj = dict()
                is_key = True
                stack = ["", ""]
                for i,char in enumerate(code):
                    if char == "\"":
                        if is_str and code[i-1] != "\\": is_str = False
                        else: is_str = True

                    if not is_str:
                        if char in "{[":
                            depth[char] += 1
                        elif char in "}]":
                            depth[flip_bracket(char)] -= 1
                        elif char == ":" and depth_size(depth) == 0:
                            is_key = False
                        elif char in [",", "\n"] and depth_size(depth) == 0:
                            is_key = True
                            obj[stack[0]] = stack[1]
                            stack = ["", ""]
                            continue

                    if is_key:
                        stack[0] += char
                    else:
                        stack[1] += char


                new_obj = dict()
                for k,v in obj.items():
                    v = v.strip()
                    k = k.strip()
                    if Tokens.Object.match(v, globals):
                        new_obj[k] = parse_level(v)
                    else:
                        if v.startswith(":"):
                            v = v[1:].strip()

                        new_obj[Tokens.parse_token(k, globals)] = Tokens.parse_token(v, globals)

                obj = new_obj

                return obj

            return Tokens.Object(parse_level(value), globals)

        @staticmethod
        def match(value: str, globals: dict = dict()):
            return re.match(r"^\{.*\}$", value)

    class Boolean(Token):
        def __init__(self, boolean: bool, globals: dict = dict()):
            self.value = str(boolean)
            self.real = boolean
            self.globals = globals

        def __str__(self):
            return str(self.value)

        @staticmethod
        def new(value: str, globals: dict = dict()):
            value = value.strip()
            assert Tokens.Boolean.match(value, globals)
            value = value == "true"

            return Tokens.Boolean(value, globals)

        @staticmethod
        def match(value: str, globals: dict = dict()):
            return value in ["true", "false"]

    class RegEx(Token):
        def __init__(self, expression: str, globals: dict = dict(), **flags):
            self.value = expression
            self.real = expression
            self.flags = flags
            self.globals = globals

        def __str__(self):
            return str(self.value)

        @staticmethod
        def new(value: str, globals: dict = dict()):
            value = value.strip()
            match = Tokens.RegEx.match(value, globals)
            assert match
            expression,flags = list(match.groups())

            return Tokens.RegEx(expression, globals, IGNORE_CASE = "i" in flags, GLOBAL = "g" in flags)

        @staticmethod
        def match(value: str, globals: dict = dict()):
            m = re.match(r"^(?!.*ii)(?!.*gg)r\"(.*)\"([ig]{0,2})$", value)
            if m:
                return m if Tokens.String.match("\"" + m.group(1) + "\"", globals) else None

            return m

    def parse_token(value: str, globals: dict = dict()):
        value = value.strip()
        for method in dir(Tokens):
            if not method.startswith("__") and method != "parse_token":
                target = getattr(Tokens, method)
                if target.match(value):
                    return target.new(value)

        if value in globals:
            return globals[value]

        return None

class HamenCSS:
    def __init__(self, code: str):
        self.code = code
        self.code = self._squo_to_dquo(self.code)
        self.globals = dict()

    def _squo_to_dquo(self, value: str) -> str:
        def replace_single_quotes(match):
            return '"' + match.group(1) + '"'

        return re.sub(r"'([^'\\]*(\\.[^'\\]*)*)'", replace_single_quotes, value)

    def _split_code(self, code: str) -> list[str]:
        depth_counts = {"(": 0, "{": 0, "[": 0}
        code_blocks = [""]
        is_str = False
        depth = lambda counts : sum([counts[k] for k in counts])

        for char in code:
            code_blocks[-1] += char

            if char == '"':
                is_str = not is_str
            if is_str:
                continue

            if char in "({[":
                depth_counts[char] += 1
            elif char in ")}]":
                depth_counts[flip_bracket(char)] -= 1

            if depth(depth_counts) == 0 and all(count == 0 for count in depth_counts.values()) and char in ["\n", ";"]:
                code_blocks[-1] = code_blocks[-1][:-1]
                code_blocks.append("")

        code_blocks = [self._remove_whitespace(x.strip()) for x in code_blocks if x.strip() != ""]
        return code_blocks

    def _remove_whitespace(self, code: str) -> str:
        is_str = False
        clean_code = ""
        for i,char in enumerate(code):
            if char == "\"" and code[i-1] != "\\":
                clean_code += char
                is_str = not is_str
                continue

            if is_str:
                clean_code += char
            elif not re.findall(r"\s", char) or (char == " " and code[i+1] != " "):
                clean_code += char

        return clean_code

    def _inherit_globals(self, globals: dict, erase: bool = False):
        if erase: self.globals = dict()
        for k,v in globals.items():
            self.globals[k] = v

    def init(self) -> str:
        code = self._split_code(self.code)
        for i,line in enumerate(code):
            startswith = lambda string : re.match(r"^" + string, line.strip())

            if startswith(r"import\s"):
                match = re.match(r"^import\s+\{\s*(\*|(" + Match.VARIABLE + r"\s*\,\s*)+(" + Match.VARIABLE + r")?)\s*\}\s+from(\s+\".*\")", line)
                if match:
                    match = list(filter(lambda x : x, list(match.groups())))

                assert match and len(match) >= 2, f"Invalid syntax for import statement: \"{line}\""

                target,module = match[0],match[-1]
                module = Tokens.String.new(module, self.globals).real

                file_source = None
                if not os.path.splitext(module)[-1]:
                    module += ".hcss"

                if module.startswith("./"):
                    pass
                else:
                    assert module in os.listdir(os.path.dirname(__file__)), f"File: \"{module}\" does not exist"

                    file_source = os.path.join(os.path.dirname(__file__), module)

                source_content = None
                with open(file_source, "r") as f:
                    source_content = f.read()

                globals = HamenCSS(source_content)
                globals.init()
                globals = globals.globals

                target = re.sub(r"\s", "", target).split(",")
                if target == ["*"]:
                    pass
                else:
                    assert all([t in globals for t in target]), f"Could not import, \"{', '.join(target)}\" from source file: \"{module}\""

                self._inherit_globals(globals)

            elif any([
                startswith(x)
                    for x in ["Selector", "Type", "Property", "FontFace", "StyleSheet"]
            ]):
                kwd = re.split(r"\s", line, 1)[0]
                match = re.match(r"^" + kwd + r"\s+(" + Match.VARIABLE + r")\s*=([\s\S]*[\S+])", line)
                assert match, f"Invalid {kwd} declaration: \"{line}\""

                name,value = [x.strip() for x in list(match.groups())]

                # Evaluate value:
                if value.startswith("new "):
                    self.globals[name] = self._evaluate_instance_creation(value)

                elif value in self.globals:
                    self.globals[name] = self.globals[value]

                elif value.lower().startswith(kwd.lower()):
                    raise SyntaxError(f"Cannot create an instance of \"{kwd}\" without using the `new` keyword")

                else:
                    raise SyntaxError(f"Unknown value: \"{value}\"")

            else:
                raise SyntaxError(f"Invalid line: \"{line}\"")

        return ""

    def _evaluate_instance_creation(self, value: str):
        match = re.match(r"new\s+(" + Match.VARIABLE + r")\s*(\(.*\)$)", value)
        assert match, f"Invalid declaration syntax"
        type,arguments = [x.strip() for x in list(match.groups())]
        tokens = [x for x in dir(Tokens) if not (x.startswith("__") or x.endswith("__"))]
        if type not in tokens:
            raise SyntaxError(f"Unknown class: \"{type}\"")

        type = getattr(Tokens, type)

        kwargs = self._parse_arguments(arguments, inspect.signature(type).parameters)
        return type(**kwargs)

    def _parse_arguments(self, arguments: str, base_arguments: dict) -> dict:
        arguments = arguments[1:-1]

        depth_counts = {"(": 0, "{": 0, "[": 0}
        depth = lambda counts : sum([counts[k] for k in counts])
        terms = [""]
        is_str = False
        flip_bracket = lambda bracket : "(" if bracket == ")" else "[" if bracket == "]" else "{" if bracket == "}" else None

        for char in arguments:
            terms[-1] += char

            if char == '"':
                is_str = not is_str
            if is_str:
                continue

            if char in "({[":
                depth_counts[char] += 1
            elif char in ")}]":
                depth_counts[flip_bracket(char)] -= 1

            if depth(depth_counts) == 0 and all(count == 0 for count in depth_counts.values()) and char == ",":
                terms[-1] = terms[-1][:-1]
                terms.append("")

        terms = [self._remove_whitespace(x.strip()) for x in terms if x.strip() != ""]

        kwargs = base_arguments
        kwargs = {k: None for k,v in kwargs.items()}
        for term in terms:
            term = term.strip()

            # Keyword argument:
            if re.findall(r"^\s*" + Match.VARIABLE + r"\s*=\s*[\s\S]*", term):
                key,value = term.split("=", 1)
                assert key in kwargs, f"Argument given, but not accepted: \"{key}\""
                kwargs[key] = self._parse_value(value)
            else:
                found = False
                for arg,_value in kwargs.items():
                    if not _value:
                        kwargs[arg] = self._parse_value(term)
                        found = True
                        break

                if not found:
                    raise SyntaxError(f"Extra parameter found: \"{term}\"")

        return kwargs

    def _parse_value(self, value: str) -> any:
        real = None
        if value in self.globals:
            real = self.globals[value]
        elif Tokens.RegEx.match(value, self.globals):
            real = Tokens.RegEx.new(value, self.globals)
        elif Tokens.String.match(value, self.globals):
            real = Tokens.String.new(value, self.globals)
        elif Tokens.Boolean.match(value, self.globals):
            real = Tokens.Boolean.new(value, self.globals)
        elif Tokens.Object.match(value, self.globals):
            real = Tokens.Object.new(value, self.globals)
        elif Tokens.Array.match(value, self.globals):
            real = Tokens.Array.new(value, self.globals)
        else:
            if value.startswith("new "):
                real = self._evaluate_instance_creation(value)

            raise SyntaxError(f"Invalid type: \"{value}\"")

        return real

with open(r"lib\test.hcss", "r") as f:
    HamenCSS(f.read()).init()