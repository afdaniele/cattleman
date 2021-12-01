import argparse
from typing import Optional

from .. import AbstractCLICommand
from ...orchestrator.orchestrator import Orchestrator
from ...persistency import Persistency
from ...types import Arguments


class CLIManagerCommand(AbstractCLICommand):

    KEY = 'manager'

    @staticmethod
    def parser(parent: Optional[argparse.ArgumentParser] = None,
               args: Optional[Arguments] = None) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(parents=[parent])
        return parser

    @staticmethod
    def execute(parsed: argparse.Namespace) -> bool:
        # load configuration from disk
        Persistency.load_from_disk()
        # create orchestrator (aka manager)
        orchestrator = Orchestrator()
        # run orchestrator
        orchestrator.run()
        # ---
        return True
