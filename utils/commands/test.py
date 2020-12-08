#!/usr/bin/env python3

import Levenshtein
import statistics

from difflib import SequenceMatcher
from pathlib import Path
from typing import NoReturn

from utils.command import Command
from utils.plots import Plotter


class Test(Command):
    def __init__(self, src_path: str = None, plot: bool = False, gpu: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.steps = self.configs.onmt_args.train["train_steps"]
        self.model_path = self.configs.data_paths.model / Path(f"final-model_step_{self.steps}.pt")
        self.src_path = src_path if src_path else self.configs.data_paths.processed
        self.src_test = self.src_path / Path('src-test.txt')
        self.tgt_test = self.src_path / Path('tgt-test.txt')
        self.out_path = Path('/tmp')
        self.out_file = self.out_path / Path(f"translate.{self.seed}.out")
        self.plot = plot
        self.predictions = self.out_path / Path('cquencer_test_predictions')

        if gpu:
            self.configs.onmt_args.translate['gpu'] = 0

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

            self.configs.onmt_args.translate['seed'] = self.seed
            onmt_translate_args = self.configs.onmt_args.unpack(name='translate', string=True)
            cmd_str = f"onmt_translate -model {self.model_path} -src {self.src_test} {onmt_translate_args} " \
                      f"-output {self.predictions} 2>&1"
            out, err, _ = super().__call__(command=cmd_str, file=self.out_file)

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
            similarity_pred = []
            all_tgt_tokens = []
            all_prd_tokens = []

            for i, target_line in enumerate(target_lines):
                found = 0
                tgt_tokens = [len(token) for token in target_line.split()]
                all_tgt_tokens.extend(tgt_tokens)

                for i in range(beam):
                    patch_line = p.readline()
                    pred_tokens = [len(token) for token in patch_line.split()]
                    all_prd_tokens.extend(pred_tokens)

                    if patch_line == target_line:
                        matches_found_total += 1
                        if found == 0:
                            matches_found_no_repeat += 1
                        found = 1
                        similarity_pred.append(1)
                    else:
                        similarity_pred.append(Levenshtein.seqratio(patch_line.split(), target_line.split()))
                        # similarity_pred.append(SequenceMatcher(None, patch_line, target_line).ratio())

            print(f"Similarity total average: {round(sum(similarity_pred) / len(similarity_pred), 3)}")
            print(f"Similarity median: {round(statistics.median(similarity_pred), 3)}")
            print(f"Average target token size: {round(sum(all_tgt_tokens) / len(all_tgt_tokens), 3)}")
            print(f"Average predicted token size: {round(sum(all_prd_tokens) / len(all_prd_tokens), 3)}")
            print(f"Median predicted token size: {round(statistics.median(all_prd_tokens), 3)}")
            print(f"Median Target Token Size: {round(statistics.median(all_tgt_tokens), 3)}")
            print(
                f"Found fixes for {matches_found_no_repeat} vulnerabilities ({round(matches_found_no_repeat / len(target_lines), 3)}%)")
            print(f"Found {matches_found_total} total fixes")
            print(f"Analyzed {len(target_lines)} total changes")

            if self.plot:
                plotter = Plotter(str(self.configs.root / Path('test_plots')))
                plotter.multi_histogram([similarity_pred], labels=['predictions'], x_label="similarity",
                                        interval=(0, 1), y_label="Frequency", bins_size=100, pdf=True)
                plotter.multi_histogram([all_tgt_tokens, all_prd_tokens], labels=['target', 'prediction'],
                                        x_label="Size", interval=(0, 35), y_label="Frequency",
                                        bins_size=100, pdf=True, file_name='tokens_size_histogram')

    @staticmethod
    def definition() -> dict:
        return {'name': 'test',
                'command': Test,
                'description': "Tests the model on the test dataset."}

    @staticmethod
    def add_arguments(cmd_parser) -> NoReturn:
        cmd_parser.add_argument('-sp', '--src_path', help='Source dataset path.', type=str, default=None)
        cmd_parser.add_argument('--plot', help='Plots stats about testing.', action="store_true", required=False)
        cmd_parser.add_argument('--gpu', action='store_true', default=False, help='Enables GPU translation.')
