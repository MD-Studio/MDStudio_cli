# -*- coding: utf-8 -*-

"""
Command Line Interface to the methods exposed by MDStudio microservices
"""

import argparse
import re
import os
import sys

USAGE = """
MDStudio command line interface.

Call a method exposed by a MDStudio microservice using it's public URI

"""

# If file path, read file content and transport "over wire"
PARSE_FILES = True


def _commandline_arg_py2(bytestring):
    """
    Decode unicode command line strings on Python 2.x
    """
    unicode_string = bytestring.decode(sys.getfilesystemencoding())
    return unicode_string


def _commandline_arg_py3(bytestring):
    """
    In Python 3.x everything is unicode
    """
    return bytestring


# Define command line argument unicode decoder based on Python major version
if sys.version[0] == '2':
    _commandline_arg = _commandline_arg_py2
else:
    _commandline_arg = _commandline_arg_py3


def _abspath(path):
    """
    Check file and resolve absolute path

    :param path: relative path
    :type path:  :py:str

    :return:     absolute path
    :rtype:      :py:str
    """

    if os.path.isfile(path):
        return os.path.abspath(path)

    return path


def _parse_variable_arguments(args, prefix='-'):
    """
    Parse an argument list with keyword argument identified as having a single
    or double dash as prefix (-, --) or other character defined by the `prefix`
    argument.
    All non-keyword arguments following a keyword are assigned values to the
    keyword. If there are no values, the keyword is treated as boolean argument.

    :param args:   argument list to parse
    :type args:    :py:list
    :param prefix: prefix character used to identify keyword arguments
    :type prefix:  :py:str

    :return:       variable name/arguments dictionary
    :rtype:        :py:dict
    """

    # Keyword positions, discard negative numbers
    positions = [e for e, n in enumerate(args) if n.startswith(prefix) and not re.match('^[-+]?[0-9]+$', n)]

    # Split the argument list based on keyword positions
    method_args = {}
    length = len(positions) - 1
    for i, kwp in enumerate(positions):
        if i < length:
            argument = args[kwp: positions[i + 1]]
        else:
            argument = args[kwp:]

        # Check for double declaration of keywords, not allowed
        var_name = argument[0].strip(prefix)
        assert var_name not in method_args, 'Variable declared twice: {0}'.format(var_name)

        # Format boolean argument
        if len(argument) == 1:
            method_args[var_name] = True
        elif len(argument) == 2:
            method_args[var_name] = argument[1]
        else:
            method_args[var_name] = argument[1:]

    return method_args


def mdstudio_cli_parser():
    """
    Command Line Interface parser

    Builds the CLI parser used by the mdstudio_cli script
    """

    # Create the top-level parser
    parser = argparse.ArgumentParser(prog="MDStudio", usage=USAGE, description="MDStudio CLI")

    # Parse application session and microservice WAMP arguments
    parser.add_argument('-u', '--uri', type=_commandline_arg, dest='uri', required=True, help='Microservice method URI')
    parser.add_argument('-i', '--info', action='store_true', dest='get_endpoint_info', help='Get method API')
    parser.add_argument('-j', '--store_json', action='store_true', dest="store_json", help='Store results as JSON')
    parser.add_argument('-l', '--log', type=_commandline_arg, dest='log_level', default='none', help='Log level')

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # parse command line arguments
    options, method_args = parser.parse_known_args()

    # Convert argparse NameSpace object to dict
    options = vars(options)

    # Parse all unknown arguments. These are the keyword arguments passed to
    # the microservice method
    options['package_config'] = _parse_variable_arguments(method_args)

    return options
