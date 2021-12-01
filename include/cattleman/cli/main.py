import argparse
import logging
import sys

import cattleman
from cattleman.exceptions import CattlemanException

from cattleman.logger import cmlogger
from cattleman.cli.commands.info import CLIInfoCommand
from cattleman.cli.commands.manager import CLIManagerCommand

_supported_commands = {
    'info': CLIInfoCommand,
    'manager': CLIManagerCommand,
}


def run():
    cmlogger.info(f"Cattleman - v{cattleman.__version__}")
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        'command',
        choices=_supported_commands.keys()
    )
    # print help (if needed)
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        parser.print_help()
        return
    # ---
    # parse `command`
    parsed, remaining = parser.parse_known_args()
    # get command
    command = _supported_commands[parsed.command]
    # let the command parse its arguments
    cmd_parser = command.get_parser(remaining)
    parsed = cmd_parser.parse_args(remaining)
    # enable debug
    if parsed.debug:
        cmlogger.setLevel(logging.DEBUG)
    # execute command
    try:
        command.execute(parsed)
    except CattlemanException as e:
        cmlogger.error(str(e))
    except KeyboardInterrupt:
        cmlogger.info(f"Operation aborted by the user")


if __name__ == '__main__':
    run()
