#!/usr/bin/env python3
import re
from pathlib import Path
from typing import NoReturn

from utils.command import Command
from utils.plots import Plotter


class Train(Command):
    def __init__(self, gpu: bool = False, plot: bool = False, skip: bool = False, transformer: bool = False, **kwargs):
        super().__init__(**kwargs)
        if gpu:
            self.configs.onmt_args.train['gpu_ranks'] = 0
        self.in_path = self.configs.data_paths.input
        self.out_path = self.configs.data_paths.model
        self.out_file = Path(self.out_path / Path(f"train.final.{self.seed}.out"))
        self.plot = plot
        self.skip = skip
        self.transformer = transformer

    def __call__(self, **kwargs):
        if not self.skip:
            out, err, _ = super().__call__(command=f"command -v onmt_train > /dev/null; echo $?;", exit_err=True)

            if out.splitlines()[0] != '0':
                self.status("onmt_train not found: install OpenNMT-py")
                exit(1)

            self.configs.onmt_args.train['seed'] = self.seed
            model = self.configs.onmt_args.train['model']['lstm']

            if self.transformer:
                model = self.configs.onmt_args.train['model']['transformer']
            # TODO: FIX this
            del self.configs.onmt_args.train['model']
            self.configs.onmt_args.train.update(model)

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
            exit(1)

        train_stats_regex = re.compile(r"Step\s+(\d+)\/ \d+\;\s+acc:\s+(\d+\.\d+);\s+ppl:\s+(\d+\.\d+);")
        val_stats_regex = re.compile(r"Validation perplexity:\s+(\d+\.\d+)\n.*Validation accuracy:\s+(\d+\.\d+)")

        with self.out_file.open(mode="r") as of:
            output = of.read()
            train_results = train_stats_regex.findall(output)
            val_results = val_stats_regex.findall(output)

        steps, acc, ppl = zip(*train_results)
        val_ppl, val_acc = zip(*val_results)
        accuracy = [float(a) for a in acc]
        perplexity = [float(p) for p in ppl]
        val_accuracy = [float(a) for a in val_acc]
        val_perplexity = [float(p) for p in val_ppl]

        plotter = Plotter(str(self.configs.root / Path('train_plots')))
        plotter.subplots(x_data=steps, y_data=[[accuracy, val_accuracy], [perplexity, val_perplexity]], x_label="Steps",
                         fig_title='Training and Validation Stats', y_labels=["Accuracy", "Perplexity"], legend=['Train', 'Validation'])

    @staticmethod
    def definition() -> dict:
        return {'name': 'train',
                'command': Train,
                'description': "Trains a model from the preprocessed dataset files."}

    @staticmethod
    def add_arguments(cmd_parser) -> NoReturn:
        cmd_parser.add_argument('--gpu', action='store_true', default=False, help='Enables GPU training.')
        cmd_parser.add_argument('--transformer', action='store_true', default=False, help='Use the transformer model.')
        cmd_parser.add_argument('--plot', help='Plots stats about testing.', action="store_true", required=False)
        cmd_parser.add_argument('--skip', help='Skips training.', action="store_true", required=False)
