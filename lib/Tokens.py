from Throw import Throw

import re

class Tokens:
    class Token:
        def __init__(self, value: str = "") -> None:
            self.token_name = "TOKEN"
            self.raw_value: str = None
            self.value: str = value

        @staticmethod
        def regex() -> str:
            """
            Returns a regular expression to match this token
            """

            return ""

        def __str__(self) -> str:
            return self.token_name

        @staticmethod
        def parse(value: str) -> 'Tokens.Token':
            """
            Parses `value`, then returns it as this token
            """

            return Tokens.Token(value)

    class String(Token):
        def __init__(self, value: str = "") -> None:
            super().__init__()
            self.token_name = "STRING"
            self.value = value

        @staticmethod
        def parse(value: str) -> 'Tokens.String':
            return Tokens.String(value)

    class Value(Token):
        def __init__(self) -> None:
            super().__init__()
            self.token_name = "VALUE"
            self.number: float = 0
            self.unit: str = "px"
            self.value = str(self.number) + str(self.unit)

        @staticmethod
        def parse(value: str) -> 'Tokens.Value':
            v = Tokens.Value()
            m = re.findall(Tokens.Value.regex(), value)
            assert len(m) == 1
            m = m[0]
            assert len(m) == 3
            m = list(m)

            sign,number,unit = m

            def parse_number(number: str) -> float | int:
                try:
                    float(number)
                    if "." in number and number.split(".")[-1].replace("0", "") != "":
                        return float(number)
                    return int(number)
                except:
                    return None

            number = (parse_number(number)) * (-1 if sign == "-" else 1)
            unit = unit.lower()

            v.number = number
            v.unit = unit
            v.value = str(number) + str(unit)

            return v

        @staticmethod
        def regex() -> str:
            return r"^(\+|\-)?(\d*\.?\d+)([a-zA-Z]{0,2})$"
        
        def render(self) -> str:
            return self.value

    class ValuePolynomial(Token):
        def __init__(self, polynomial: list = [], *, globals: dict = None) -> None:
            super().__init__()
            self.token_name = "VALUEPOLYNOMIAL"
            self.polynomial = polynomial

            if globals:
                for i,term in enumerate(polynomial):
                    if isinstance(term, Tokens.Variable):
                        term: Tokens.Variable
                        Throw.assertError(term.name in globals and globals[term.name].get("value"), f"Variable does not exist; attempted to identify a variable that has not been defined in the current scope;\n$T{{2}}variable name: '{term.name}'", "VariableIdentificationError")

                        polynomial[i] = globals[term.name]["value"]

            self.value = " ".join([x.value for x in polynomial])

        @staticmethod
        def parse(value: list, *, globals: dict = None) -> 'Tokens.ValuePolynomial':
            poly = Tokens.ValuePolynomial(value, globals = globals)
            assert all([isinstance(x, (Tokens.Value, Tokens.Symbol, Tokens.SelectorOperator, Tokens.Variable, Tokens.ArithmeticOperator)) for x in value])
            poly.polynomial = value
            poly.value = " ".join([x.value for x in value])

            return poly
        
        def render(self) -> str:
            value = re.sub(r"((?<!calc)(\())", r"calc(", self.value)
            def clean_value(original_value: str) -> str:
                value = re.sub(r"(\()\s+|\s+(\))", r"\2\1", original_value)
                if original_value == value:
                    return value
                return clean_value(value)

            return clean_value(value)

    class Variable(Token):
        def __init__(self, name: str = "") -> None:
            super().__init__()
            self.token_name = "VARIABLE"
            self.value = name
            self.name = name

        @staticmethod
        def regex() -> str:
            return r"^(\w(?<![0-9])+\w*)$"

        @staticmethod
        def parse(value: str) -> 'Tokens.Variable':
            return Tokens.Variable(value)

    class Selector(Token):
        def __init__(self, selector: str = "") -> None:
            super().__init__()
            self.token_name = "SELECTOR"
            self.value = selector

        @staticmethod
        def regex() -> str:
            return r"^([\#\.])(\w(?<![0-9])+\w*)"

        @staticmethod
        def parse(value: str) -> 'Tokens.Selector':
            return Tokens.Selector(value)

    class PseudoElement(Token):
        def __init__(self, element: str = "") -> None:
            super().__init__()
            self.token_name = "PSEUDO"
            self.value = element

        @staticmethod
        def regex() -> str:
            return r"^(\:)(\w(?<![0-9])+\w*)"

        @staticmethod
        def parse(value: str) -> 'Tokens.PseudoElement':
            return Tokens.PseudoElement(value)

    class SelectorOperator(Token):
        def __init__(self, operator: str = "") -> None:
            super().__init__()
            self.token_name = "SELECTOROPERATOR"
            self.value = operator

        @staticmethod
        def regex() -> str:
            return r"^([>,~+])$"

        @staticmethod
        def parse(value: str) -> 'Tokens.SelectorOperator':
            return Tokens.SelectorOperator(value)

    class Keyword(Token):
        def __init__(self) -> None:
            super().__init__()
            self.token_name = "KEYWORD"

    class Import(Keyword):
        def __init__(self) -> None:
            super().__init__()
            self.token_name = "IMPORT"

        @staticmethod
        def parse(value: str) -> 'Tokens.Import':
            return Tokens.Import()

        @staticmethod
        def regex() -> str:
            return r"^(import)\s+"

    class Let(Keyword):
        def __init__(self) -> None:
            super().__init__()
            self.token_name = "LET"

        @staticmethod
        def regex() -> str:
            return r"^(let)\s+"

        @staticmethod
        def parse(value: str) -> 'Tokens.Let':
            return Tokens.Let()

    class Package(Keyword):
        def __init__(self) -> None:
            super().__init__()
            self.token_name = "PACKAGE"

        @staticmethod
        def regex() -> str:
            return r"^(package)\s+"

        @staticmethod
        def parse(value: str) -> 'Tokens.Package':
            return Tokens.Package()

    class Const(Keyword):
        def __init__(self) -> None:
            super().__init__()
            self.token_name = "CONST"

        @staticmethod
        def regex() -> str:
            return r"^(const)\s+"

        @staticmethod
        def parse(value: str) -> 'Tokens.Const':
            return Tokens.Const()

    class Symbol(Token):
        def __init__(self) -> None:
            super().__init__()
            self.token_name = "SYMBOL"
            self.symbol: str = ""
            self.value = self.symbol

    class Equals(Symbol):
        def __init__(self) -> None:
            super().__init__()
            self.token_name = "EQUALS"
            self.symbol: str = "="
            self.value = "="

        @staticmethod
        def parse(value: str) -> 'Tokens.Equals':
            return Tokens.Equals()

    class Colon(Symbol):
        def __init__(self) -> None:
            super().__init__()
            self.token_name = "COLON"
            self.symbol: str = ":"
            self.value = ":"

        @staticmethod
        def parse(value: str) -> 'Tokens.Colon':
            return Tokens.Colon()

    class OBrace(Symbol):
        def __init__(self) -> None:
            super().__init__()
            self.token_name = "OBRACE"
            self.symbol: str = "{"
            self.value = "{"

        @staticmethod
        def parse(value: str) -> 'Tokens.OBrace':
            return Tokens.OBrace()

    class CBrace(Symbol):
        def __init__(self) -> None:
            super().__init__()
            self.token_name = "CBRACE"
            self.symbol: str = "}"
            self.value = "}"

        @staticmethod
        def parse(value: str) -> 'Tokens.CBrace':
            return Tokens.CBrace()

    class OBracket(Symbol):
        def __init__(self) -> None:
            super().__init__()
            self.token_name = "OBRACKET"
            self.symbol: str = "("
            self.value = "("

        @staticmethod
        def parse(value: str) -> 'Tokens.OBracket':
            return Tokens.OBracket()

    class CBracket(Symbol):
        def __init__(self) -> None:
            super().__init__()
            self.token_name = "CBRACKET"
            self.symbol: str = ")"
            self.value = ")"

        @staticmethod
        def parse(value: str) -> 'Tokens.CBracket':
            return Tokens.CBracket()

    class OSquareBracket(Symbol):
        def __init__(self) -> None:
            super().__init__()
            self.token_name = "OSQUAREBRACKET"
            self.symbol: str = "["
            self.value = "["

        @staticmethod
        def parse(value: str) -> 'Tokens.OSquareBracket':
            return Tokens.OSquareBracket()

    class CSquareBracket(Symbol):
        def __init__(self) -> None:
            super().__init__()
            self.token_name = "CSQUAREBRACKET"
            self.symbol: str = "]"
            self.value = "]"

        @staticmethod
        def parse(value: str) -> 'Tokens.CSquareBracket':
            return Tokens.CSquareBracket()

    class Ampersand(Symbol):
        def __init__(self) -> None:
            super().__init__()
            self.token_name = "AMP"
            self.symbol: str = "&"
            self.value = "&"

        @staticmethod
        def parse(value: str) -> 'Tokens.Ampersand':
            return Tokens.Ampersand()

    class SelectorSymbol(Symbol):
        def __init__(self) -> None:
            """ char literal : `$` """

            super().__init__()
            self.token_name = "SELECTORSYMBOL"
            self.symbol: str = "$"
            self.value = "$"

        @staticmethod
        def parse(value: str) -> 'Tokens.SelectorSymbol':
            return Tokens.SelectorSymbol()

    class ForwardSlash(Symbol):
        def __init__(self) -> None:
            """ char literal : `/` """

            super().__init__()
            self.token_name = "FORWARDSLASH"
            self.symbol: str = "/"
            self.value = "/"

        @staticmethod
        def parse(value: str) -> 'Tokens.ForwardSlash':
            return Tokens.ForwardSlash()

    class ArithmeticOperator(Token):
        def __init__(self, symbol: str = "") -> None:
            super().__init__()
            self.token_name = "ARITHMETIC"
            self.symbol: str = symbol
            self.value = symbol

        @staticmethod
        def parse(value: str) -> 'Tokens.ArithmeticOperator':
            return Tokens.ArithmeticOperator(value)
        
        @staticmethod
        def regex() -> str:
            operators = ["+", "-", "*", "/"]
            operators = "".join([fr"\{x}" for x in operators])

            return r"^([" + operators + r"])$"

def identify_token(token: str) -> Tokens.Token | None:
    if isinstance(token, Tokens.Token):
        return type(token)
    elif type(token) is not str:
        raise TypeError(f"Type of token is not string: '{type(token)}'")

    token = token.lower()
    match token:
        case "&": return Tokens.Ampersand
        case "{": return Tokens.OBrace
        case "}": return Tokens.CBrace
        case "(": return Tokens.OBracket
        case ")": return Tokens.CBracket
        case "[": return Tokens.OSquareBracket
        case "]": return Tokens.CSquareBracket
        case ":": return Tokens.Colon
        case "=": return Tokens.Equals
        case "$": return Tokens.SelectorSymbol
        case "/": return Tokens.ForwardSlash
        case "const": return Tokens.Const
        case "let": return Tokens.Let
        case "import": return Tokens.Import
        case "package": return Tokens.Package
        case _:
            if re.findall(Tokens.Variable.regex(), token): return Tokens.Variable
            if re.findall(Tokens.Selector.regex(), token): return Tokens.Selector
            if re.findall(Tokens.SelectorOperator.regex(), token): return Tokens.SelectorOperator
            if re.findall(Tokens.PseudoElement.regex(), token): return Tokens.PseudoElement
            if re.findall(Tokens.Value.regex(), token): return Tokens.Value
            if re.findall(Tokens.ArithmeticOperator.regex(), token): return Tokens.ArithmeticOperator

    return None

def camel_to_kebab(variable: str) -> str:
    """ `myVar` -> `my-var` """

    return "".join([x.lower() + "-" if x.isupper() else x for x in list(variable)])

class CSSRule:
    def __init__(self, css_selector: str, css_declarations: dict):
        self.selector = css_selector
        self.declarations = css_declarations

    def __str__(self) -> str:
        return f"""{self.selector} {{{";".join([camel_to_kebab(k) + ":" + v for k,v in self.declarations.items()])}}}"""

def parse_selector(selector_list: list[Tokens.Selector, Tokens.PseudoElement]) -> str:
    """
    Creates a CSS selector from a hcss-selector
    """

    css_selector = [x.value for x in selector_list]

    Throw.assertError(not re.findall(r"(\[[^\[\]]*?\[[^\[\]]*?\][^\[\]]*?\])", "".join(css_selector)), f"Nested groups detected; selector groups cannot be nested with sub-groups;\n$T{{2}}selector : '{''.join(css_selector)}'")

    terms = [[None]]
    i = 0
    while i < len(selector_list):
        term = selector_list[i]

        if type(terms[-1][-1]) is list:
            if term.value != "]":
                if term.value != ",":
                    terms[-1][-1].append(term)
            else:
                terms[-1].append(None)

        elif term.value == "[":
            terms[-1].append([])

        elif term.value == ":":
            terms[-1].append(Tokens.PseudoElement(":" + selector_list[i+1].value))
            i += 2
            continue

        elif term.value == "/":
            if selector_list[i+1].value == ">":
                terms[-1].append(Tokens.SelectorOperator("/>"))
                i += 2
                continue
            else:
                assert False

        elif term.value in ["~", "+", ">"]:
            terms[-1].append(Tokens.SelectorOperator(term.value))

        elif term.value == ",":
            terms.append([None])
        
        else:
            assert isinstance(term, (Tokens.Selector, Tokens.Variable)), term
            terms[-1].append(Tokens.Selector(term.value))

        i += 1

    terms = [[x for x in y if x] for y in terms]
    selectors = terms

    for selector in selectors:
        def generate_selector_permutations(_selector):
            if not _selector:
                return [""]
            
            result = []

            if isinstance(_selector[0], str):
                current_selectors = [_selector[0]]
                remaining_permutations = generate_selector_permutations(_selector[1:])
                
                for selector in current_selectors:
                    for perm in remaining_permutations:
                        result.append(f"{selector} {perm}")

            elif isinstance(_selector[0], list):
                for sub_group in _selector[0]:
                    sub_group_permutations = generate_selector_permutations([sub_group] + _selector[1:])
                    result.extend(sub_group_permutations)

            return result

        selector = [x.value if type(x) is not list else [y.value for y in x] for x in selector]
        css_selector += generate_selector_permutations(selector)

    css_selector = ["".join(x) for x in css_selector]
    exit(css_selector)

    return css_selector