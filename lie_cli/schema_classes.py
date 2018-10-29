# -*- coding: utf-8 -*-

"""
file: schema_classes.py

Graph ORM classes used for defining input data for MDStudio WAMP endpoints
based on their JSON Schema definitions.
"""

import os
import logging

from lie_graph.graph_axis.graph_axis_mixin import NodeAxisTools
from lie_graph.graph_orm import GraphORM

lg = logging.getLogger('clilogger')


class IntegerType(NodeAxisTools):

    def set_cli_value(self, data):

        parsed = int(data)
        self.nodes[self.nid][self.node_value_tag] = parsed


class FloatType(NodeAxisTools):

    def set_cli_value(self, data):

        parsed = float(data)
        self.nodes[self.nid][self.node_value_tag] = parsed


class BooleanType(NodeAxisTools):

    def set_cli_value(self, data):

        parsed = bool(data)
        self.nodes[self.nid][self.node_value_tag] = parsed


class StringType(NodeAxisTools):

    def set_cli_value(self, data):

        parsed = str(data)
        self.nodes[self.nid][self.node_value_tag] = parsed


class FileType(NodeAxisTools):

    def set_cli_value(self, path):

        # default file object
        file_obj = {u'path': None, u'extension': None, u'content': None, u'encoding': u'utf8'}

        # File object defined
        children = dict([(n.get(self.node_key_tag), n) for n in list(self.children())])

        # Hack for SMILES strings
        if children.get(u'extension', {}).get(self.node_value_tag) == 'smi' and not os.path.isfile(path):
            file_obj[u'extension'] = 'smi'
            file_obj[u'content'] = str(path)

        else:
            path = os.path.abspath(path)
            if not os.path.isfile(path):
                raise IOError('Argument {0} file does not exist: {1}'.format(self.key, path))

            file_obj[u'path'] = path
            file_obj[u'extension'] = os.path.splitext(path)[-1].lstrip('.')
            with open(path, 'r') as inf:
                file_obj[u'content'] = inf.read()

        if children.keys() == [u'content', u'path', u'extension', u'encoding']:
            children[u'path'].set(self.node_value_tag, file_obj[u'path'])
            children[u'extension'].set(self.node_value_tag, file_obj[u'extension'])
            children[u'content'].set(self.node_value_tag, file_obj[u'content'])

        else:
            self.nodes[self.nid][self.node_value_tag] = file_obj


class ArrayType(NodeAxisTools):

    def set_cli_value(self, data):

        data = [d.strip(',') for d in data]
        formatted = []

        for item in data:
            try:
                item = float(item)
            except:
                try:
                    item = int(item)
                except:
                    item = str(item)

            formatted.append(item)

        self.nodes[self.nid][self.node_value_tag] = formatted


CLIORM = GraphORM()
CLIORM.map_node(StringType, type='string')
CLIORM.map_node(IntegerType, type='integer')
CLIORM.map_node(FloatType, type='number')
CLIORM.map_node(BooleanType, type='boolean')
CLIORM.map_node(ArrayType, type='array')
CLIORM.map_node(FileType, format='file')
