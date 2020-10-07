from pathlib import Path
from typing import List


class PatchFile:
    def __init__(self, target_file: str, path: Path, changes: List[str]):
        self.path = path
        self.target_file = target_file
        self.changes = changes

    def __str__(self):
        return '@@\n'.join(self.changes)


class Patch:
    def __init__(self, number: int, root_path: Path):
        self.number = number
        self.patch_files = {}
        self.root_path = root_path
        self.compiles = None
        self.compile_time = 0
        self.neg_tests = []
        self.pos_tests = []
        self.is_fix = None

    def add(self, patch_file: PatchFile):
        self.patch_files[patch_file.target_file] = patch_file

    def __call__(self, is_fix: bool):
        self.is_fix = is_fix

    def __iter__(self):
        # since list is already iterable
        return (pf for pf in self.patch_files.values())

    def __str__(self):
        return ' '.join([str(pf.path) for pf in self])


class Test:
    def __init__(self, name: str):
        self.name = name
        self.passed = None
        self.exec_time = 0

    def __str__(self):
        return self.name
