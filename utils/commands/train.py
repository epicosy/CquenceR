#!/usr/bin/env python3
import re
from pathlib import Path
from typing import NoReturn

from utils.command import Command
from utils.plots import Plotter


class Train(Command):
    def __init__(self, gpu: bool = False, plot: bool = False, **kwargs):
        super().__init__(**kwargs)
        if gpu:
            self.configs.onmt_args.train['gpu_ranks'] = 0
        self.in_path = self.configs.data_paths.input
        self.out_path = self.configs.data_paths.model
        self.out_file = Path(self.out_path / Path(f"train.final.{self.seed}.out"))
        self.plot = plot

    def __call__(self, **kwargs):
        out, err, _ = super().__call__(command=f"command -v onmt_train > /dev/null; echo $?;", exit_err=True)

        if out.splitlines()[0] != '0':
            self.status("onmt_train not found: install OpenNMT-py")
            exit(1)

        self.configs.onmt_args.train['seed'] = self.seed
        mutable_args = self.configs.onmt_args.unpack(name='train', string=True)
        cmd_str = f"onmt_train -data {self.in_path / Path('final')} {mutable_args} " \
                  f"-save_model {self.out_path / Path('final-model')} 2>&1"
        out, err, _ = super().__call__(command=cmd_str, file=self.out_file)

        if err:
            self.status('train: something went wrong.')
            exit(1)

        if self.plot:
            self.plot_stats()

    def plot_stats(self):
        if not self.out_file.exists():
            print(f"File {self.out_file} found.")

        stats_regex = re.compile(r"Step (\d+)\/ \d+\; acc:  (\d+\.\d+); ppl:  (\d+\.\d+);")

        with self.out_file.open(mode="r") as s:
            results = stats_regex.findall(s.read())

        steps, acc, ppl = zip(*results)
        accuracy = [float(a) for a in acc]
        perplexity = [float(p) for p in ppl]

        plotter = Plotter(str(self.configs.root / Path('train_plots')))
        plotter.subplots(x_data=steps, y_data=[accuracy, perplexity], x_label="Steps", fig_title='Training stats',
                         y_labels=["Accuracy", "Perplexity"])

    @staticmethod
    def definition() -> dict:
        return {'name': 'train',
                'command': Train,
                'description': "Trains a model from the preprocessed dataset files."}

    @staticmethod
    def add_arguments(cmd_parser) -> NoReturn:
        cmd_parser.add_argument('--gpu', action='store_true', default=False, help='Enables GPU training.')
        cmd_parser.add_argument('--plot', help='Plots stats about testing.', action="store_true", required=False)
