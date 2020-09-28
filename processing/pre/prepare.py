#!/usr/bin/env python3

import pandas as pd

from pathlib import Path

from utils.processing.dataset import train_val_split, train_val_test_split
from processing.pre.metadata import Metadata
from processing.pre.input_dataset import InputDataset


def process_dataset(dataset_path: Path, out_path: Path, truncation_limit: int, split: str = None):
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
