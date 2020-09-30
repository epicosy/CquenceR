#!/usr/bin/env python3

from pathlib import Path
from typing import NoReturn

from utils.command import Command


class Train(Command):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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
        # cmd_parser.add_argument('-sp', '--src_path', help='Source dataset path.', type=str, required=None)
        # cmd_parser.add_argument('-op', '--out_path', help='Destination path.', type=str, default=None)
        # cmd_parser.add_argument('-s', '--split', help='Split dataset.', choices=list_of_split_choices, default=None)
        # cmd_parser.add_argument('-tl', '--truncation_limit', help='Truncation limit for the number of tokens.', type=int,
        #                        choices=[500, 1000, 1500], default=500)
        pass
