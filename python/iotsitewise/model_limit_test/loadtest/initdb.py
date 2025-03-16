import os
import time

import boto3
from anytree import Node, PreOrderIter
from botocore.exceptions import ClientError
from dynamodb_json import json_util as json
from graphlib import TopologicalSorter


NEW_MODELS_TABLE = os.environ['NEW_MODELS_TABLE']
MODELS_TABLE = os.environ['MODELS_TABLE']
DDB_BATCH_SIZE = 25


class AssetModelTree:
    def __init__(self, root_node):
        self.root_node = root_node

    @staticmethod
    def balanced_tree(prefix, num_models, max_children):
        root_node = Node(f'{prefix}-1')
        while root_node.size < num_models:
            for node in root_node.leaves:
                for _ in range(max_children):
                    if root_node.size < num_models:
                        Node(f'{prefix}-{root_node.size + 1}', parent=node)
        return AssetModelTree(root_node)

    @classmethod
    def flat_tree(cls, prefix, num_models):
        return cls.balanced_tree(prefix, num_models, num_models)

    @classmethod
    def single_path(cls, prefix, num_models):
        return cls.balanced_tree(prefix, num_models, 1)

    def batches(self):
        graph = TopologicalSorter()
        for n in PreOrderIter(self.root_node):
            if n.parent:
                graph.add(n.parent, n)

        graph.prepare()
        while graph.is_active():
            node_group = graph.get_ready()
            yield list(node_group)
            graph.done(*node_group)


def batch_put_items(ddb, table_name, items):
    print(f"Writing {len(items)} entries to '{table_name}' table")
    for i in range(0, len(items), DDB_BATCH_SIZE):
        chunk = items[i:i + DDB_BATCH_SIZE]
        batch_items = {
            table_name: [{ 'PutRequest': { 'Item': json.dumps(item, as_dict=True) }}
                         for item in chunk]
        }
        time.sleep(0.1)
        response = ddb.batch_write_item(RequestItems=batch_items)
        unprocessed = response.get('UnprocessedItems', {})
        if unprocessed:
            raise RuntimeError(f'Some items were not written to DDB: {unprocessed}')


def update_db_items(ddb, tree):
    new_models_items = []
    models_items = []
    for idx, node_group in enumerate(tree.batches()):
        for n in node_group:
            new_models_items.append({
                'group': idx,
                'name': n.name
            })
            models_items.append({
                'name': n.name,
                'is_leaf_node': len(n.children) == 0,
                'sw_id': None,
                'children': [c.name for c in n.children]
            })

    models_items.append({
        'name': 'config',
        'current_group': 0
    })

    batch_put_items(ddb, NEW_MODELS_TABLE, new_models_items)
    batch_put_items(ddb, MODELS_TABLE, models_items)


def handler(event, context):
    prefix = event['prefix']
    num_models = event['num_models']
    max_children = event.get('max_children', 2)
    tree_type = event['tree_type']

    ddb = boto3.client('dynamodb', endpoint_url=os.getenv('DDB_ENDPOINT'))

    if tree_type == 'balanced':
        tree = AssetModelTree.balanced_tree(prefix, num_models, max_children)
    elif tree_type == 'flat':
        tree = AssetModelTree.flat_tree(prefix, num_models)
    elif tree_type == 'single-path':
        tree = AssetModelTree.single_path(prefix, num_models)
    else:
        raise RuntimeError(f'Invalid tree type. Event: {event}')

    update_db_items(ddb, tree)
