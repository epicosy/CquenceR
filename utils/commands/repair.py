#!/usr/bin/env python3

from pathlib import Path
from typing import NoReturn, List
import time

from utils.command import Command
from utils.processing.transform import tokenize_vuln, truncate
from processing.post.generate_patches import apply_predictions


class Repair(Command):
    def __init__(self, working_dir: str, src_path: str, vuln_line: int, compile_script: str, test_script: str,
                 pos_tests: int, neg_tests: int, seed: int = 0, beam_size: int = None, **kwargs):
        super().__init__(**kwargs)
        self.working_dir = Path(working_dir)
        self.source = self.working_dir / Path(src_path)
        self.seed = seed
        self.vuln_line = vuln_line
        self.pos_tests = pos_tests
        self.neg_tests = neg_tests
        self.compile_script = compile_script
        self.test_script = test_script
        self.root = self.configs.data_paths.root
        self.model_path = self.configs.data_paths.model / Path('final-model_step_1000.pt')
        self.out_path = self.configs.data_paths.root
        self.limit = self.configs.trunc_limit
        self.beam = beam_size if beam_size else self.configs.onmt_args.translate['beam_size']
        print(self.working_dir.name)
        self.temp_path = self.configs.temp_path / Path(f"{self.working_dir.name}_{seed}")
        self.temp_path.mkdir()

        if pos_tests == 0 or neg_tests == 0:
            raise ValueError('Insufficient number of tests.')

    def __call__(self, **kwargs):
        self._check_onmt()

        # Tokenize and truncate
        pp_source = self._preprocess()

        # Generate predictions
        predictions = self._predict(pp_source)
        # Post Process
        self._postprocess()

        # Generate patches
        patches = self._patch(predictions)

        # check syntax gcc main.c -fsyntax-only
        # The technically best way to do this is to simply compile each file.
        # Setting up all those compiles is either easy (because you have the build scripts) or will be
        # h--- if you don't have them, and the difference may drive your choice of solution.
        # For C, you pretty much need to run them through a compiler with the preprocessor enabled.
        # If you don't do that, the typical C code containg macros and preprocessor conditionals won't be parsable at all.
        # Compile
        compilation_results = {'success': [], 'fail': []}
        elapsed = 0
        fix = None

        for patch in patches:
            start = time.time()
            if self._compile(patch):
                end = time.time()
                elapsed += (end - start)
                compilation_results['success'].append(patch.parent.name)
                # Pos Test
                passed = self._test([f"p{pt}" for pt in range(1, self.pos_tests+1)])
                if not passed:
                    continue
                # Neg Test
                passed = self._test([f"n{nt}" for nt in range(1, self.neg_tests+1)])
                if not passed:
                    continue
                else:
                    fix = patch.parent.name
                    break
            else:
                compilation_results['fail'].append(patch.parent.name)

        print(f"Compilation success ratio: {len(compilation_results['success'])/len(compilation_results['success']+compilation_results['fail'])}")
        print(f"Compilation time elapsed: {elapsed}")
        if fix:
            print(f"Patch found: {fix}.")
        else:
            print(f"No patch found.")

    def _check_onmt(self):
        out, err = super().__call__(command=f"command -v onmt_translate > /dev/null; echo $?;", exit_err=True)

        if out.splitlines()[0] != '0':
            print(f"onmt_translate not found: install OpenNMT-py")
            exit(1)

    def _preprocess(self) -> Path:
        if not self.working_dir.exists():
            raise ValueError(f"{self.working_dir} not found.")
        if not self.source.exists():
            raise ValueError(f"{self.source} not found.")

        with self.source.open(mode="r") as s:
            code = s.read().splitlines()

            if len(code) < self.vuln_line:
                raise ValueError('Vulnerable line outside the scope of the input file')

            result = tokenize_vuln(code, self.vuln_line)
            result = truncate(result, self.limit)

        source_pre_proc = self.temp_path / Path(f"{self.source.stem}_preprocessed.txt")

        with source_pre_proc.open(mode="w") as spp:
            spp.write(result)

        return source_pre_proc

    def _predict(self, preprocessed: Path):
        predictions_file = self.temp_path / Path(f"predictions_{self.beam}.txt")
        mutable_args = self.configs.onmt_args.unpack(name='translate', string=True)
        cmd_str = f"onmt_translate -model {self.model_path} -src {preprocessed} {mutable_args} " \
                  f"-output {predictions_file} 2>&1"

        out, err = super().__call__(command=cmd_str,
                                    file=Path(self.out_path / Path('translate.out')))
        if err:
            self.status('onmt_translate: something went wrong.')
            exit(1)

        return predictions_file

    def _postprocess(self):
        pass

    def _patch(self, predictions_file: Path):
        patches = apply_predictions(target_file=self.source, vuln_line_number=self.vuln_line,
                                    predictions_file=predictions_file, out_path=self.temp_path)

        return patches

    def _compile(self, patch: Path):
        compile_cmd = self.compile_script.replace("__SOURCE_NAME__", str(patch))
        out, err = super().__call__(command=f"{compile_cmd} > /dev/null; echo $?;", exit_err=True)
        print(compile_cmd)
        if err or out.splitlines()[0] != '0':
            print(f"compiling: something went wrong: {out} {err}")
            return False

        return True

    def _test(self, tests: List[str]):
        for test in tests:
            test_cmd = self.test_script.replace("__TEST_NAME__", test)
            out, err = super().__call__(command=f"{test_cmd} > /dev/null; echo $?;", exit_err=True)

            if err or out.splitlines()[0] != '0':
                print(f"{test}: 0")
                return False

            print(f"{test}: 1")
        return True

    @staticmethod
    def definition() -> dict:
        return {'name': 'repair',
                'command': Repair,
                'description': "Patches C programs."}

    @staticmethod
    def add_arguments(cmd_parser) -> NoReturn:
        cmd_parser.add_argument('-sp', '--src_path', help='Source dataset path.', type=str, required=True)
        cmd_parser.add_argument('-cs', '--compile_script', help='Compile script to be used.', type=str, required=True)
        cmd_parser.add_argument('-ts', '--test_script', help='Test script to be used.', type=str, required=True)
        cmd_parser.add_argument('-vl', '--vuln_line', help='Vulnerable line number.', type=int, required=True)
        cmd_parser.add_argument('-pt', '--pos_tests', help='Number of positive tests.', type=int, required=True)
        cmd_parser.add_argument('-nt', '--neg_tests', help='Number of negative tests.', type=int, required=True)
        cmd_parser.add_argument('-s', '--seed', type=int, default=0,
                                help='Set random seed used for better reproducibility between experiments.')
        cmd_parser.add_argument('-wd', '--working_dir', help='Working directory.', type=str, required=True)
        cmd_parser.add_argument('-bs', '--beam_size', help='Number of predictions to be generated.', type=str,
                                required=False)