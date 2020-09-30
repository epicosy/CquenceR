import time
from typing import List
from utils.patch import Patch
from utils.data_objects import Stats


class Results:
    def __init__(self, patches: List[Patch], pos_tests: int, neg_tests: int):
        self.patches = patches
        self.elapsed = time.time()
        self.stats = Stats(total_patches=len(patches), total_tests=pos_tests + neg_tests)

    def __call__(self, *args, **kwargs):
        self.elapsed = time.time() - self.elapsed

        for patch in self.patches:
            self.stats.patches_sizes.append(len(patch.change))
            if patch.is_fix:
                self.stats.fixes.append(patch.name)

            if patch.compiles:
                self.stats.success_comp += 1

            if patch.compiles is not None:
                self.stats.comp_attempts += 1

            self.stats.comp_time += patch.compile_time

            for test in patch.pos_tests:
                self.stats.pos_tests_time += test.exec_time

                if test.passed is not None:
                    self.stats.pos_tests_exec += 1

            for test in patch.neg_tests:
                self.stats.neg_tests_time += test.exec_time

                if test.passed is not None:
                    self.stats.neg_tests_exec += 1

    def __str__(self):
        res_str = f"Duration: {self.elapsed:9.3f}\n"
        res_str += f"Compilation time: {self.stats.comp_time:9.3f} seconds\n"
        res_str += f"Compilation attempts: {self.stats.comp_attempts}\n"
        res_str += f"Average compilation time: {self.stats.average_comp_time():9.3f} seconds\n"
        res_str += f"Compilation success ratio: {self.stats.success_ratio():9.3f}\n"
        res_str += f"Tests time: {self.stats.tests_time():9.3f} seconds\n"
        res_str += f"\tPositive tests time: {self.stats.pos_tests_time:9.3f} seconds\n"
        res_str += f"\tNegative tests time: {self.stats.neg_tests_time:9.3f} seconds\n"
        res_str += f"Average tests time: {self.stats.average_tests_time():9.3f} seconds\n"
        res_str += f"Positive tests executed: {self.stats.pos_tests_exec}\n"
        res_str += f"Negative tests executed: {self.stats.neg_tests_exec}\n"
        res_str += f"Average patch size: {self.stats.average_patch_size()}\n"
        res_str += f"{'-'*20}\n"
        n_fixes = len(self.stats.fixes)

        if n_fixes > 0:
            res_str += f"{n_fixes} patches found: {self.stats.fixes}\n"
        else:
            res_str += f"No patches found.\n"

        return res_str
