#!/usr/bin/env python3

import subprocess
import sys
import time


from pathlib import Path
from typing import Tuple, Union, AnyStr, List
from abc import ABCMeta

from utils.config import Configuration


class Command(object):
    __metaclass__ = ABCMeta

    def __init__(self,
                 name: str,
                 configs: Configuration,
                 log_file: str = None,
                 seed: int = 0,
                 verbose: bool = False,
                 **kwargs):
        self.name = name
        self.configs = configs
        self.verbose = verbose
        self.seed = seed
        self.log_file = Path(log_file) if log_file else log_file

        if kwargs:
            self.log(f"Unknown arguments: {kwargs}\n")

    def __call__(self,
                 command: Union[str, List],
                 cwd: str = None,
                 file: Path = None,
                 exit_err: bool = False) -> Tuple[Union[str, None], Union[str, None], float]:
        if self.verbose:
            print(command)
        # based on https://stackoverflow.com/a/28319191
        with subprocess.Popen(args=command,
                              shell=isinstance(command, str),
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              cwd=cwd) as proc:
            exec_time = time.time()
            out, err = self._exec(proc, file=file if file else self.log_file)
            exec_time = time.time() - exec_time

            if exit_err and err:
                exit(proc.returncode)

            return out, err, exec_time

    def _exec(self, proc: subprocess.Popen, file: Path = None) -> Tuple[str, Union[str, None]]:
        out = []
        err = None

        for line in proc.stdout:
            decoded = line.decode()
            out += decoded

            if self.verbose:
                print(decoded, end='')

            if file:
                tmp = self.log_file
                self.log_file = file
                self.log(decoded)
                self.log_file = tmp
        proc.wait(timeout=1)
        if proc.returncode and proc.returncode != 0:
            proc.kill()
            err = proc.stderr.read().decode()

            if not err:
                err = f"Return code: {proc.returncode}"

            if self.verbose:
                print(err, file=sys.stderr)

            if file and err:
                tmp = self.log_file
                self.log_file = file
                self.log(err)
                self.log_file = tmp

        return ''.join(out), err

    def log(self, msg: AnyStr):
        if self.log_file and msg:
            with self.log_file.open(mode="a") as lf:
                lf.write(msg)

    def status(self, message: str):
        print(message)
        self.log(message)

    def __str__(self):
        return self.name
