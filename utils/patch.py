from pathlib import Path


class Patch:
    def __init__(self, name: str, path: Path, change: str):
        self.path = path
        self.name = name
        self.change = change
        self.compiles = None
        self.compile_time = 0
        self.neg_tests = []
        self.pos_tests = []
        self.is_fix = None

    def __call__(self, is_fix: bool):
        self.is_fix = is_fix

    def __str__(self):
        return self.change


class Test:
    def __init__(self, name: str):
        self.name = name
        self.passed = None
        self.exec_time = 0

    def __str__(self):
        return self.name
