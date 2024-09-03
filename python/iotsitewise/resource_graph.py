#!/usr/bin/env python3

import time

import boto3
from anytree import Node, RenderTree
from anytree.render import ContStyle
from collections import namedtuple
from enum import Enum


NodeData = namedtuple('NodeData', ['id', 'name', 'type'])


class RenderOption(Enum):
    BRIEF_LABELS = 1
    DETAILED_LABELS = 2


class SiteWiseResources:
    def __init__(self):
        self.nodes = {}
        self.model_component_adjlist = []
        self.model_asset_adjlist = []
        self.model_adjlist = []
        self.asset_adjlist = []

    def _add_node(self, node_id, node_name, node_type):
        if node_id not in self.nodes:
            self.nodes[node_id] = NodeData(node_id, node_name, node_type)

    def _build_trees(self, adjlist):
        tree = {}
        for parent_id, child_id in adjlist:
            if parent_id not in tree:
                tree[parent_id] = self._create_node_obj(parent_id)
            if child_id not in tree:
                tree[child_id] = self._create_node_obj(child_id)
            tree[child_id].parent = tree[parent_id]
        return [n for n in tree.values() if n.is_root and n.children]

    def _create_node_obj(self, node_id):
        return Node(self.nodes[node_id].name, sw_id=node_id, type=self.nodes[node_id].type)

    def add_model(self, model_id, model_name):
        self._add_node(model_id, model_name, 'model')

    def add_component_model(self, comp_model_id, comp_model_name, model_id):
        self._add_node(comp_model_id, comp_model_name, 'comp_model')
        self.model_component_adjlist.append((model_id, comp_model_id))

    def add_child_model(self, model_id, child_id):
        self.model_adjlist.append((model_id, child_id))

    def add_asset(self, asset_id, asset_name, model_id):
        self._add_node(asset_id, asset_name, 'asset')
        self.model_asset_adjlist.append((model_id, asset_id))

    def add_child_asset(self, asset_id, child_id):
        self.asset_adjlist.append((asset_id, child_id))

    def build_component_model_usage_trees(self):
        return self._build_trees((c_id, m_id) for m_id, c_id in self.model_component_adjlist)

    def build_model_component_usage_trees(self):
        return self._build_trees(self.model_component_adjlist)

    def build_model_to_asset_trees(self):
        return self._build_trees(self.model_asset_adjlist)

    def build_model_hierarchy_trees(self):
        return self._build_trees(self.model_adjlist)

    def build_asset_hierarchy_trees(self):
        return self._build_trees(self.asset_adjlist)


def list_resources(list_func, output_key, params=None):
    params = params or {}
    while True:
        response = list_func(**params)
        for resource in response[output_key]:
            yield resource['id'], resource['name']
        if 'nextToken' not in response:
            break
        params['nextToken'] = response['nextToken']
        time.sleep(0.25)


def list_child_models(asset_model):
    return [h['childAssetModelId'] for h in asset_model['assetModelHierarchies']]


def list_asset_models(iotsitewise_client):
    return list_resources(iotsitewise_client.list_asset_models,
                          'assetModelSummaries')


def list_asset_model_component_models(iotsitewise_client, asset_model_id):
    return list_resources(iotsitewise_client.list_asset_model_composite_models,
                          'assetModelCompositeModelSummaries',
                          {'assetModelId': asset_model_id})


def list_assets(iotsitewise_client, asset_model_id):
    return list_resources(iotsitewise_client.list_assets,
                          'assetSummaries',
                          {'assetModelId': asset_model_id})


def list_child_assets(iotsitewise_client, parent_asset_id):
    return (child_asset_id
            for child_asset_id, _ in list_resources(iotsitewise_client.list_associated_assets,
                                                    'assetSummaries',
                                                    {'assetId': parent_asset_id}))


def print_tree(root, render_option=RenderOption.BRIEF_LABELS):
    if render_option == RenderOption.BRIEF_LABELS:
        print(RenderTree(root, style=ContStyle()).by_attr())
    else:
        print(RenderTree(root, style=ContStyle()).by_attr(lambda n: f'[{n.type}] {n.name} ({n.sw_id})'))


def main():
    iotsitewise_client = boto3.client('iotsitewise')

    resources = SiteWiseResources()
    for am_id, am_name in list_asset_models(iotsitewise_client):
        asset_model = iotsitewise_client.describe_asset_model(assetModelId=am_id)
        resources.add_model(am_id, am_name)
        for comp_model_id, comp_model_name in list_asset_model_component_models(iotsitewise_client, am_id):
            resources.add_component_model(comp_model_id, comp_model_name, am_id)
        for child_model_id in list_child_models(asset_model):
            resources.add_child_model(am_id, child_model_id)
        for a_id, a_name in list_assets(iotsitewise_client, am_id):
            resources.add_asset(a_id, a_name, am_id)
            for child_asset_id in list_child_assets(iotsitewise_client, a_id):
                resources.add_child_asset(a_id, child_asset_id)

    print('ComponentModels -> AssetModels')
    print('-----------------------------')
    for root in resources.build_component_model_usage_trees():
        print_tree(root, RenderOption.DETAILED_LABELS)
    print()

    print()
    print('AssetModels -> ComponentModels')
    print('-----------------------------')
    for root in resources.build_model_component_usage_trees():
        print_tree(root, RenderOption.DETAILED_LABELS)
    print()

    print()
    print('AssetModels -> Assets')
    print('--------------------')
    for root in resources.build_model_to_asset_trees():
        print_tree(root, RenderOption.DETAILED_LABELS)
    print()

    print()
    print('Asset Model Hierarchy Trees')
    print('---------------------------')
    for root in resources.build_model_hierarchy_trees():
        print_tree(root)
    print()

    print()
    print('Asset Hierarchy Trees')
    print('---------------------')
    for root in resources.build_asset_hierarchy_trees():
        print_tree(root)


if __name__ == '__main__':
    main()
