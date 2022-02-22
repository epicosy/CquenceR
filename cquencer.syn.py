mport re

from pathlib import Path
from typing import List, Any, Dict

from synapser.core.data.api import RepairRequest
from synapser.core.data.results import RepairCommand
from synapser.core.database import Signal
from synapser.handlers.tool import ToolHandler
from synapser.utils.misc import match_patches


class CquenceR(ToolHandler):
    """CquenceR"""

    class Meta:
        label = 'cquencer'
        version = '33ac258'

    def write_manifest(self, working_dir: Path, manifest: dict):
        manifest_file = working_dir / Path('hunk_manifest')

        with manifest_file.open(mode="w") as mf:
            for file, hunk in manifest.items():
                hunks = ""
                for start, lines in hunk.items():
                    size = len(lines)
                    hunks += f"{start},{int(start) + (size if size > 1 else 0)};"
                mf.write(f"{file}: {hunks}\n")

        return manifest_file

    def repair(self, signals: dict, repair_request: RepairRequest) -> RepairCommand:
        manifest_file = self.write_manifest(repair_request.working_dir, repair_request.manifest)

        with manifest_file.open(mode='w') as mf:
            mf.write('\n'.join(repair_request.manifest))

        self.repair_cmd.add_arg(opt='--working_dir', arg=str(repair_request.working_dir))
        self.repair_cmd.add_arg(opt='--seed', arg="0")
        self.repair_cmd.add_arg(opt='--verbose', '')
        self.repair_cmd.add_arg(opt='--manifest_path', str(manifest_file))

        for opt, arg in repair_request.args.items():
            self.repair_cmd.add_arg(opt=opt, arg=arg)

        for opt, arg in signals.items():
            self.repair_cmd.add_arg(opt=opt, arg=arg)

        self.app.log.info(f"Repair cmd cquencer {self.repair_cmd}")

        return self.repair_cmd

    def get_patches(self, working_dir: str, target_files: List[str], **kwargs) -> Dict[str, Any]:
        # TODO: implement this
        pass

    def parse_extra(self, extra_args: List[str], signal: Signal) -> str:
        """
            Parses extra arguments in the signals.
        """
        return ""


def load(synapser):
    synapser.handler.register(CquenceR)



