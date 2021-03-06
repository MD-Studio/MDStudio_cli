# -*- coding: utf-8 -*-

"""
mdstudio_cli command line entry point converted into the mdstudio-cli command
line tool by Python setuptools upon installation of the package.

Requires the /bin directory of the Python version used to isntall the package
to be available in the users PATH.
"""

from mdstudio.runner import main

from mdstudio_cli.wamp_services import CliWampApi
from mdstudio_cli.cli_parser import mdstudio_cli_parser

import logging
import sys


def cli_main():
    """
    Enable mdstudio_cli as a command line tool

    Main entry point function called from the mdstudio-cli command line tool
    created by Python setuptools upon package installation.
    """

    # Override txaio logger to print result to stdout
    lg = logging.getLogger('clilogger')
    lg.setLevel(logging.INFO)
    lg.addHandler(logging.StreamHandler(sys.stdout))

    # Parse command line arguments
    config = mdstudio_cli_parser()

    main(CliWampApi, auto_reconnect=False, log_level=config['log_level'], extra=config, daily_log=False)
