#!/usr/bin/env python3

import re


def replacer(match):
    s = match.group(0)
    if s.startswith('/'):
        return " "  # note: a space and not an empty string
    else:
        return s


pattern = re.compile(
    r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
    re.DOTALL | re.MULTILINE
)


def remove_comments(code: str):
    return re.sub(pattern, replacer, code)



