from pathlib import Path
from typing import List, Tuple
import Levenshtein


class DatasetAnalyzer:
    def __init__(self, src: Path, tgt: Path, verbose: bool = False):
        self.verbose = verbose

        if not src.exists():
            raise ValueError(f"{src.name} not found")
        if not tgt.exists():
            raise ValueError(f"{tgt.name} not found")

        with src.open(mode="r") as s:
            self.source = [line.split() for line in s.readlines()]

        with tgt.open(mode="r") as t:
            self.target = [line.split() for line in t.readlines()]

        self.src_tgt = zip(self.source, self.target)

    def token_counts(self) -> Tuple[List, List]:
        tokens_mapping = {}

        for line in self.source:
            for token in line:
                if token in ['<TAB>', '<NEW_LINE>', '<START_VULN>', '<END_VULN>']:
                    continue
                if token in tokens_mapping:
                    tokens_mapping[token] += 1
                else:
                    tokens_mapping[token] = 1

        tokens, values = zip(*tokens_mapping.items())
        size = len(tokens_mapping)

        if self.verbose:
            print(f"Unique tokens: {size}")

        # tokens, counts, size
        return tokens, values

    def tokens_per_line(self, tgt: bool = False):
        if tgt:
            return [len(line) for line in self.target]
        return [len(line) for line in self.source]

    def hunk_size(self):
        total = {'1': 0, '2': 0, '3': 0, '4-10': 0, '11+': 0}
        no_vuln = 0

        for line in self.source:
            if '<START_VULN>' not in line:
                no_vuln += 1
                continue
            start_vuln = line.index('<START_VULN>')
            end_vuln = line.index('<END_VULN>')
            hunk = line[start_vuln: end_vuln]
            count = hunk.count('<NEW_LINE>')

            if count == 1:
                total['1'] += 1
            elif count == 2:
                total['2'] += 1
            elif count == 3:
                total['3'] += 1
            elif 4 <= count <= 10:
                total['4-10'] += 1
            else:
                total['11+'] += 1

        if self.verbose:
            print(f"Hunks with no special tokens: {no_vuln}")

        return total

    def similarity(self):
        return [Levenshtein.ratio(' '.join(src), ' '.join(tgt)) for src, tgt in self.src_tgt]
