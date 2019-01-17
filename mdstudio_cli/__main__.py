# -*- coding: utf-8 -*-

"""
mdstudio_cli __main__. Calling the python package as command line executable
"""

import sys
import os

module_path = os.path.realpath(os.path.join(__file__, '../../'))
if module_path not in sys.path:
    sys.path.insert(0, module_path)

from mdstudio_cli.cli_entry_point import cli_main

if __name__ == '__main__':
    cli_main()
