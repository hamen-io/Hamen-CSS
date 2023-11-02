from termcolor import colored
import re

from Common import (parse_number,tab,user_file)

class Throw:
    def __init__(self, message: str, error: str = "SyntaxError"):
        message = re.sub(r"((\$T)(\{\d+\})?)", lambda m : tab * (2 + int((parse_number(m.group(3)) or 1))), message)

        print(colored(
            f"""
Traceback, most recent call:
{tab}An error occurred in "{user_file}":
{tab}{tab}{error}: {message}

              """.strip(), "red")
        )

        exit()

    def assertError(condition: bool, message: str = "", error: str = "AssertionError"):
        if not condition:
            Throw(message, error)