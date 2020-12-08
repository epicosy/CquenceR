from pathlib import Path
from typing import Hashable

from utils.processing.c_tokenizer import truncate, tokenize
from pandas import DataFrame


class InputDataset:
    def __init__(self, name: str, dataset: DataFrame, target_path: Path, column="hunk"):
        self.name = name
        self.dataset = dataset
        self.column = column
        self.target_path = target_path
        self.src = Path(target_path, f"src-{name}.txt")
        self.tgt = Path(target_path, f"tgt-{name}.txt")
        self.tmp = Path(target_path, f"{name}-tmp.txt")
        self.to_drop = []
        self.processed = 0

    def write(self, trunc_limit: int = None):
        with self.src.open(mode="a", encoding="utf-8") as src, self.tgt.open(mode="a", encoding="utf-8") as tgt, \
                self.tmp.open(mode="a", encoding="utf-8") as tmp:

            for index, row in self.dataset.iterrows():
                source_tokens, target_tokens = tokenize(row[self.column])

                if trunc_limit and len(source_tokens) > trunc_limit:
                    source_tokens = truncate(source_tokens, trunc_limit)

                    if not source_tokens:
                        self._drop(index=index)
                        continue

                try:
                    tmp.write(source_tokens.strip() + '\n')
                except Exception as e:
                    print(e)
                    self._drop(index=index)
                    continue

                if source_tokens.strip() == "":
                    self._drop(index=index)
                    continue

                src.write(source_tokens.strip() + '\n')
                tgt.write(target_tokens.strip() + '\n')

                self.processed += 1
                print(f"{self.name} - Count: {index+1}; " +
                      f"Processed: {self.processed}", end='\r')
        print('\n')
        self.dataset.drop(self.dataset.index[self.to_drop], inplace=True)
        print(f"{self.name}: Dropped {len(self.to_drop)} records.\n")

        self.tmp.unlink()

        return self.processed, len(self.to_drop)

    def _drop(self, index: Hashable):
        print(f"{self.name}: No source tokens for record {index}")
        self.to_drop.append(index)

    def save(self, name):
        self.dataset.to_pickle(f"{self.target_path}/{name}_{self.name}.pkl")
