import re
from typing import List, Union, Tuple, Dict

from utils.processing.code import remove_comments

START_TOKEN = "<START_VULN>"
END_TOKEN = "<END_VULN>"
NEW_LINE_TOKEN = "<NEW_LINE>"
TAB_TOKEN = "<TAB>"

operators3 = {'<<=', '>>='}
operators2 = {
    '->', '++', '--', '**',
    '!~', '<<', '>>', '<=', '>=',
    '==', '!=', '&&', '||', '+=',
    '-=', '*=', '/=', '%=', '&=', '^=', '|='
}
operators1 = {
    '(', ')', '[', ']', '.',
    '+', '&', '$',
    '%', '<', '>', '^', '|',
    '=', ',', '?', ':',
    '{', '}', '!', '~'
}


def to_regex(lst):
    return r'|'.join([f"({re.escape(el)})" for el in lst])


regex_split_operators = to_regex(operators3) + to_regex(operators2) + to_regex(operators1)


def truncate(source: str, limit: int) -> Union[str, None]:
    tokens = source.split()
    # VULN Tokens position
    try:
        start = tokens.index(START_TOKEN)
        end = tokens.index(END_TOKEN, start)
    except ValueError as ve:
        print(ve)
        print(source)
        return None

    # Size of the vulnerability in tokens
    vuln_size = end - start
    source_size = len(tokens)
    # Calculate the limits for truncation based on vulnerability size
    before = round(2 * (limit - vuln_size) / 3)
    after = round((limit - vuln_size) / 3)
    # Truncation start and end indexes
    start_trunc_index = start - before
    end_trunc_index = end + after
    # Truncate if context size isn't within the limit
    if start_trunc_index < 0:
        residual = abs(start_trunc_index)
        start_trunc_index = 0
        # Add the residual context if is within the limit
        if start + vuln_size + residual < limit:
            end_trunc_index += residual
            if end_trunc_index > source_size:
                end_trunc_index = source_size

    tokens = tokens[start_trunc_index:end_trunc_index]

    return ' '.join(tokens)


def tokenizer(code: str):
    tokenized: List[str] = []

    # code = codecs.getdecoder("unicode_escape")(code)[0]
    # Remove newlines & tabs
    # code = re.sub('(\n)|(\\\\n)|(\\\\)|(\\t)|(/)|(\\r)', '', code)

    for line in code.splitlines():
        if line == '':
            continue

        stripped = line.strip()

        # Mix split (characters and words)
        splitter = r' +|' + regex_split_operators + r'|(\/)|(\;)|(\-)|(\*)'
        cg = re.split(splitter, stripped)

        # Remove None type
        cg = list(filter(None, cg))
        cg = list(filter(str.strip, cg))
        # code = " ".join(code)
        # Return list of tokens
        tokenized.extend(cg)

    return tokenized


def tokenize_leading_spaces(line: str):
    removed_spaces = line.lstrip()
    strip_start = line.find(removed_spaces)

    if strip_start == 0:
        return line

    leading_spaces = line[0:strip_start]
    leading_tabs = leading_spaces.replace('    ', ' TOKENIZER_TAB ')
    tabs_escaped = leading_tabs.replace('\t', ' TOKENIZER_TAB ')

    return tabs_escaped + removed_spaces


def tokenize(snippet: str):
    no_comments = remove_comments(snippet)
    new_line_escape = no_comments.replace('\n', ' TOKENIZER_NEW_LINE \n')
    hunk_file_lines = new_line_escape.splitlines()
    source_hunk = []
    vuln_start = False
    target_line = ""

    for line in hunk_file_lines:
        if line.startswith("-"):
            if not vuln_start:
                vuln_start = True
                source_hunk.append("TOKENIZER_START_VULN ")
            source_hunk.append(tokenize_leading_spaces(line.replace('-', '', 1)).strip())
        elif line.startswith("+"):
            if vuln_start:
                source_hunk.append(" TOKENIZER_END_VULN ")
                vuln_start = False
            target_line += tokenize_leading_spaces(line.replace('+', '', 1).strip())
        else:
            if vuln_start:
                source_hunk.append(" TOKENIZER_END_VULN ")
                vuln_start = False
            source_hunk.append(tokenize_leading_spaces(line).strip() + " ")

    if vuln_start:
        source_hunk.append(" TOKENIZER_END_VULN ")

    tokens = tokenizer(''.join(source_hunk))
    source_tokens = ' '.join(tokens)
    source_tokens = replace_source_tokens(source_tokens)

    if not target_line:
        target_line += " TOKENIZER_NEW_LINE "

    tokens = tokenizer(target_line)
    target_tokens = ' '.join(tokens)
    target_tokens = target_tokens.replace("TOKENIZER_TAB", TAB_TOKEN)
    target_tokens = target_tokens.replace("TOKENIZER_NEW_LINE", NEW_LINE_TOKEN)

    return source_tokens, target_tokens


def tokenize_hunks(snippet: str, hunks: Dict[int, Tuple[int, int]], truncation_limit: int):
    # TODO: REMOVE COMMENTS
    new_line_escape = snippet.replace('\n', ' TOKENIZER_NEW_LINE \n')
    hunk_file_lines = new_line_escape.splitlines()
    source_hunks = {}
    source_tokens = []
    size_snippet = len(hunk_file_lines)

    for line in hunk_file_lines:
        source_tokens.append(tokenize_leading_spaces(line).strip() + " ")

    for h_id, hunk in hunks.items():
        start, end = hunk

        if not (start <= end < size_snippet):
            raise ValueError("Hunk sizes don't match")

        copy_source_tokens = source_tokens.copy()
        copy_source_tokens[start] = "TOKENIZER_START_VULN " + copy_source_tokens[start]
        copy_source_tokens[end] = copy_source_tokens[end] + " TOKENIZER_END_VULN "

        tokens = tokenizer(''.join(copy_source_tokens))
        string_tokens = ' '.join(tokens)
        string_tokens = replace_source_tokens(string_tokens)

        if len(tokens) > truncation_limit:
            string_tokens = truncate(string_tokens, truncation_limit)

        source_hunks[h_id] = string_tokens

    return source_hunks


def replace_source_tokens(source_tokens: str) -> str:
    source_tokens = source_tokens.replace("TOKENIZER_TAB", TAB_TOKEN)
    source_tokens = source_tokens.replace("TOKENIZER_NEW_LINE", NEW_LINE_TOKEN)
    source_tokens = source_tokens.replace("TOKENIZER_START_VULN", START_TOKEN)
    source_tokens = source_tokens.replace("TOKENIZER_END_VULN", END_TOKEN)

    return source_tokens
