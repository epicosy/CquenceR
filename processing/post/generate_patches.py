
from pathlib import Path
from typing import List
from utils.patch import Patch


def predictions_to_patches(target_file: Path, vuln_line_number: int, predictions_file: Path, out_path: Path) -> List[Patch]:
    patches = []
    with target_file.open(mode="r") as tf, predictions_file.open(mode="r") as pf:
        code_lines = tf.readlines()
        predictions = pf.readlines()
        vuln_line = code_lines[vuln_line_number-1]
        line_indentation = vuln_line[0:vuln_line.find(vuln_line.lstrip())]

        for i, prediction in enumerate(predictions):
            patch_dir = f"{i}".zfill(6)
            out_file = out_path / Path(patch_dir, target_file.name)
            out_file.parent.mkdir(parents=True)

            with out_file.open(mode="w") as of:
                for j, line in enumerate(code_lines):
                    if j+1 == vuln_line_number:
                        of.write(line_indentation+prediction)
                    else:
                        of.write(line)

            patches.append(Patch(name=patch_dir, path=out_file, change=line_indentation+prediction))
    return patches
