#!/usr/bin/env python3

from pathlib import Path
from typing import NoReturn

from utils.command import Command


class Train(Command):
    def __init__(self, gpu: bool = False, **kwargs):
        super().__init__(**kwargs)
        if gpu:
            self.config.onmt_args.train['gpu_ranks'] = 0
        self.in_path = self.configs.data_paths.input
        self.out_path = self.configs.data_paths.model

    def __call__(self, **kwargs):
        out, err, _ = super().__call__(command=f"command -v onmt_train > /dev/null; echo $?;", exit_err=True)

        if out.splitlines()[0] != '0':
            print(f"onmt_train not found: install OpenNMT-py")
            exit(1)

        mutable_args = self.configs.onmt_args.unpack(name='train', string=True)
        cmd_str = f"onmt_train -data {self.in_path / Path('final')} {mutable_args} " \
                  f"-save_model {self.out_path / Path('final-model')} 2>&1"
        print(cmd_str)
        out, err, _ = super().__call__(command=cmd_str,
                                       file=Path(self.out_path / Path('train.final.out')))

        if err:
            self.status('train: something went wrong.')
            exit(1)

    @staticmethod
    def definition() -> dict:
        return {'name': 'train',
                'command': Train,
                'description': "Trains a model from the preprocessed dataset files."}

    @staticmethod
    def add_arguments(cmd_parser) -> NoReturn:
        cmd_parser.add_argument('--gpu', action='store_true', default=False, help='Enables GPU training.')
