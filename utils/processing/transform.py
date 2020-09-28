import re
from typing import List, Union

from utils.processing.code import remove_comments

START_TOKEN = "<START_VULN>"
END_TOKEN = "<END_VULN>"

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


def tokenizer(code):
    tokenized: List[str] = []

    # Remove comments
    code = remove_comments(code)
    # code = codecs.getdecoder("unicode_escape")(code)[0]
    # Remove newlines & tabs
    code = re.sub('(\n)|(\\\\n)|(\\\\)|(\\t)|(/)|(\\r)', '', code)

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


def tokenize(snippet: str):
    hunk_file_lines = snippet.split('\n')

    source_hunk = []
    target_line = ""

    for line in hunk_file_lines:
        if line.startswith("-"):
            source_hunk.append("TOKENIZER_START_VULN " + line.replace('-', ' ', 1).strip() +
                               "TOKENIZER_END_VULN ")
        elif line.startswith("+"):
            target_line = line.replace('+', ' ', 1).strip()
        else:
            source_hunk.append(line.strip() + " ")

    tokens = tokenizer(''.join(source_hunk))
    source_tokens = ' '.join(tokens)

    source_tokens = source_tokens.replace("TOKENIZER_START_VULN", START_TOKEN)
    source_tokens = source_tokens.replace("TOKENIZER_END_VULN", END_TOKEN)

    tokens = tokenizer(target_line)
    target_tokens = ' '.join(tokens)

    return source_tokens, target_tokens


def tokenize_vuln(snippet: List[str], vuln_line: int):
    source_hunk = []

    for i, line in enumerate(snippet):
        if i+1 == vuln_line:
            source_hunk.append("TOKENIZER_START_VULN " + line.replace('-', ' ', 1).strip() + "TOKENIZER_END_VULN ")
        else:
            source_hunk.append(line.strip() + " ")

    tokens = tokenizer(''.join(source_hunk))
    source_tokens = ' '.join(tokens)

    source_tokens = source_tokens.replace("TOKENIZER_START_VULN", START_TOKEN)
    source_tokens = source_tokens.replace("TOKENIZER_END_VULN", END_TOKEN)

    return source_tokens
