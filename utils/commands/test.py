#!/usr/bin/env python3

import Levenshtein
from pathlib import Path
from typing import NoReturn

from utils.command import Command
from utils.plots import Plotter


class Test(Command):
    def __init__(self, src_path: str = None, hist: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.model_path = self.configs.data_paths.model / Path('final-model_step_2000.pt')
        self.src_path = src_path if src_path else self.configs.data_paths.processed
        self.src_test = self.src_path / Path('src-test.txt')
        self.tgt_test = self.src_path / Path('tgt-test.txt')
        self.out_path = Path('/tmp')
        self.hist = hist
        self.plotter = Plotter()
        self.predictions = self.out_path / Path('cquencer_test_predictions')

        if not self.src_test.exists():
            raise ValueError("src-test.txt not found")
        if not self.tgt_test.exists():
            raise ValueError("tgt_test.txt not found")

    def __call__(self, **kwargs):
        if not self.predictions.exists():
            print('Translating')
            out, err, _ = super().__call__(command=f"command -v onmt_translate > /dev/null; echo $?;", exit_err=True)

            if out.splitlines()[0] != '0':
                print(f"onmt_translate not found: install OpenNMT-py")
                exit(1)

            onmt_translate_args = self.configs.onmt_args.unpack(name='translate', string=True)
            cmd_str = f"onmt_translate -model {self.model_path} -src {self.src_test} {onmt_translate_args} " \
                      f"-output {self.predictions} 2>&1"

            out, err, _ = super().__call__(command=cmd_str, file=self.out_path / Path('translate.out'))

            if err:
                self.status('onmt_translate: something went wrong.')
                exit(1)

        self.match()

    # based on https://github.com/KTH/chai/blob/master/src/Continuous_Learning/codrep-compare.py
    def match(self):
        beam = self.configs.onmt_args.translate["beam_size"]
        with self.predictions.open(mode="r") as p, self.tgt_test.open(mode="r") as tt:
            target_lines = tt.readlines()

            matches_found_total = 0
            matches_found_no_repeat = 0
            found = 0
            similarity_pred = []

            for i, target_line in enumerate(target_lines):

                for i in range(beam):
                    patch_line = p.readline()

                    if patch_line == target_line:
                        matches_found_total += 1
                        if found == 0:
                            matches_found_no_repeat += 1
                        found = 1
                        similarity_pred.append(1)
                    else:
                        similarity_pred.append(Levenshtein.ratio(patch_line, target_line))

            print(f"Similarity total average: {round(sum(similarity_pred) / len(similarity_pred), 3)}")
            print(
                f"Found fixes for {matches_found_no_repeat} vulnerabilities ({round(matches_found_no_repeat / len(target_lines), 3)}%)")
            print(f"Found {matches_found_total} total fixes")
            print(f"Analized {len(target_lines)} total changes")

            if self.hist:
                self.plotter.multi_histogram([similarity_pred], labels=['predictions'], x_label="Frequency",
                                             interval=(0, 1), y_label="similarity", bins_size=100, pdf=True)

    @staticmethod
    def definition() -> dict:
        return {'name': 'test',
                'command': Test,
                'description': "Tests the model on the test dataset."}

    @staticmethod
    def add_arguments(cmd_parser) -> NoReturn:
        cmd_parser.add_argument('-sp', '--src_path', help='Source dataset path.', type=str, default=None)
        cmd_parser.add_argument('--hist', help='Plots similarity histogram.', action="store_true", required=False)
