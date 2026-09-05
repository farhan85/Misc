import csv
import os
import threading
from concurrent.futures import ThreadPoolExecutor

import boto3
import click
from anytree import LevelOrderGroupIter, Node, PreOrderIter, RenderTree
from botocore.exceptions import ClientError


METRIC_NAME = 'power_avg'
HIERARCHY_NAME_1 = 'hierarchy1'
HIERARCHY_NAME_2 = 'hierarchy2'

thread_local = threading.local()
MAX_WORKERS = 8

CSV_FIELDS = ['name', 'parent', 'model_id', 'prop_id', 'hierarchy_id_1', 'hierarchy_id_2']


def get_prop_id(asset_model, prop_name):
    for p in asset_model.get('assetModelProperties', []):
        if p['name'] == prop_name:
            return p['id']


def get_hierarchy_id(asset_model, hierarchy_name):
    for h in asset_model.get('assetModelHierarchies', []):
        if h['name'] == hierarchy_name:
            return h['id']


def create_leaf_node_spec(name):
    return {
        'assetModelName': name,
        'assetModelDescription': 'Leaf node',
        'assetModelProperties': [
            {
                'name': 'power',
                'dataType': 'DOUBLE',
                'unit': 'Watts',
                'type': {'measurement': {}}
            },
            {
                'name': METRIC_NAME,
                'dataType': 'DOUBLE',
                'unit': 'Watts',
                'type': {
                    'metric': {
                        'expression': 'avg(p)',
                        'variables': [
                            {'name': 'p', 'value': {'propertyId': 'power'}}
                        ],
                        'window': {'tumbling': {'interval': '1m'}}
                    }
                }
            }
        ]
    }


def create_ancestor_node_spec(name, description, child_models):
    hierarchy_names = [HIERARCHY_NAME_1, HIERARCHY_NAME_2]
    child_ids = [c.model_id for c in child_models]
    prop_ids = [c.prop_id for c in child_models]
    return {
        'assetModelName': name,
        'assetModelDescription': description,
        'assetModelProperties': [
            {
                'name': METRIC_NAME,
                'dataType': 'DOUBLE',
                'unit': 'Watts',
                'type': {
                    'metric': {
                        'expression': 'avg(p1,p2)',
                        'variables': [
                            {'name': f'p{i}', 'value': {'propertyId': p[0], 'hierarchyId': p[1]}}
                            for i, p in enumerate(zip(prop_ids, hierarchy_names), start=1)
                        ],
                        'window': {'tumbling': {'interval': '1m'}}
                    }
                }
            }
        ],
        'assetModelHierarchies': [
            {'name': h[0], 'childAssetModelId': h[1]}
            for h in zip(hierarchy_names, child_ids)
        ]
    }


def create_tree(num_nodes, prefix):
    nodes = [Node(f"{prefix}-{i}") for i in range(1, num_nodes + 1)]
    for i in range(1, num_nodes):
        parent_index = (i - 1) // 2
        nodes[i].parent = nodes[parent_index]
    return nodes[0]


def append_row(state_file, save_lock, node):
    with save_lock:
        with open(state_file, 'a', newline='') as f:
            csv.DictWriter(f, fieldnames=CSV_FIELDS).writerow({
                'name': node.name,
                'parent': node.parent.name if node.parent else '',
                'model_id': node.model_id,
                'prop_id': node.prop_id,
                'hierarchy_id_1': node.hierarchy_id_1 or '',
                'hierarchy_id_2': node.hierarchy_id_2 or '',
            })
            f.flush()
            os.fsync(f.fileno())


def load_model_ids(root_node, state_file):
    with open(state_file, newline='') as f:
        created = {row['name']: row for row in csv.DictReader(f)}

    for node in PreOrderIter(root_node):
        row = created.get(node.name)
        if row:
            node.model_id = row['model_id']
            node.prop_id = row['prop_id']
            node.hierarchy_id_1 = row['hierarchy_id_1'] or None
            node.hierarchy_id_2 = row['hierarchy_id_2'] or None
    return len(created)


def build_tree_from_file(state_file):
    with open(state_file, newline='') as f:
        rows = list(csv.DictReader(f))

    nodes = {}
    for row in rows:
        node = Node(row['name'])
        node.model_id = row['model_id']
        node.prop_id = row['prop_id']
        node.hierarchy_id_1 = row['hierarchy_id_1'] or None
        node.hierarchy_id_2 = row['hierarchy_id_2'] or None
        nodes[row['name']] = node

    root = None
    for row in rows:
        name = row['name']
        parent_name = row['parent']
        if parent_name:
            nodes[name].parent = nodes[parent_name]
        else:
            root = nodes[name]
    return root


def get_client(client_factory):
    if not hasattr(thread_local, 'client'):
        thread_local.client = client_factory()
    return thread_local.client


def create_models(executor, root_node, client_factory, state_file):
    save_lock = threading.Lock()

    def create(node):
        if hasattr(node, 'model_id'):
            return

        if node.is_leaf:
            spec = create_leaf_node_spec(node.name)
        else:
            description = 'Root node' if node.is_root else 'Internal node'
            spec = create_ancestor_node_spec(node.name, description, node.children)
        sitewise = get_client(client_factory)
        response = sitewise.create_asset_model(**spec)
        model_id = response['assetModelId']

        model = sitewise.describe_asset_model(assetModelId=model_id)
        node.model_id = model_id
        node.prop_id = get_prop_id(model, METRIC_NAME)
        node.hierarchy_id_1 = get_hierarchy_id(model, HIERARCHY_NAME_1)
        node.hierarchy_id_2 = get_hierarchy_id(model, HIERARCHY_NAME_2)
        append_row(state_file, save_lock, node)

        sitewise.get_waiter('asset_model_active').wait(assetModelId=model_id)
        print(f'Created AssetModel {node.name} {model_id}')

    # Child models need to be created before parents.
    for level in reversed(list(LevelOrderGroupIter(root_node))):
        futures = [executor.submit(create, node) for node in level]
        for future in futures:
            future.result()


def delete_models(executor, root_node, client_factory):
    def delete(node):
        sitewise = get_client(client_factory)
        try:
            sitewise.delete_asset_model(assetModelId=node.model_id)
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise
        sitewise.get_waiter('asset_model_not_exists').wait(assetModelId=node.model_id)
        print(f'Deleted AssetModel {node.name} {node.model_id}')

    # Parent models need to be deleted before children.
    for level in LevelOrderGroupIter(root_node):
        futures = [executor.submit(delete, node) for node in level]
        for future in futures:
            future.result()


def render_tree(root_node):
    def node_str(node):
        h1_id = node.hierarchy_id_1 or ''
        h2_id = node.hierarchy_id_2 or ''
        return f'{node.name}(id={node.model_id}, prop={node.prop_id}, h1={h1_id}, h2={h2_id})'
    return RenderTree(root_node).by_attr(node_str)


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-p', '--prefix', help='Model name prefix')
@click.option('-n', '--num-models', '--num', type=int, help='Number of models to create')
@click.option('-f', '--state-file', required=True, help='CSV state file to append progress to and resume from')
@click.option('-d', '--delete', is_flag=True, help='Delete all models recorded in the state file')
@click.option('-t', '--tree', is_flag=True, help='Render the model tree after creating')
@click.option('-r', '--region', help='AWS region', envvar='AWS_DEFAULT_REGION')
def main(prefix, num_models, state_file, delete, tree, stage, region):
    client_factory = lambda: boto3.client('iotsitewise', region_name=region)

    if delete:
        if not os.path.exists(state_file):
            raise click.UsageError(f'State file {state_file} not exists')
        root_node = build_tree_from_file(state_file)
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            delete_models(executor, root_node, client_factory)
        print('Deleted all models')
        return

    if not prefix or not num_models:
        raise click.UsageError('Missing --prefix and --num-models')
    if not os.path.exists(state_file):
        with open(state_file, 'w', newline='') as f:
            csv.DictWriter(f, fieldnames=CSV_FIELDS).writeheader()

    root_node = create_tree(num_models, prefix)
    loaded = load_model_ids(root_node, state_file)
    print(f'Loaded {loaded} models from {state_file}')
    print(f'Remaining {num_models - loaded} models to be created')

    if loaded < num_models:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            create_models(executor, root_node, client_factory, state_file)
        print('Created all models')
        if tree:
            print(render_tree(root_node))


if __name__ == '__main__':
    main()
