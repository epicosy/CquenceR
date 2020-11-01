#!/usr/bin/env python3

from pathlib import Path
from typing import NoReturn, List, AnyStr

from utils.command import Command
from utils.analyze import DatasetAnalyzer
from utils.plots import Plotter


class Stats(Command):
    def __init__(self, src_path: str = None, save: str = None, plots: List[AnyStr] = None, **kwargs):
        super().__init__(**kwargs)
        self.src_path = src_path if src_path else self.configs.data_paths.processed
        self.analyzer = DatasetAnalyzer(src=self.src_path / Path('src-dataset.txt'),
                                        tgt=self.src_path / Path('tgt-dataset.txt'), verbose=self.verbose)
        self.plotter = Plotter(save)
        mapping = {'zipf': self.zipf, 'hist': self.histogram, 'bars': self.bars}
        self.plots = {name: func for name, func in mapping.items() if name in plots} if plots else mapping

    def __call__(self, **kwargs):
        for name, plot in self.plots.items():
            plot()

    def zipf(self):
        tokens, counts = self.analyzer.token_counts()
        self.plotter.zipf_log(tokens, counts)

    def histogram(self):
        histogram_data = [self.analyzer.tokens_per_line(), self.analyzer.tokens_per_line(tgt=True)]
        self.plotter.multi_histogram(data=histogram_data, labels=['source', 'target'], x_label="Frequency",
                                     interval=(0, 400), y_label="Number of tokens", bins_size=100, pdf=True)

    def bars(self):
        # Number of statements
        labels, values = zip(*self.analyzer.hunk_size().items())
        self.plotter.bars(values, index=labels, bar_label="statements", y_label="number of samples")

    @staticmethod
    def definition() -> dict:
        return {'name': 'stats',
                'command': Stats,
                'description': "Tests the model on the test dataset."}

    @staticmethod
    def add_arguments(cmd_parser) -> NoReturn:
        cmd_parser.add_argument('-sp', '--src_path', help='Source dataset path.', type=str, required=None)
        cmd_parser.add_argument('--save', help='Saves the plots to specified path.', type=str, required=False)
        cmd_parser.add_argument('--plots', help='Flag for specifying the available plots to be shown.',
                                choices=['zipf', 'hist', 'bars'],
                                default=None)

