global user_file,tab
tab = "    "
user_file = "..."
em = "—"

def xextend(original_array: list, extension: list, at_index: int = -1, replace = False) -> list:
    """
    ```
    extend([1, 2, 3], ["h", "e", "l", "l", "o"], 1)
    # Output: [1, "h", "e", "l", "l", "o", 2, 3]
    ```

    When `replace` is True, it replaces the term at `at_index`
    """

    if at_index < 0:
        at_index = len(original_array) + at_index

    assert at_index < len(original_array), "index exceeds length of array"

    left = original_array[:at_index]
    right = original_array[at_index + (1 if replace else 0):]

    new_array = left + extension + right

    return new_array

def lrange(array: list) -> range:
    return range(len(array))

def xequals(array_1: list, array_2: list, order_matters: bool = False) -> bool:
    if order_matters:
        array_1 = array_1.sort()
        array_2 = array_2.sort()

    if len(array_1) != len(array_2):
        return False
    
    for i,value in enumerate(array_1):
        if value != array_2[i]:
            return False

    return True

def xfilter(array: list, values: list = []) -> list:
    """
    Removes non-None values in `array` if they are not in `values`
    """

    array = [x for x in array if x and x not in values and (x.strip() if type(x) is str else True)]
    return array

def parse_number(number: str) -> float:
    try:
        float(number)
        return float(number)
    except:
        return None