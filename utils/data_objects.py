#!/usr/bin/env python3

from pathlib import Path
from dataclasses import dataclass
from typing import List, Union


@dataclass
class DataPaths:
    root: Path
    raw: Path
    processed: Path
    input: Path
    model: Path

    def validate(self):
        return self.root.exists() and self.raw.exists() \
               and self.processed.exists() and self.input.exists() \
               and self.model.exists()

    def mkdirs(self):
        self.root.mkdir(parents=True, exist_ok=True)
        self.raw.mkdir(parents=True, exist_ok=True)
        self.processed.mkdir(parents=True, exist_ok=True)
        self.input.mkdir(parents=True, exist_ok=True)
        self.model.mkdir(parents=True, exist_ok=True)


@dataclass
class ONMTArguments:
    preprocess: dict
    train: dict
    translate: dict

    def unpack(self, name: str, string=False) -> Union[str, List[str]]:
        result = []
        try:
            for opt, arg in getattr(self, name).items():
                opt = f"--{opt}"
                if isinstance(arg, bool) and arg:
                    result.extend([opt])
                else:
                    result.extend((opt, str(arg)))
        except (KeyError, ValueError) as e:
            print(f'Some error occurred: {e}')

        if string:
            return ' '.join(result)
        return result


@dataclass
class Configuration:
    root: Path
    data_paths: DataPaths
    onmt_args: ONMTArguments
    trunc_limit: int = 1000
    temp_path: Path = Path('/tmp/')

    def validate(self):
        return self.root.exists() and self.data_paths.validate()
