# -*- coding: utf-8 -*-

"""
mdstudio_cli __main__. Calling the python package as command line executable
"""

import logging
import sys

from mdstudio.runner import main

from mdstudio_cli.wamp_services import CliWampApi
from mdstudio_cli.cli_parser import mdstudio_cli_parser

# Override txaio logger to print result to stdout
lg = logging.getLogger('clilogger')
lg.setLevel(logging.INFO)
lg.addHandler(logging.StreamHandler(sys.stdout))


if __name__ == '__main__':

    # Parse command line arguments
    config = mdstudio_cli_parser()

    main(CliWampApi,  auto_reconnect=False, log_level=config['log_level'], extra=config)
