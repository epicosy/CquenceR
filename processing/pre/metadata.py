import json
from datetime import datetime
from pathlib import Path


class Metadata:
    def __init__(self, total_records: int):
        self.total_records = total_records
        self.discarded = 0
        self.processed = 0

    def __call__(self, processed, discarded):
        self.processed += processed
        self.discarded += discarded

    def write(self, out_path: Path):
        metadata = {
            "total_records" : self.total_records,
            "discarded_records" : self.discarded,
            "processed_records" : self.processed,
            "date": datetime.now().strftime("%d-%m-%Y %H-%M")
        }
        metadata_file = out_path / Path("metadata-" + datetime.now().strftime("%d%m%Y-%H%M") + ".json")

        with metadata_file.open(mode="w") as mf:
            json.dump(metadata, mf)
