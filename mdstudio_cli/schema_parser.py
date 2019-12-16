# -*- coding: utf-8 -*-

"""
file: schema_parser.py
"""

import logging
import re
import os
import shutil

from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value

from graphit.graph_io.io_pydata_format import write_pydata, read_pydata

urisplitter = re.compile("[^\\w']+")
mdstudio_urischema = (u'type', u'group', u'component', u'name', u'version')
wamp_urischema = (u'group', u'component', u'type', u'name')

lg = logging.getLogger('clilogger')


def write_schema_info(schema, uri):
    """
    Write print friendly version of the endpoint schema to stdout

    Print endpoint argument names (key) as CLI arguments that will be used by
    'argparse'. For every argument report if:

    * The argument is required
    * The argument format (integer, number, string, boolean, array, object)
    * Default values for the argument if any
    * Description of the argument

    :param schema:  JSON schema object
    :type schema:   :lie_graph:GraphAxis
    :param uri:     Endpoint URI
    :type uri:      :py:str
    """

    # Main endpoint description
    root = schema.get_root()

    lg.info('\nAPI definition for endpoint: {0}\n'.format(uri))
    lg.info('Title:       {0}'.format(root.get('title', '')))
    lg.info('Description: {0}'.format(root.get('description', '')))

    # Print endpoint argument description
    lg.info('\nArguments:')
    endpoint_args = dict([(n.path(), n) for n in schema.query_nodes({u'schema_label': u'properties'}).iternodes()])
    for arg in sorted(endpoint_args):

        pr = endpoint_args[arg]
        required = 'REQUIRED' if pr.get('required', False) else ''
        arg_type = pr.get('type', '')
        if isinstance(arg_type, list):
            arg_type = arg_type[0]

        lg.info('  --{0:<30}  {1:<8}  {2:<8}  {3:<8}  {4}'.format(re.sub('^root.', '', arg), required, arg_type,
                                                                str(pr.get('default', '')), pr.get('description', '')))


def prepaire_config(schema, config):
    """
    Prepare dictionary of endpoint input data

    Process command line arguments to the endpoint according to the schema definitions

    :param schema:  JSON schema object
    :type schema:   :graphit:GraphAxis
    :param config:  command line arguments to process
    :type config:   :py:dict

    :return:        endpoint input data
    :rtype:         :py:dict
    """

    parsed = []
    for arg in schema.query_nodes({u'schema_label': u'properties'}).iternodes():
        arg_path = re.sub('^root.', '', arg.path())
        if arg_path in config:
            arg.set_cli_value(config[arg_path])
            parsed.append(arg_path)

    # Raise AttributeError in case of unknown arguments in config
    not_parsed = set(config.keys()).difference(set(parsed))
    if not_parsed:
        raise AttributeError('Unknow arguments: {0}'.format(', '.join(not_parsed)))

    # Build parameter dictionary from JSON Schema
    param_dict = write_pydata(schema)

    # Remove all 'value' parameters with value None.
    def recursive_remove_none(d):

        for k in list(d.keys()):
            value = d[k]
            if value is None:
                del d[k]
            elif isinstance(value, dict):
                d[k] = recursive_remove_none(value)

        return d

    if param_dict is not None:
        lg.info(param_dict)
        param_dict = recursive_remove_none(param_dict)
        return param_dict
    else:
        return {}


def create_unique_filename(path, existing):

    counter = 1
    base, ext = os.path.splitext(path)
    while path in existing or os.path.exists(path):
        path = '{0}_{1}{2}'.format(base, counter, ext)
        counter += 1

    return path


def process_results(results):
    """
    Process WAMP endpoint results

    Store the content of all file-like result objct to disk.
    Remaining (nested) results are converted to a flattened representation and
    printend to standard-out (stdout).

    In a flattened representation, the nested parameters names are concatenated
    as a dot seperated string.

    :param results: WAMP endpoint results
    :type results:  :py:dict

    :raises:        AttributeError, input not of type dict
    """

    if not isinstance(results, dict):
        raise AttributeError('Returned endpoint results should be a dict. Got: {0}'.format(type(results)))

    result_graph = read_pydata(results)

    # Export all file-like objects to disk
    currdir = os.getcwd()
    file_names_processed = []
    file_obj_keys = {u'extension', u'encoding', u'content', u'path'}
    nodes_to_remove = []
    for nid, attr in result_graph.nodes.items():
        if len(file_obj_keys.difference(set(attr.keys()))) == 0:

            processed = False

            # File from path
            if attr[u'path'] is not None:
                if os.path.isfile(attr[u'path']):
                    fname = create_unique_filename(os.path.join(currdir, os.path.basename(attr[u'path'])),
                                                   file_names_processed)
                    shutil.copy(attr[u'path'], fname)
                    file_names_processed.append(fname)
                    processed = True

            # File from content
            if not processed and attr[u'content'] is not None:
                fname = os.path.join(currdir, '{0}.{1}'.format(attr[result_graph.node_key_tag], attr[u'extension']))
                fname = create_unique_filename(fname, file_names_processed)

                with open(fname, 'w') as outf:
                    outf.write(attr[u'content'])

                file_names_processed.append(fname)
                processed = True

            if processed:
                nodes_to_remove.append(nid)

    if nodes_to_remove:
        result_graph.remove_nodes(nodes_to_remove)

    # Export remaining parameters
    flattened = write_pydata(result_graph)
    for key, value in flattened.items():
        lg.info('{0} = {1}'.format(key, value))


def schema_uri_to_dict(uri, request=True):
    """
    Parse MDStudio WAMP JSON schema URI to dictionary

    The function accepts both the WAMP standard URI as well as the MDStudio
    resource URI. The latter one defines explicitly if the URI describes a
    'resource' or 'endpoint', uses the full request or response endpoint
    schema name as stored in the database (e.a. <endpoint name>_<request or
    response>) and defines the schema version.

    The WAMP URI style will always default to version 1 of the schema and
    uses the `request` argument to switch between retrieving the 'request' or
    'response' schema for the endpoint

    MDStudio resource URI syntax:
        <resource or endpoint>://<context>/<component>/<endpoint>/v<version ID>'

    WAMP URI syntax:
        <context>.<component>.<endpoint or resource>.<name>

    :param uri:     MDStudio WAMP JSON Schema URI
    :type uri:      :py:str
    :param request: return the request schema for a WAMP style URI else return
                    the response schema
    :type request:  :py:bool

    :return:        parsed JSON schema URI
    :rtype:         :py:dict
    """

    split_uri = re.split(urisplitter, uri)

    # Parse MDStudio resource URI
    if '//' in uri:
        if len(split_uri) != 5:
            raise IOError('Invalid MDStudio schema uri: {0}'.format(uri))
        uri_dict = dict(zip(mdstudio_urischema[:4], split_uri[:4]))
        uri_dict[u'version'] = int(split_uri[-1].strip(u'v'))

    # Parse WAMP URI
    else:
        if len(split_uri) != 4:
            raise IOError('Invalid WAMP schema uri: {0}'.format(uri))
        uri_dict = dict(zip(wamp_urischema, split_uri))
        uri_dict[u'name'] = u'{0}_{1}'.format(uri_dict[u'name'], u'request' if request else u'response')
        uri_dict[u'version'] = 1

    return uri_dict


def dict_to_schema_uri(uri_dict):
    """
    Build MDStudio WAMP JSON schema URI from dictionary

    :param uri_dict: dictionary describing WAMP JSON Schema URI
    :type uri_dict:  :py:dict

    :return:         MDStudio WAMP JSON Schema URI
    :rtype:          :py:str
    """

    return u'{type}://{group}/{component}/{name}/v{version}'.format(**uri_dict)


class SchemaParser(object):
    """
    MDStudio WAMP JSON Schema parser

    Obtain the JSON Schema describing a MDStudio micro service endpoint
    or resource registered with the MDStudio router using its URI.
    The MDStudio router exposes the `endpoint`
    """

    def __init__(self, session):
        """
        :param session: MDStudio WAMP session required to make WAMP calls.
        :type session:  :mdstudio:component:session:ComponentSession
        """

        self.session = session
        self.schema_endpoint = u'mdstudio.schema.endpoint.get'

        # Cache schema's to limit calls
        self._schema_cache = {}

    def _get_refs(self, schema, refs=None):
        """
        Get JSON Schema reference URI's ($ref) from a JSON Schema document.

        :param schema: JSON Schema
        :type schema:  :py:dict

        :return:       list of referred JSON schema's
        :rtype:        :py:list
        """

        if refs is None:
            refs = []

        for key, value in schema.items():
            if key == u'$ref':
                refs.append(value)
            elif isinstance(value, dict):
                self._get_refs(value, refs=refs)

        return refs

    @chainable
    def _recursive_schema_call(self, uri_dict):
        """
        Recursivly obtain endpoint schema's

        Recursivly calls the MDStudio schema endpoint to retrieve JSON schema
        definitions for the (nested) endpoint and resources based on a URI.
        In document references to other schema's use the JSON Schema '$ref'
        argument accepting a MDStudio schema URI as value.

        :param uri_dict: dictionary from the `schema_uri_to_dict` function
                         describing WAMP JSON Schema URI.
        :type uri_dict:  :py:dict
        """

        uri = dict_to_schema_uri(uri_dict)
        if uri not in self._schema_cache:

            response = {}
            try:
                response = yield self.session.group_context(
                    self.session.component_config.static.vendor).call(
                    self.schema_endpoint, uri_dict,
                    claims={u'vendor': self.session.component_config.static.vendor})
            except Exception:
                logging.error('Unable to call endpoint: {0}'.format(uri))

            self._schema_cache[uri] = response
            refs = self._get_refs(response)

            if refs:
                for ref in set(refs):
                    yield self._recursive_schema_call(schema_uri_to_dict(ref))

    def _build_schema(self, schema):
        """
        Build full JSON Schema from source and referenced schemas
        """

        for key in list(schema.keys()):

            value = schema[key]
            if isinstance(value, dict):
                if u'$ref' in value:
                    schema[key].update(self._schema_cache[value[u'$ref']])
                self._build_schema(value)
            elif key == '$ref':
                prop = self._schema_cache[value][u'properties']
                schema[u'properties'] = self._build_schema(prop)

        return schema

    @chainable
    def get(self, uri, clean_cache=True, **kwargs):
        """
        Retrieve the JSON Schema describing an MDStudio endpoint (request or
        response) or resource based on a WAMP or MDStudio schema URI.

        The method returns a Twisted deferred object for which the results
        can be obtained using `yield`.

        :param uri:         MDStudio endpoint or resource JSON Schema URI to
                            retrieve
        :type uri:          :py:str
        :param clean_cache: clean the uri cache used to limit calls to the
                            same uri
        :type clean_cache:  :py:bool
        :param kwargs:      additional keyword arguments are passed to the
                            `schema_uri_to_dict` function
        :type kwargs:       :py:dict

        :return:            Schema as Twisted deferred object
        """

        # Parse uri elements to dictionary
        uri_dict = schema_uri_to_dict(uri, **kwargs)
        uri = dict_to_schema_uri(uri_dict)

        # Clean the uri cache
        if clean_cache:
            self._schema_cache = {}

        # Recursively call the MDStudio schema endpoint to obtain schema's
        yield self._recursive_schema_call(uri_dict)
        return_value(self._build_schema(self._schema_cache.get(uri, {})))
