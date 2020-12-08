import time

from utils.patch import Patch
from utils.data_objects import Stats


class Results:
    def __init__(self, total_patches: int, pos_tests: int, neg_tests: int):
        self.patches = []
        self.current = None
        self.elapsed = time.time()
        self.stats = Stats(total_patches=total_patches, total_tests=pos_tests + neg_tests)

    def __call__(self, patch: Patch):
        self.stats.patches_sizes.append(sum([len(pf.changes) for pf in patch]))

        if patch.is_fix:
            self.stats.fixes.append(patch.number)

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

    def stop(self):
        self.elapsed = time.time() - self.elapsed

    def __str__(self):
        res_str = f"Duration: {self.elapsed:9.3f}\n"
        res_str += f"Compile time: {self.stats.comp_time:9.3f} seconds\n"
        res_str += f"Compile attempts: {self.stats.comp_attempts}\n"
        res_str += f"Compile failures: {self.stats.comp_attempts - self.stats.success_comp}\n"
        res_str += f"Average compile time: {self.stats.average_comp_time():9.3f} seconds\n"
        res_str += f"Compile success rate: {self.stats.success_ratio():9.3f}\n"
        res_str += f"Tests time: {self.stats.tests_time():9.3f} seconds\n"
        res_str += f"\tPositive tests time: {self.stats.pos_tests_time:9.3f} seconds\n"
        res_str += f"\tNegative tests time: {self.stats.neg_tests_time:9.3f} seconds\n"
        res_str += f"Average tests time: {self.stats.average_tests_time():9.3f} seconds\n"
        res_str += f"Tests executed: {self.stats.pos_tests_exec+self.stats.neg_tests_exec}\n"
        res_str += f"\tPositive tests executed: {self.stats.pos_tests_exec}\n"
        res_str += f"\tNegative tests executed: {self.stats.neg_tests_exec}\n"
        res_str += f"Average patch size: {self.stats.average_patch_size()}\n"
        res_str += f"{'-'*20}\n"
        n_fixes = len(self.stats.fixes)

        if n_fixes > 0:
            res_str += f"{n_fixes} patches found: {self.stats.fixes}\n"
        else:
            res_str += f"No patches found.\n"

        return res_str
