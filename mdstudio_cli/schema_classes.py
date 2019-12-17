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

    def set(self, key, value=None):

        parsed = int(value)
        self.nodes[self.nid][key] = parsed


class FloatType(NodeAxisTools):

    def set(self, key, value=None):

        parsed = float(value)
        self.nodes[self.nid][key] = parsed


class BooleanType(NodeAxisTools):

    def set(self, key, value=None):

        parsed = bool(value)
        self.nodes[self.nid][key] = parsed


class FileType(NodeAxisTools):

    def set(self, key, value=None):

        # default file object
        file_obj = {u'path': None, u'extension': None, u'content': None, u'encoding': u'utf8'}

        # File object defined
        children = dict([(n.get(key), n) for n in list(self.children())])

        # Hack for SMILES strings
        lg.info(self.children().values())
        if children.get(u'extension', {}).get(key) == 'smi' and not os.path.isfile(value):
            file_obj[u'extension'] = 'smi'
            file_obj[u'content'] = str(value)

        else:
            abspath = os.path.abspath(value)
            if not os.path.isfile(abspath):
                raise IOError('Argument {0} file does not exist: {1}'.format(self.key, value))

            file_obj[u'path'] = abspath
            file_obj[u'extension'] = os.path.splitext(abspath)[-1].lstrip('.')
            with open(abspath, 'r') as inf:
                file_obj[u'content'] = inf.read()

        if set(children.keys()) == {u'content', u'path', u'extension', u'encoding'}:
            children[u'path'].set(self.data.value_tag, file_obj[u'path'])
            children[u'extension'].set(key, file_obj[u'extension'])
            children[u'content'].set(key, file_obj[u'content'])
        else:
            self.nodes[self.nid][key] = file_obj


class ArrayType(NodeAxisTools):

    def set(self, key, value=None):

        data = [d.strip(',') for d in value]
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

        self.nodes[self.nid][key] = formatted


CLIORM = GraphORM()
CLIORM.node_mapping.add(IntegerType, lambda x: x.get('type') == 'integer')
CLIORM.node_mapping.add(FloatType, lambda x: x.get('type') == 'number')
CLIORM.node_mapping.add(BooleanType, lambda x: x.get('type') == 'boolean')
CLIORM.node_mapping.add(ArrayType, lambda x: x.get('type') == 'array')
CLIORM.node_mapping.add(FileType, lambda x: x.get('format') == 'file')
