#!/usr/bin/env python3
from pathlib import Path
from typing import NoReturn

from utils.command import Command


class Clean(Command):
    def __init__(self, command: str = None, **kwargs):
        super().__init__(**kwargs)
        self.mapping = {'train': [self.configs.data_paths.model],
                        'preprocess': [self.configs.data_paths.input, self.configs.data_paths.processed],
                        'test': [Path('/tmp', 'cquencer_test_predictions')]}
        self.commands = {command: self.mapping[command]} if command else self.mapping

    def __call__(self, **kwargs):
        for command, values in self.commands.items():
            for value in values:
                if not value.exists():
                    continue
                if value.is_dir():
                    cmd_str = f"rm -rf {value} 2>&1"
                    out, err, _ = super().__call__(command=cmd_str, file=self.out_file)

                    if err:
                        self.status('clean: something went wrong.')
                        exit(1)
                    value.mkdir(exist_ok=True)
                else:
                    value.unlink()
        self.status(f"Cleaned {' '.join(self.commands)}")

    @staticmethod
    def definition() -> dict:
        return {'name': 'clean',
                'command': Clean,
                'description': "Cleans files created from commands."}

    @staticmethod
    def add_arguments(cmd_parser) -> NoReturn:
        cmd_parser.add_argument('--command', help='Flag for specifying the command.', default=None,
                                choices=['train', 'preprocess', 'test'])
