# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os
import json
import logging

from twisted.internet import reactor
from autobahn.wamp.exception import ApplicationError
from lie_graph.graph_io.io_jsonschema_format import read_json_schema

from mdstudio.component.session import ComponentSession
from mdstudio.deferred.chainable import chainable

from mdstudio_cli.schema_parser import SchemaParser, write_schema_info, prepaire_config, process_results
from mdstudio_cli.schema_classes import CLIORM

lg = logging.getLogger('clilogger')


class CliWampApi(ComponentSession):
    """
    CLI WAMP methods.
    """

    def authorize_request(self, uri, claims):
        """
        If you were allowed to call this in the first place,
        I will assume you are authorized
        """

        return True

    def result_callback(self, result):
        """
        WAMP result callback

        Process the results storing all file-like output to file.
        Optionally store the full results directory as a JSON file.

        :param result:  WAMP results
        :type result:   :py:dict
        """

        # Store results as JSON
        if self.config.extra.get('store_json', False):
            result_json = os.path.join(os.getcwd(), '{0}.json'.format(self.config.extra['uri']))
            json.dump(result, open(result_json, 'w'))

        # Process file-like output and print remaining.
        process_results(result)

        # Disconnect from broker and stop reactor event loop
        self.disconnect()
        reactor.stop()

    def error_callback(self, failure):
        """
        WAMP error callback

        Process a WAMP endpoint failure and write the failure message to
        standard out (stdout).

        :param failure:  Endpoint failure message
        """

        failure_message = failure
        if isinstance(failure, Exception) or isinstance(failure, str):
            failure_message = str(failure)
        elif isinstance(failure.value, ApplicationError):
            failure_message = failure.value.error_message()
        else:
            failure.getErrorMessage()

        lg.error('Unable to process: {0}'.format(failure_message))

        # Disconnect from broker and stop reactor event loop
        self.disconnect()
        reactor.stop()

    @chainable
    def on_run(self):

        # Get endpoint config
        config = self.config.extra

        # Retrieve JSON schemas for the endpoint request and response
        schemaparser = SchemaParser(self)
        request = yield schemaparser.get(uri=config['uri'], request=True)

        request = read_json_schema(request)
        request.orm = CLIORM

        # Write print friendly endpoint definition to stdout or call endpoint
        if config['get_endpoint_info']:
            write_schema_info(request, config['uri'])

            # Disconnect from broker and stop reactor event loop
            self.disconnect()
            reactor.stop()

        else:
            endpoint_input = prepaire_config(request, config['package_config'])

            # Call method and wait for results
            deferred = self.call(config['uri'], endpoint_input)
            deferred.addCallback(self.result_callback)
            deferred.addErrback(self.error_callback)
