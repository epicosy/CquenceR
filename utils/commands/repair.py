#!/usr/bin/env python3

from pathlib import Path
from typing import NoReturn, List

from utils.command import Command
from utils.patch import Patch, Test
from processing.post.generate_patches import prediction_to_patch
from processing.pre.prepare import process_manifest, preprocess_files
from utils.results import Results


class Repair(Command):
    def __init__(self, working_dir: str, prefix: str, manifest_path: str, compile_script: str, test_script: str,
                 compile_args: str, pos_tests: int, neg_tests: int, seed: int = 0, beam_size: int = None,
                 cont: bool = False, skip_check: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.working_dir = Path(working_dir)
        self.manifest_path = Path(manifest_path)
        self.seed = seed
        self.skip_check = skip_check
        self.prefix = prefix
        self.pos_tests = pos_tests
        self.neg_tests = neg_tests
        self.compile_script = compile_script
        self.compile_args = compile_args
        self.test_script = test_script
        self.root = self.configs.data_paths.root
        self.model_path = self.configs.data_paths.model / Path('final-model_step_4000.pt')
        self.out_path = self.working_dir
        self.limit = self.configs.trunc_limit
        self.cont = cont
        self.beam = self.configs.onmt_args.translate['beam_size']
        self.repair_dir = self.working_dir / Path("repair")

        if beam_size:
            self.beam = beam_size
            self.configs.onmt_args.translate['beam_size'] = self.beam
            self.configs.onmt_args.translate['n_best'] = self.beam

        if pos_tests == 0 or neg_tests == 0:
            raise ValueError('Insufficient number of tests.')

    def __call__(self, **kwargs):
        self._check_onmt()

        if not self.skip_check:
            self._sanity_check()
        # Tokenize and truncate
        self._preprocess()
        # Generate predictions
        self._predict()
        # Post Process
        self._postprocess()
        self.results = Results(total_patches=self.beam, pos_tests=self.pos_tests, neg_tests=self.neg_tests)
        # Generate patches
        for i in range(self.beam):
            patch = self._patch(prediction=i)
            passed = self._test_patch(patch=patch)
            self.results(patch)
            if passed:
                if not self.cont:
                    break
        self.results.stop()
        print(self.results)

    def _check_onmt(self):
        out, err, _ = super().__call__(command=f"command -v onmt_translate > /dev/null; echo $?;", exit_err=True)

        if out.splitlines()[0] != '0':
            print(f"onmt_translate not found: install OpenNMT-py")
            exit(1)

    def _check_syntax(self, file_path: Path):
        out, err, _ = super().__call__(command=f"gcc -c -fsyntax-only {file_path} >/dev/null 2>&1; echo $?;")
        print(out, err)
        if out.splitlines()[0] != '0':
            return False
        return True

    def _get_tests(self, pos=True):
        if pos:
            return [Test(name=f"p{pt}") for pt in range(1, self.pos_tests + 1)]
        return [Test(name=f"n{nt}") for nt in range(1, self.neg_tests + 1)]

    def _sanity_check(self):
        print("Performing sanity check.")

        compiles, _ = self._compile()
        if not compiles:
            print("Sanity check failed: compile failure.")
            exit(1)

        # Positive Tests
        pos_tests = self._get_tests()
        # Negative Tests
        neg_tests = self._get_tests(pos=False)

        if not self._test(tests=neg_tests, should_fail=True):
            print("Sanity check failed: test failure.")
            exit(1)
        if not self._test(tests=pos_tests):
            print("Sanity check failed: test failure.")
            exit(1)

    def _preprocess(self):
        if not self.working_dir.exists():
            raise ValueError(f"{self.working_dir} not found.")
        if not self.manifest_path.exists():
            raise ValueError(f"{self.manifest_path} not found.")

        self.manifest = process_manifest(self.manifest_path)
        self.preprocessed = preprocess_files(prefix=self.prefix,
                                             manifest=self.manifest,
                                             truncation_limit=self.limit,
                                             out_path=self.working_dir / Path('preprocessed'))

    def _predict(self):
        self.predictions = {}
        onmt_translate_args = self.configs.onmt_args.unpack(name='translate', string=True)

        if not self.preprocessed:
            raise ValueError("No preprocessed files generated.")

        for file, hunk_files in self.preprocessed.items():
            file_path = Path(file)
            self.predictions[file] = {}

            for hunk_id, hunk_file in hunk_files.items():
                predictions_file = Path("predictions", file_path.parent, file_path.stem, f"{hunk_id}.txt")
                preprocess_file_path = self.working_dir / predictions_file
                preprocess_file_path.parent.mkdir(parents=True, exist_ok=True)
                cmd_str = f"onmt_translate -model {self.model_path} -src {hunk_file} {onmt_translate_args} " \
                          f"-output {preprocess_file_path} 2>&1"

                out, err, _ = super().__call__(command=cmd_str,
                                               file=Path(self.out_path / Path('translate.out')))
                if err:
                    self.status('onmt_translate: something went wrong.')
                    exit(1)

                self.predictions[file][hunk_id] = preprocess_file_path

    def _postprocess(self):
        pass

    def _patch(self, prediction: int) -> Patch:
        if not self.predictions:
            raise ValueError("No predictions files generated.")

        patch_dir = f"{prediction}".zfill(6)
        out_path = self.working_dir / Path('patches', patch_dir)

        return prediction_to_patch(prefix=self.prefix, manifest=self.manifest, predictions_files=self.predictions,
                                   prediction_number=prediction, out_path=out_path)

    # check syntax gcc main.c -fsyntax-only
    # The technically best way to do this is to simply compile each file.
    # Setting up all those compiles is either easy (because you have the build scripts) or will be
    # h--- if you don't have them, and the difference may drive your choice of solution.
    # For C, you pretty much need to run them through a compiler with the preprocessor enabled.
    # If you don't do that, the typical C code containg macros and preprocessor conditionals won't be parsable at all.
    def _compile(self, patch: Patch = None):
        compile_cmd = self.compile_script

        if patch:
            print(f"Compiling patch {patch.number}.")
            compile_cmd += " " + self.compile_args.replace('__SOURCE_NAME__', str(patch))
        else:
            print("Compiling")

        out, err, exec_time = super().__call__(command=f"{compile_cmd}")

        if self.verbose:
            print(f"Command: {compile_cmd}\nOutput: {out}")
        if err:
            print(f"compiling: something went wrong: {err}")
            return False, exec_time
        return True, exec_time

    def _test(self, tests: List[Test], should_fail: bool = False):
        print(f"Testing:")
        for test in tests:
            test_cmd = self.test_script.replace("__TEST_NAME__", test.name)
            out, err, exec_time = super().__call__(command=f"{test_cmd}")
            test.exec_time = exec_time

            if self.verbose:
                print(f"Command: {test_cmd}\nOutput: {out}")
            if not err and should_fail:
                print(f"\t{test}: 0")
                test.passed = False
                return False
            if err:
                if should_fail:
                    print(f"\t{test}: 0")
                    return True
                print(f"\t{test}: 0")
                test.passed = False
                return False
            test.passed = True
            print(f"\t{test}: 1")
        return True

    def _test_patch(self, patch: Patch) -> bool:
        # Compile
        patch.compiles, patch.compile_time = self._compile(patch)
        # Positive Tests
        pos_tests = self._get_tests()
        patch.pos_tests = pos_tests
        # Negative Tests
        neg_tests = self._get_tests(pos=False)
        patch.neg_tests = neg_tests

        if patch.compiles:
            if self._test(tests=neg_tests):
                if self._test(tests=pos_tests):
                    patch(is_fix=True)
                    for pf in patch:
                        repair_file_path = self.repair_dir / Path(pf.target_file)
                        repair_file_path.parent.mkdir(parents=True, exist_ok=True)

                        # if is patch, write to the repair folder the file
                        with pf.path.open(mode='r') as pp, repair_file_path.open(mode="w") as rf:
                            rf.write(pp.read())
                    return True
        patch(is_fix=False)
        return False

    @staticmethod
    def definition() -> dict:
        return {'name': 'repair',
                'command': Repair,
                'description': "Patches C programs."}

    @staticmethod
    def add_arguments(cmd_parser) -> NoReturn:
        cmd_parser.add_argument('-mp', '--manifest_path', type=str, required=True,
                                help='File with the vulnerable files and respective hunks lines.')
        cmd_parser.add_argument('-cs', '--compile_script', help='Compile script to be used.', type=str, required=True)
        cmd_parser.add_argument('-ca', '--compile_args', type=str, required=True,
                                help='Arguments to be used for compiling the patches.')
        cmd_parser.add_argument('-pf', '--prefix', help='Prefix for source files.', type=str, required=True)
        cmd_parser.add_argument('-ts', '--test_script', help='Test script to be used.', type=str, required=True)
        cmd_parser.add_argument('-pt', '--pos_tests', help='Number of positive tests.', type=int, required=True)
        cmd_parser.add_argument('-nt', '--neg_tests', help='Number of negative tests.', type=int, required=True)
        cmd_parser.add_argument('--skip_check', help='Skips sanity check.', action='store_true', required=False)
        cmd_parser.add_argument('-s', '--seed', type=int, default=0,
                                help='Set random seed used for better reproducibility between experiments.')
        cmd_parser.add_argument('-wd', '--working_dir', help='Working directory.', type=str, required=True)
        cmd_parser.add_argument('--cont', action='store_true', default=False,
                                help='Continue search after repair has been found.')
        cmd_parser.add_argument('-bs', '--beam_size', help='Number of predictions to be generated.', type=int,
                                required=False)
