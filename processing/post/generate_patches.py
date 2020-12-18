from pathlib import Path
from typing import Dict, Tuple
from utils.patch import Patch, PatchFile
from utils.processing.c_tokenizer import NEW_LINE_TOKEN, detokenize


def tokens_to_source(tokens: str) -> str:
    # source = tokens.replace(TAB_TOKEN, "\t")
    source = detokenize(tokens)
    return source.replace(NEW_LINE_TOKEN, "\n")


def prediction_to_patch(prefix: Path, manifest: Dict[str, Dict[int, Tuple[int, int]]],
                        predictions_files: Dict[str, Dict[int, Path]], prediction_number: int, out_path: Path) -> Patch:
    patch = Patch(number=prediction_number, root_path=out_path)

    for target_file, pred_hunks in predictions_files.items():
        target_file_path = prefix / Path(target_file)
        with target_file_path.open() as tfp:
            code_lines = tfp.readlines()
            hunks = manifest[target_file]
            changes = []
            shift = 0
            for hunk_id, pred_hunk in pred_hunks.items():
                with pred_hunk.open() as ph:
                    prediction = ph.read().splitlines()[prediction_number]
                    prediction = tokens_to_source(prediction)
                    changes.append(prediction)
                    start, end = hunks[hunk_id]
                    if start == end:
                        end += 1
                    hunk_size = end - start
                    prediction_lines = prediction.splitlines(keepends=True)
                    code_lines[start+shift: end+shift] = prediction_lines

                    if hunk_size > len(prediction_lines):
                        shift -= hunk_size - len(prediction_lines)
                    elif hunk_size < len(prediction_lines):
                        shift += len(prediction_lines) - hunk_size

            out_file = out_path / target_file
            out_file.parent.mkdir(parents=True, exist_ok=True)

            with out_file.open(mode="w") as of:
                of.write(''.join(code_lines))

            patch_file = PatchFile(target_file, path=out_file, changes=changes)
            patch.add(patch_file)

    return patch
