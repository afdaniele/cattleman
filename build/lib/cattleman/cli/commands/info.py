import argparse
from typing import Optional

from .. import AbstractCLICommand
from ...types import Arguments


class CLIInfoCommand(AbstractCLICommand):

    KEY = 'info'

    @staticmethod
    def parser(parent: Optional[argparse.ArgumentParser] = None,
               args: Optional[Arguments] = None) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(parents=[parent])
        return parser

    @staticmethod
    def execute(parsed: argparse.Namespace) -> bool:
        # ---
        return True
