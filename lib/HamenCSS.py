from Throw import Throw
from Common import *
from Tokens import (Tokens,identify_token,parse_selector,CSSRule,camel_to_kebab)

import os
import re
import string
import colorama
from termcolor import colored

class HamenCSS:
    def __init__(self, code: str, tokenize: bool = True, execute: bool = True) -> None:
        self.package_name: str = None
        self.external_packages: list = []
        self.globals: dict = dict()
        self.tokens = list[Tokens.Token]

        self.code = str(code).replace("\n", "")
        if tokenize:
            self.tokens = self.tokenize(self.code)
            if execute:
                self.globals = self.execute_code(self.tokens)

    def execute_code(self, lines: list[list[str | Tokens.String]], globals: dict = dict()) -> dict:
        for i,tokens in enumerate(lines):
            line = ":".join([x.__str__() for x in tokens])
            line_t = line.split(":")

            if re.findall(r"^(PACKAGE)", line):
                # Ensure package is registered at top of file:
                Throw.assertError(i == 0, f"Package declaration below top-level; packages can only be registered at the top of a file.", "PackageRegistrationError")
                
                # Do nothing since the package declaration functionality is implemented in the tokenization method

            elif re.findall(r"^(IMPORT)", line):
                Throw.assertError(type(self.package_name) is str, f"Unregistered package import; import-statements cannot be used in unregistered-packages;\n$T{{2}}try naming the package with the `package` keyword")
                Throw.assertError(len(line_t) == 2, f"Not enough values; import-statements should specify exactly one term: the module;\n$T{{2}}parameters found: '{len(line_t) - 1}'.", "ImportError")

                path = tokens[1]
                path: Tokens.Token
                Throw.assertError(type(path) is Tokens.String, f"Invalid path data-type; import-statements should have exactly one string-typed path;\n$T{{2}}path-type found: '{path.token_name.capitalize()}' [val. '{path.raw_value}'].")

                path: Tokens.String
                hcss_file = path.value
                filetype = os.path.splitext(hcss_file)[-1]
                if filetype == "":
                    filetype = ".hcss"
                    hcss_file += ".hcss"

                Throw.assertError(filetype.lower() == ".hcss", f"Invalid filetype; import-statements should import an `hcss` file;\n$T{{2}}path specified: '{filetype}' [path. '{hcss_file}']")
                Throw.assertError(os.path.exists(hcss_file) and os.path.isfile(hcss_file), f"Import file not found; attempted to import an `.hcss` file that does not exist;\n$T{{2}}path specified: '{hcss_file}'")

                with open(hcss_file, "r") as file:
                    hcss = HamenCSS(file.read(), execute = False)
                    if hcss.package_name == self.package_name:
                        Throw(f"Imported parent package; attempted to import the current Main package\n$T{{2}}imported package: '{hcss_file}' [name. '{hcss.package_name}']", "ImportError")

                    hcss = HamenCSS(file.read(), execute = True)
                    for k,v in hcss.globals.items():
                        if k.get(v) and k[v]["const"] == True:
                            Throw(f"Import file constant interference; attempted to import a file that includes variables that overwrites constant files in this file's global scope\n$T{{2}}constant variable affected: '{k}'", "ImportError")

                        globals[k] = v
            
            elif re.findall(r"^(LET|CONST)", line):
                Throw.assertError(line.startswith((
                        "LET:VARIABLE:EQUALS:",     # 'let' syntax
                        "CONST:VARIABLE:EQUALS:"    # 'const' syntax
                    )), f"Invalid syntax for variable declaration; attempted to define a variable without the necessary semantic syntax", "VariableDeclarationError")

                scope,name,eq,*value = tokens
                scope: Tokens.Let
                name: Tokens.Variable
                eq: Tokens.Equals

                Throw.assertError(type(name) is Tokens.Variable and name.value != "throw", f"Variable name is reserved; attempted to declare a variable with a reserve keyword\n$T{{2}}variable name: '{name.raw_value}'", "ReservedKeywordError")
                Throw.assertError(not globals.get(name.name), f"Variable already exist; attempted to declare a variable that already exists\n$T{{2}}variable name: '{name.name}'", "VariableDeclarationError")

                if len(value) == 1:
                    value = value[0]
                    value: Tokens.Value
                else:
                    value = Tokens.ValuePolynomial.parse(value, globals = globals)
                    value: Tokens.ValuePolynomial

                globals[name.name] = dict({
                    "scope": scope.token_name,
                    "value": value
                })

            elif line.startswith("VARIABLE:"):
                # Re-assign variable:
                if line.startswith("VARIABLE:EQUALS:"):
                    # Get variable and value:
                    variable: Tokens.Variable = tokens[0]
                    value: list[Tokens.Value] = tokens[2:]

                    # Assign non-existent variable:
                    Throw.assertError(variable.name in globals, f"Cannot re-assign non-existent variable; attempted to re-assign a variable that does not exist in the current scope;\n$T{{2}}variable: '{variable.name}'")

                    # Assign constant variable:
                    Throw.assertError(globals[variable.name]["scope"] == "LET", f"Constant re-assignment; attempted to re-assign a constant variable;\n$T{{2}}variable: '{variable.name}'")

                    # Make value a polynomial if more than one terms;
                    #   if one term, just make value equal the first term
                    value = Tokens.ValuePolynomial.parse(value) if len(value) > 1 else value[0]

                    # Modify globals with the new value:
                    globals[variable.name]["value"] = value

                else:
                    pass

            elif line.startswith("SELECTORSYMBOL:"):
                split = line.split(":").index("OBRACE")
                selector,declarations = tokens[:split],tokens[split:]

                # Blank selector:
                Throw.assertError(len(selector) > 3, f"Blank selector; attempted to create a blank selector", "BlankSelectorError")

                # Transform the selector to an actual CSS selector:
                selector = parse_selector(selector[2:-1])

                print(selector)

            else:
                pass

        return globals

    def tokenize(self, code: str) -> list[Tokens.Token]:
        tokens = []

        # Separate strings:
        string_pattern = r"(\"|')(.*?(?<!\\))\1"
        string_matches = re.finditer(string_pattern, code)
        start = 0
        for match in string_matches:
            tokens.append(code[start:match.start()])
            tokens.append(Tokens.String(match.group(0)[1:-1]))
            start = match.end()
        tokens.append(code[start:])

        # Separate tokens:
        i = 0
        while i < len(tokens):
            term = tokens[i]
            if type(term) is str:
                # Remove whitespace:
                term = term.strip()
                term = re.sub(r"\s+", " ", term)
                term = re.sub(r"(?<=\W)\s+(?=\w)|(?<=\w)\s+(?=\W)|(?<=\W)\s+(?=\W)", "", term)

                # Separate symbols:
                match_symbols = [
                    r"(\W(?!\w))",
                    r"([\{\}\[\]\(\)\,\;\s])",
                    r"((?<=\w)[^\w\.](?=\w))",
                    r"([\+\-\/\*])"
                ]

                term = re.split("|".join(match_symbols), term)

                term = xfilter(term)
                tokens = xextend(tokens, term, i, True)

                i += len(term)

                continue

            i += 1

        # Group tokens by lines (defined by ";")
        #   this also groups items inside {}
        grouped_tokens = [[]]
        depth = 0
        for i,term in enumerate(tokens):
            if term in list("{}"):
                depth += 1 if term == "{" else -1

                if depth == 0:
                    grouped_tokens[-1].append(term)
                    grouped_tokens.append([])
                elif depth == 1 and term == "{":
                    grouped_tokens.append(["{"])
                else:
                    grouped_tokens[-1].append(term)

                continue

            if depth != 0:
                grouped_tokens[-1].append(term)
            elif term == ";":
                grouped_tokens.append([])
            else:
                grouped_tokens[-1].append(term)

        grouped_tokens = xfilter(grouped_tokens)

        # Tokenize EACH term in the line:
        tokens = []
        dependent = 0 # When >= 1, a dependency is created where the next line is appended to the previous line
        for line in grouped_tokens:
            if dependent:
                dependent -= 1
            else:
                tokens.append([])

            for i,token in enumerate(line):
                if token == ";":
                    continue
                elif type(token) is Tokens.String:
                    tokens[-1].append(token)
                    continue

                value = token
                token = identify_token(value)
                if not token:
                    Throw(f"Fatal syntax error; invalid token;\n$T{{2}}token: '{value.__str__()}'", "SyntaxError")

                token = token.parse(value)
                token: Tokens.Token
                token.raw_value = value

                if token.token_name == "SELECTORSYMBOL":
                    dependent += 1

                tokens[-1].append(token)

        # Name package;
        #   this is done before the code is executed as when external files
        #   are imported, their package name is first found, then the code
        #   is executed
        if tokens and tokens[0] and tokens[0][0].__str__() == "PACKAGE":
            # Ensure package name is specified
            Throw.assertError(len(tokens[0]) == 2, f"Not enough values; packages must be registered with exactly one specified string-name;\n$T{{2}}parameters found: '{len(tokens[0]) - 1}'.", "PackageRegistrationError")

            # Ensure that package name is Tokens.String
            package_name = tokens[0][1]
            package_name: Tokens.Token
            Throw.assertError(type(package_name) is Tokens.String, f"Invalid package-name data-type; package names should be defined as strings;\n$T{{2}}path-type found: '{package_name.token_name.capitalize()}' [val. '{package_name.raw_value}'].")

            # Get package name:
            package_name: Tokens.String
            package_name = package_name.value

            # Ensure that package name is valid:
            Throw.assertError(re.findall(r"^([a-zA-Z_]+[a-zA-Z0-9_]*)$", package_name), f"Invalid package-name; package names must follow the pattern: `^[a-zA-Z_]+\w*$`;\n$T{{2}}specified package name: '{package_name}'")

            self.package_name = package_name
            self.external_packages.append(package_name)

        return tokens

with open(r"lib\Main.hcss", "r") as file:
    user_file = os.path.split(r"lib\Main.hcss")[-1]
    HamenCSS(file.read())