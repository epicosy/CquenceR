#!/usr/bin/env python3

from utils.config import configuration
from utils.cmd_parser import parser, run


if __name__ == "__main__":
    args, unk_args = parser.parse_known_args()
    vars_args = dict(vars(args))
    vars_args.update({"configs": configuration})
    vars_args.update({"unknown": unk_args})
    run(**vars_args)
