# -*- coding: utf-8 -*-

"""
file: schema_classes.py

Graph ORM classes used for defining input data for MDStudio WAMP endpoints
based on their JSON Schema definitions.
"""

import os
import logging

from graphit.graph_axis.graph_axis_mixin import NodeAxisTools
from graphit.graph_orm import GraphORM

lg = logging.getLogger('clilogger')


class IntegerType(NodeAxisTools):

    def set_cli_value(self, data):

        parsed = int(data)
        self.nodes[self.nid][self.data.value_tag] = parsed


class FloatType(NodeAxisTools):

    def set_cli_value(self, data):

        parsed = float(data)
        self.nodes[self.nid][self.data.value_tag] = parsed


class BooleanType(NodeAxisTools):

    def set_cli_value(self, data):

        parsed = bool(data)
        self.nodes[self.nid][self.data.value_tag] = parsed


class StringType(NodeAxisTools):

    def set_cli_value(self, data):

        parsed = str(data)
        self.nodes[self.nid][self.data.value_tag] = parsed


class FileType(NodeAxisTools):

    def set_cli_value(self, path):

        # default file object
        file_obj = {u'path': None, u'extension': None, u'content': None, u'encoding': u'utf8'}

        # File object defined
        children = dict([(n.get(self.data.key_tag), n) for n in list(self.children())])

        # Hack for SMILES strings
        if children.get(u'extension', {}).get(self.data.value_tag) == 'smi' and not os.path.isfile(path):
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

        if set(children.keys()) == {u'content', u'path', u'extension', u'encoding'}:
            children[u'path'].set(self.data.value_tag, file_obj[u'path'])
            children[u'extension'].set(self.data.value_tag, file_obj[u'extension'])
            children[u'content'].set(self.data.value_tag, file_obj[u'content'])
        else:
            self.nodes[self.nid][self.data.value_tag] = file_obj


class ArrayType(NodeAxisTools):

    def set_cli_value(self, data):

        data = [d.strip(',') for d in data]
        formatted = []

        for item in data:
            try:
                item = float(item)
            except ValueError:
                try:
                    item = int(item)
                except ValueError:
                    item = str(item)

            formatted.append(item)

        self.nodes[self.nid][self.data.value_tag] = formatted


CLIORM = GraphORM()
CLIORM.node_mapping.add(StringType, lambda x: x.get('type') == 'string')
CLIORM.node_mapping.add(IntegerType, lambda x: x.get('type') == 'integer')
CLIORM.node_mapping.add(FloatType, lambda x: x.get('type') == 'number')
CLIORM.node_mapping.add(BooleanType, lambda x: x.get('type') == 'boolean')
CLIORM.node_mapping.add(ArrayType, lambda x: x.get('type') == 'array')
CLIORM.node_mapping.add(FileType, lambda x: x.get('format') == 'file')
