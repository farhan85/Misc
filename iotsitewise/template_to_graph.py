#!/usr/bin/env python3

import click
import json
import graphviz


class CloudFormationParser:
    def __init__(self, cfn_defn):
        self._models = [(res_id, res['Properties'])
                        for res_id, res in cfn_defn['Resources'].items()
                        if res['Type'] == 'AWS::IoTSiteWise::AssetModel']
        self._assets = [(res_id, res['Properties'])
                        for res_id, res in cfn_defn['Resources'].items()
                        if res['Type'] == 'AWS::IoTSiteWise::Asset']

    def models(self):
        return ((m_id, m['AssetModelName'])
                for m_id, m in self._models)

    def model_hierarchies(self):
        return ((m_id, h['ChildAssetModelId']['Ref'])
                for m_id, m in self._models
                for h in m['AssetModelHierarchies'])

    def assets(self):
        return ((a_id, a['AssetName'])
                for a_id, a in self._assets)

    def asset_associations(self):
        return ((a_id, h['ChildAssetId']['Ref'])
                for a_id, a in self._assets
                for h in a['AssetHierarchies'])


class BulkExportParser:
    def __init__(self, bulk_export_defn):
        self.resources = bulk_export_defn

    def models(self):
        return ((m['assetModelId'], m['assetModelName'])
                for m in self.resources['assetModels'])

    def model_hierarchies(self):
        return ((m['assetModelId'], h['childAssetModelId'])
                for m in self.resources['assetModels']
                for h in m['assetModelHierarchies'])

    def assets(self):
        return ((a['assetId'], a['assetName'])
                for a in self.resources['assets'])

    def asset_associations(self):
        return ((a['assetId'], h['childAssetId'])
                for a in self.resources['assets']
                for h in a['assetHierarchies'])


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-c', '--cfn-file', type=click.File('r'), help='CloudFormation template file (json)')
@click.option('-b', '--bulk-export-file', type=click.File('r'), help='SiteWise BulkExport file')
@click.option('-n', '--name', required=True, help='Identifying name for graphs')
@click.option('-d', '--dot', is_flag=True, help='Generate dot files (instead of png files)')
def main(cfn_file, bulk_export_file, name, dot):
    if cfn_file:
        contents = cfn_file.read()
        resources = CloudFormationParser(json.loads(contents))
    elif bulk_export_file:
        contents = bulk_export_file.read()
        resources = BulkExportParser(json.loads(contents))
    else:
        raise click.UsageError('Must provide either a CloudFormation or BulkExport file')

    model_graph = graphviz.Graph(f'{name}_model_graph')
    asset_graph = graphviz.Graph(f'{name}_asset_graph')

    for model_id, model_name in resources.models():
        model_graph.node(model_id, model_name)
    for asset_id, asset_name in resources.assets():
        asset_graph.node(asset_id, asset_name)
    model_graph.edges(resources.model_hierarchies())
    asset_graph.edges(resources.asset_associations())

    format = 'dot' if dot else 'png'
    model_graph.render(directory='.', format=format, cleanup=True)
    asset_graph.render(directory='.', format=format, cleanup=True)


if __name__ == '__main__':
    main()
