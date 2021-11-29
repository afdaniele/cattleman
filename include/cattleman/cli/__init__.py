import argparse
from abc import abstractmethod, ABC
from typing import Optional

from cattleman.types import Arguments


class AbstractCLICommand(ABC):

    KEY = None

    @classmethod
    def name(cls) -> str:
        return cls.KEY

    @staticmethod
    def common_parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument(
            "-v",
            "--verbose",
            default=False,
            action="store_true",
            help="Be verbose"
        )
        parser.add_argument(
            "--debug",
            default=False,
            action="store_true",
            help="Enable debug mode"
        )
        return parser

    @classmethod
    def get_parser(cls, args: Arguments) -> argparse.ArgumentParser:
        common_parser = cls.common_parser()
        command_parser = cls.parser(common_parser, args)
        command_parser.prog = f'cattle {cls.KEY}'
        return command_parser

    @staticmethod
    @abstractmethod
    def parser(parent: Optional[argparse.ArgumentParser] = None,
               args: Optional[Arguments] = None) -> argparse.ArgumentParser:
        pass

    @staticmethod
    @abstractmethod
    def execute(parsed: argparse.Namespace) -> bool:
        pass


__all__ = [
    "AbstractCLICommand"
]
