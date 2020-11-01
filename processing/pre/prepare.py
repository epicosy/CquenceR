#!/usr/bin/env python3

import pandas as pd

from pathlib import Path

from utils.processing.dataset import train_val_split, train_val_test_split
from utils.processing.c_tokenizer import tokenize_hunks, truncate
from processing.pre.metadata import Metadata
from processing.pre.input_dataset import InputDataset


def process_dataset(dataset_path: Path, out_path: Path, truncation_limit: int = None, split: str = None):
    dataset = pd.read_pickle(dataset_path)
    metadata = Metadata(len(dataset))

    sets = {}

    if split == "train_val":
        sets.update(train_val_split(dataset))
    elif split == "train_val_test":
        sets.update(train_val_test_split(dataset))
    else:
        sets['dataset'] = dataset

    for name, d_set in sets.items():
        input_ds = InputDataset(name, d_set, out_path)
        processed, discarded = input_ds.write(truncation_limit)
        metadata(processed, discarded)
        input_ds.save(dataset_path.stem)

    metadata.write(out_path=out_path)


# file_path: hunk_start, hunk_end; hunk_start, hunk_end;
# manifest -> {file_path: {hunk_id: (start, end), hunk_id: (start, end)}}
def process_manifest(manifest_path: Path) -> dict:
    manifest = {}
    with manifest_path.open(mode="r") as mp:
        content = mp.readlines()

    for line in content:
        file_path, hunks_str = line.replace('\n', '').split(':')
        manifest[file_path] = {}
        hunks = hunks_str.split(';')

        if hunks[-1] == '':
            hunks = hunks[:-1]

        for i, hunk in enumerate(hunks):
            start, end = hunk.split(',')
            manifest[file_path][i] = (int(start)-1, int(end)-1)

    return manifest


# tokenized_files -> {file: {hunk_id: hunk_file, hunk_id: hunk_file}}
def preprocess_files(prefix: Path, manifest: dict, truncation_limit: int, out_path: Path) -> dict:
    tokenized_files = {}
    out_path.mkdir(parents=True, exist_ok=True)

    for file, hunks in manifest.items():
        file_path = prefix / Path(file)
        tokenized_files[file] = {}

        with file_path.open(mode="r") as fp:
            content = fp.read()
            results = tokenize_hunks(content, hunks, truncation_limit)

        for h_id, hunk in results.items():
            file_out_path = out_path / Path(f"{file_path.stem}_{h_id}.txt")
            tokenized_files[file][h_id] = Path(file_out_path)

            with file_out_path.open(mode="w") as op:
                op.write(hunk)

    return tokenized_files
