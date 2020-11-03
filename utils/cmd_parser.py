#!/usr/bin/env python3

import argparse
from collections import Callable

from utils.command import Command
from utils.commands.preprocess import Preprocess
from utils.commands.test import Test
from utils.commands.train import Train
from utils.commands.repair import Repair
from utils.commands.stats import Stats
from utils.commands.clean import Clean

COMMANDS = {}

parser = argparse.ArgumentParser(prog="CquenceR",
                                 description='Program Repair Tool based on Sequence-to-Sequence Learning.')
main_parser = argparse.ArgumentParser(add_help=False)

main_parser.add_argument('-v', '--verbose', help='Verbose output.', action='store_true')
main_parser.add_argument('-seed', required=False, action='store_true',
                         help='Seed used for better reproducibility between experiments')
main_parser.add_argument('-l', '--log_file', type=str, default=None, help='Log file to write the results to.')

subparsers = parser.add_subparsers()


def add_command(name: str, command: Command, description: str):
    cmd_parser = subparsers.add_parser(name=name, help=description, parents=[main_parser])
    cmd_parser.set_defaults(command=command)
    cmd_parser.set_defaults(name=name)

    return cmd_parser


def register(definition: Callable, arguments: Callable):
    """Register a command as a positional argument"""
    cmd_parser = add_command(**definition())
    arguments(cmd_parser)


register(definition=Preprocess.definition, arguments=Preprocess.add_arguments)
register(definition=Train.definition, arguments=Train.add_arguments)
register(definition=Test.definition, arguments=Test.add_arguments)
register(definition=Repair.definition, arguments=Repair.add_arguments)
register(definition=Stats.definition, arguments=Stats.add_arguments)
register(definition=Clean.definition, arguments=Clean.add_arguments)


def run(command: Command, **kwargs):
    cmd = command(**kwargs)
    cmd()
