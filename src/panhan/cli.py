import inspect
import sys
from argparse import ArgumentParser
from logging import DEBUG, INFO

from panhan import __version__, commands
from panhan.logger import logger


def get_parser() -> ArgumentParser:
    """Get CLI argument parser.

    Returns:
        ArgumentParser: argument parser.
    """
    parser = ArgumentParser(prog="panhan")
    parser.add_argument("SOURCE", nargs="*", help="markdown source file(s)")
    parser.add_argument("--panhan-yaml", help="path to panhan.yaml")
    parser.add_argument(
        "--print-yaml-template",
        action="store_true",
        help="print panhan config template",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="explain what is being done"
    )
    parser.add_argument("--debug", action="store_true", help="print debug output")
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def cli() -> None:
    """Launch command line interface."""
    parser = get_parser()
    args = parser.parse_args()

    # Set logging level.
    if args.debug:
        logger.setLevel(DEBUG)
    elif args.verbose:
        logger.setLevel(INFO)

    # Print usage if no arguments passed.
    if len(sys.argv) < 2:
        parser.print_help()
        return

    # Print YAML template and quit.
    if args.print_yaml_template:
        commands.print_panhan_yaml_template()
        return

    # Select args that should be passed to main.
    args_dict = {
        k: v
        for k, v in vars(args).items()
        if k in inspect.signature(commands.process_source_files).parameters
    }

    commands.process_source_files(**args_dict)


if __name__ == "__main__":
    cli()
