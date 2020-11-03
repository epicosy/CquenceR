#!/usr/bin/env python3
from pathlib import Path
from typing import NoReturn

from utils.command import Command
from processing.pre.prepare import process_dataset

list_of_split_choices = ["train_val", "train_val_test"]


class Preprocess(Command):
    def __init__(self, src_path: str = None, out_path: str = None, split: str = None, no_onmt: bool = False,
                 no_truncation: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.source = Path(src_path) if src_path else self.configs.data_paths.raw / Path('dataset.pkl')
        self.out = Path(out_path) if out_path else self.configs.data_paths.processed
        self.onmt_input_path = self.configs.data_paths.input
        self.limit = self.configs.trunc_limit if not no_truncation else None
        self.split = split
        self.no_onmt = no_onmt
        self.no_truncation = no_truncation
        self.out_file = Path(self.onmt_input_path / Path(f"preprocess.{self.seed}.out"))

    def __call__(self, **kwargs):
        if self.source.is_dir():
            raise ValueError("Source path is not a file.")

        if self.source.suffix != '.pkl':
            raise ValueError("Source file is not a pickle file.")

        if not self.out.exists():
            self.out.mkdir(parents=True, exist_ok=True)

        process_dataset(dataset_path=self.source, out_path=self.out, truncation_limit=self.limit, split=self.split)

        if not self.no_onmt:
            out, err, _ = super().__call__(command=f"command -v onmt_preprocess > /dev/null; echo $?;", exit_err=True)

            if out.splitlines()[0] != '0':
                print(f"onmt_preprocess not found: install OpenNMT-py")
                exit(1)

            train_src = self.out / Path('src-train.txt')
            train_tgt = self.out / Path('tgt-train.txt')
            valid_src = self.out / Path('src-val.txt')
            valid_tgt = self.out / Path('tgt-val.txt')
            save_data = self.onmt_input_path / Path('final')
            self.configs.onmt_args.preprocess['seed'] = self.seed
            mutable_options = self.configs.onmt_args.unpack(name='preprocess', string=True)

            cmd_str = f"onmt_preprocess -train_src {train_src} -train_tgt {train_tgt} -valid_src {valid_src} " \
                      f"-valid_tgt {valid_tgt} {mutable_options} " \
                      f"--save_data {save_data} 2>&1"
            out, err, _ = super().__call__(command=cmd_str, file=self.out_file)

            if err:
                self.status('train: something went wrong.')
                exit(1)

    @staticmethod
    def definition() -> dict:
        return {'name': 'preprocess',
                'command': Preprocess,
                'description': "Preprocess the dataset into the input files for the neural net."}

    @staticmethod
    def add_arguments(cmd_parser) -> NoReturn:
        cmd_parser.add_argument('-sp', '--src_path', help='Source dataset path.', type=str, required=None)
        cmd_parser.add_argument('-op', '--out_path', help='Destination path.', type=str, default=None)
        cmd_parser.add_argument('-s', '--split', help='Split dataset.', choices=list_of_split_choices,
                                default=None)
        cmd_parser.add_argument('--no_onmt', action='store_true', default=False,
                                help='Disables onmt pre-processing on the train and val sets.')
        cmd_parser.add_argument('--no_truncation', action='store_true', default=False,
                                help='Doesnt truncates the samples in the dataset.')
