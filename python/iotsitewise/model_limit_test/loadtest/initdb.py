import os
import time
from collections import deque

import boto3
import json
from botocore.exceptions import ClientError
from dynamodb_json import json_util as ddbjson


MODELS_TABLE = os.environ['MODELS_TABLE']
DDB_ENDPOINT = os.getenv('DDB_ENDPOINT')
S3_BUCKET = os.environ['DATA_BUCKET']
MODELS_FILE_KEY = os.environ['MODELS_FILE_KEY']
REGION = os.environ['AWS_DEFAULT_REGION']


class Node:
    def __init__(self, name, parent=None):
        self.name = name
        self.children = []
        if parent:
            self.parent = parent
            parent.add_child(self)

    def add_child(self, child):
        child.parent = self
        self.children.append(child)


class Tree:
    def __init__(self, root):
        self.root = root

    @classmethod
    def create_binary(cls, prefix, num_models):
        return cls.create(prefix, num_models, 2)

    @staticmethod
    def create(prefix, num_models, max_children):
        names = (f'{prefix}-{idx}' for idx in range(num_models))
        first_name = next(names)
        root_node = Node(first_name)
        queue = deque()
        queue.append(root_node)
        for name in names:
            while queue:
                node = queue.popleft()
                if len(node.children) < max_children:
                    node.add_child(Node(name))
                    queue.appendleft(node)
                    break
                else:
                    queue.extend(node.children)
        return Tree(root_node)

    def batches(self):
        levels = []
        curr_level = [self.root]
        while curr_level:
            levels.append(curr_level)
            curr_level = [child for node in curr_level
                                for child in node.children]
        for level in reversed(levels):
            yield level


class FlatTree:
    def __init__(self, prefix, num_models):
        self.root_node = Node(f'{prefix}-1')
        self.children = [Node(f'{prefix}-{idx}', parent=self.root_node)
                         for idx in range(2, num_models + 1)]

    def batches(self):
        return [self.children, [self.root_node]]


class SinglePath:
    def __init__(self, prefix, num_models):
        self.levels = [[Node(f'{prefix}-1')]]
        for idx in range(2, num_models + 1):
            parent = self.levels[-1][0]
            self.levels.append([ Node(f'{prefix}-{idx}', parent=parent) ])

    def batches(self):
        return reversed(self.levels)


class DisconnectedNodes:
    def __init__(self, prefix, num_models):
        self.models = [Node(f'{prefix}-{i}') for i in range(num_models)]

    def batches(self):
        return [self.models]


def to_models_obj(tree):
    models = { 'models': [] }
    for idx, node_group in enumerate(tree.batches()):
        for n in node_group:
            models['models'].append({
                'name': n.name,
                'group': idx,
                'is_leaf_node': len(n.children) == 0,
                'sw_id': None,
                'children': [c.name for c in n.children],
                'parent': n.parent.name if n.parent else None,
            })
    return models


def handler(event, context):
    prefix = event['prefix']
    num_models = event['num_models']
    max_children = event['max_children']
    tree_type = event['tree_type']

    s3 = boto3.client('s3')
    ddb = boto3.client('dynamodb', endpoint_url=DDB_ENDPOINT)

    if tree_type == 'tree':
        tree = Tree.create(prefix, num_models, max_children)
    elif tree_type == 'binary':
        tree = Tree.create_binary(prefix, num_models)
    elif tree_type == 'flat':
        tree = FlatTree(prefix, num_models)
    elif tree_type == 'single-path':
        tree = SinglePath(prefix, num_models)
    elif tree_type == 'disconnected':
        tree = DisconnectedNodes(prefix, num_models)
    else:
        raise RuntimeError(f'Invalid tree type. Event: {event}')

    models = to_models_obj(tree)
    s3.put_object(Body=json.dumps(models), Bucket=S3_BUCKET, Key=MODELS_FILE_KEY , ContentType='application/json')
    print(f'Updated file s3://{S3_BUCKET}/{MODELS_FILE_KEY}')

    config = { 'name': 'config', 'current_group': 0 }
    ddb.put_item(TableName=MODELS_TABLE, Item=ddbjson.dumps(config, as_dict=True))
