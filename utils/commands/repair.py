#!/usr/bin/env python3

from pathlib import Path
from typing import NoReturn, List

from utils.command import Command
from utils.patch import Patch, Test
from utils.processing.transform import tokenize_vuln, truncate
from processing.post.generate_patches import predictions_to_patches
from utils.results import Results


class Repair(Command):
    def __init__(self, working_dir: str, src_path: str, vuln_line: int, compile_script: str, test_script: str,
                 pos_tests: int, neg_tests: int, seed: int = 0, beam_size: int = None, cont: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.working_dir = Path(working_dir)
        self.source = self.working_dir / Path(src_path)
        self.src_path = Path(src_path)
        self.seed = seed
        self.vuln_line = vuln_line
        self.pos_tests = pos_tests
        self.neg_tests = neg_tests
        self.compile_script = compile_script
        self.test_script = test_script
        self.root = self.configs.data_paths.root
        self.model_path = self.configs.data_paths.model / Path('final-model_step_2000.pt')
        self.out_path = self.configs.data_paths.root
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

        # Tokenize and truncate
        pp_source = self._preprocess()

        # Generate predictions
        predictions = self._predict(pp_source)

        # Post Process
        self._postprocess()

        # Generate patches
        patches = self._patch(predictions)

        results = self._test_patches(patches=patches)
        print(results)

    def _check_onmt(self):
        out, err, _ = super().__call__(command=f"command -v onmt_translate > /dev/null; echo $?;", exit_err=True)

        if out.splitlines()[0] != '0':
            print(f"onmt_translate not found: install OpenNMT-py")
            exit(1)

    def _get_tests(self, pos=True):
        if pos:
            return [Test(name=f"p{pt}") for pt in range(1, self.pos_tests + 1)]
        return [Test(name=f"n{nt}") for nt in range(1, self.neg_tests + 1)]

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

        source_pre_proc = self.working_dir / Path(f"{self.source.stem}_preprocessed_{self.seed}.txt")

        with source_pre_proc.open(mode="w") as spp:
            spp.write(result)

        return source_pre_proc

    def _predict(self, preprocessed: Path):
        predictions_file = self.working_dir / Path(f"predictions_{self.beam}_{self.seed}.txt")
        mutable_args = self.configs.onmt_args.unpack(name='translate', string=True)
        cmd_str = f"onmt_translate -model {self.model_path} -src {preprocessed} {mutable_args} " \
                  f"-output {predictions_file} 2>&1"

        out, err, _ = super().__call__(command=cmd_str,
                                       file=Path(self.out_path / Path('translate.out')))
        if err:
            self.status('onmt_translate: something went wrong.')
            exit(1)

        return predictions_file

    def _postprocess(self):
        pass

    def _patch(self, predictions_file: Path):
        patches = predictions_to_patches(target_file=self.src_path, vuln_line_number=self.vuln_line,
                                         predictions_file=predictions_file, out_path=self.working_dir)

        return patches

    # check syntax gcc main.c -fsyntax-only
    # The technically best way to do this is to simply compile each file.
    # Setting up all those compiles is either easy (because you have the build scripts) or will be
    # h--- if you don't have them, and the difference may drive your choice of solution.
    # For C, you pretty much need to run them through a compiler with the preprocessor enabled.
    # If you don't do that, the typical C code containg macros and preprocessor conditionals won't be parsable at all.
    def _compile(self, patch_file: Path):
        print(f"Compiling patch {patch_file.stem}.")
        compile_cmd = self.compile_script.replace("__SOURCE_NAME__", str(patch_file))
        out, err, exec_time = super().__call__(command=f"{compile_cmd}")

        if self.verbose:
            print(f"Command: {compile_cmd}\nOutput: {out}")
        if err:
            print(f"compiling: something went wrong: {err}")
            return False, exec_time
        return True, exec_time

    def _test(self, tests: List[Test]):
        print(f"Testing:")
        for test in tests:
            test_cmd = self.test_script.replace("__TEST_NAME__", test.name)
            out, err, exec_time = super().__call__(command=f"{test_cmd}")
            test.time = exec_time

            if self.verbose:
                print(f"Command: {test_cmd}\nOutput: {out}")
            if err:
                print(f"\t{test}: 0")
                test.passed = False
                return False
            test.passed = True
            print(f"\t{test}: 1")
        return True

    def _test_patches(self, patches: List[Patch]):
        results = Results(patches, pos_tests=self.pos_tests, neg_tests=self.neg_tests)

        for patch in patches:
            # Compile
            patch.compiles, patch.compile_time = self._compile(patch.path)
            # Pos Test
            pos_tests = self._get_tests()
            patch.pos_tests = pos_tests
            # Neg Test
            neg_tests = self._get_tests(pos=False)
            patch.neg_tests = neg_tests

            if not patch.compiles:
                continue

            if not self._test(tests=pos_tests):
                continue

            if self._test(tests=neg_tests):
                patch(is_fix=True)
                patch_file_path = self.repair_dir / self.src_path
                patch_file_path.parent.mkdir(parents=True, exist_ok=True)

                # if is patch, write to the repair folder the file
                with patch.path.open(mode='r') as pp, patch_file_path.open(mode="w") as pf:
                    pf.write(pp.read())

                if not self.cont:
                    break
            else:
                patch(is_fix=False)

        results()
        return results

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
        cmd_parser.add_argument('--cont', action='store_true', default=False,
                                help='Continue search after repair has been found.')
        cmd_parser.add_argument('-bs', '--beam_size', help='Number of predictions to be generated.', type=str,
                                required=False)
