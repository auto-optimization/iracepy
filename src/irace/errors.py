import re

def irace_assert(condition, message):
    # Currently just a plain assert. In the future we might add logging and change assertion error behavior to include cleanup, etc.
    assert condition, message

def check_numbers(start, end, log):
    irace_assert(not ((type(start) is int or float) and (type(end) is int or float)) or end >= start, f"lower bound must be smaller than upper bound in numeric range ({start}, {end})")
    if log:
        if (type(start) is int or float) and start <= 0 or (type(end) is int or float) and end <= 0:
            irace_assert("Domain of type 'log' cannot be non-positive")

def check_illegal_character(name):
    irace_assert(re.match("^[_a-zA-Z0-9]+$", name), f"name {repr(name)} container illegal character. THe only allowed characters are a-z, A-Z, 0-9 and _ (underscore).")
