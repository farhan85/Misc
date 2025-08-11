#!/usr/bin/env python3

import os
import time

import boto3
import botocore


def wait_for_resource_deleted(resource_str, get_resource_status):
    for _ in range(0, 30):
        try:
            status = get_resource_status()
            time.sleep(1)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return
    raise Exception(f'Failed to delete {resource_str}. Final status: {status}')


def wait_for_asset_model_deleted(sw_client, asset_model_id):
    wait_for_resource_deleted(f'AssetModel {asset_model_id}',
        lambda: sw_client.describe_asset_model(assetModelId=asset_model_id)['assetModelStatus'])


def wait_for_asset_deleted(sw_client, asset_id):
    wait_for_resource_deleted(f'Asset {asset_id}',
        lambda: sw_client.describe_asset(assetId=asset_id)['assetStatus'])


def wait_for_portal_deleted(sw_client, portal_id):
    wait_for_resource_deleted(f'Portal {portal_id}',
        lambda: sw_client.describe_portal(portalId=portal_id)['portalStatus'])


def paginate_list(list_func, output_key, return_val_func, params):
    params = params or {}
    while True:
        response = list_func(**params)
        for resource in response[output_key]:
            yield return_val_func(resource)
        if 'nextToken' not in response:
            break
        params['nextToken'] = response['nextToken']


def all_asset_models(sw_client):
    return paginate_list(
        sw_client.list_asset_models,
        'assetModelSummaries',
        lambda model: sw_client.describe_asset_model(assetModelId=model['id']))


def asset_ids(sw_client, asset_model_id):
    return paginate_list(
        sw_client.list_assets,
        'assetSummaries',
        lambda asset: asset['id'],
        {'assetModelId': asset_model_id})


def list_associated_assets_for_parent(sw_client, parent_asset_id, hierarchy_id):
    return paginate_list(
        sw_client.list_associated_assets,
        'assetSummaries',
        lambda child_asset: {'assetId': parent_asset_id,
                             'childAssetId': child_asset['id'],
                             'hierarchyId': hierarchy_id},
        {'assetId': parent_asset_id, 'hierarchyId': hierarchy_id})


def list_associated_assets(sw_client, asset_id, hierarchy_ids):
    for hierarchy_id in hierarchy_ids:
        for association in list_associated_assets_for_parent(sw_client, asset_id, hierarchy_id):
            yield association


def portal_ids(sw_client):
    return paginate_list(
        sw_client.list_portals,
        'portalSummaries',
        lambda portal: portal['id'])


def project_ids(sw_client, portal_id):
    return paginate_list(
        sw_client.list_projects,
        'projectSummaries',
        lambda project: project['id'],
        {'portalId': portal_id})


def dashboard_ids(sw_client, project_id):
    return paginate_list(
        sw_client.list_dashboards,
        'dashboardSummaries',
        lambda dashboard: dashboard['id'],
        {'projectId': project_id})


def access_policy_ids(sw_client, resource_id, resource_type):
    return paginate_list(
        sw_client.list_access_policies,
        'accessPolicySummaries',
        lambda policy: policy['id'],
        {'resourceId': resource_id, 'resourceType': resource_type})


def time_series_aliases(sw_client):
    return paginate_list(
        sw_client.list_time_series,
        'TimeSeriesSummaries',
        lambda time_series: time_series['alias'])


def topological_sort(asset_models):
    # Implemented using Kahn's algorithm
    asset_model_id_map = dict((am['assetModelId'], am) for am in asset_models)

    adjancy_graph = {}
    for am in asset_models:
        am_id = am['assetModelId']
        adjancy_graph.setdefault(am_id, set())
        # Parent models must be deleted before child models
        for child_id in (h['childAssetModelId'] for h in am['assetModelHierarchies']):
            adjancy_graph.setdefault(child_id, set()).add(am_id)
        # Asset models must be deleted before interfaces
        for int_id in (i['id'] for i in am.get('interfaceDetails', [])):
            adjancy_graph.setdefault(int_id, set()).add(am_id)

    while adjancy_graph:
        next_batch = set(am_id for am_id, child_ids in adjancy_graph.items() if len(child_ids) == 0)
        yield next_batch
        for am_id in next_batch:
            del adjancy_graph[am_id]
        for child_ids in adjancy_graph.values():
            # Remove the next_batch nodes from the in-node list
            child_ids.difference_update(next_batch)


def delete_asset_model_assets(sw_client, asset_model):
    asset_model_id = asset_model['assetModelId']
    hierarchy_ids = [h['id'] for h in asset_model['assetModelHierarchies']]
    for asset_id in asset_ids(sw_client, asset_model_id):
        for association in list_associated_assets(sw_client, asset_id, hierarchy_ids):
            sw_client.disassociate_assets(assetId=asset_id,
                                          hierarchyId=association['hierarchyId'],
                                          childAssetId=association['childAssetId'])
            print(f'Removed association: {association}')

        print(f'Deleting Asset {asset_id}...', end='', flush=True)
        sw_client.delete_asset(assetId=asset_id)
        wait_for_asset_deleted(sw_client, asset_id)
        print('done')


def delete_asset_model(sw_client, asset_model_id):
    print(f'Deleting AssetModel {asset_model_id}...', end='', flush=True)
    sw_client.delete_asset_model(assetModelId=asset_model_id)
    wait_for_asset_model_deleted(sw_client, asset_model_id)
    print('done')


def delete_access_policies(sw_client, resource_id, resource_type):
    for access_policy_id in access_policy_ids(sw_client, resource_id, resource_type):
        sw_client.delete_access_policy(accessPolicyId=access_policy_id)
        print(f'Deleted {resource_type.capitalize()} AccessPolicy {access_policy_id}')


def delete_portal(sw_client, portal_id):
    for project_id in project_ids(sw_client, portal_id):
        for dashboard_id in dashboard_ids(sw_client, project_id):
            sw_client.delete_dashboard(dashboardId=dashboard_id)
            print(f'Deleted Dashboard {dashboard_id}')

        delete_access_policies(sw_client, project_id, 'PROJECT')
        sw_client.delete_project(projectId=project_id)
        print(f'Deleted Project {project_id}')

    delete_access_policies(sw_client, portal_id, 'PORTAL')
    print(f'Deleting Portal {portal_id}...', end='', flush=True)
    sw_client.delete_portal(portalId=portal_id)
    wait_for_portal_deleted(sw_client, portal_id)
    print('done')


def delete_sitewise_resources(sw_client):
    for portal_id in list(portal_ids(sw_client)):
        delete_portal(sw_client, portal_id)
    asset_models = list(all_asset_models(sw_client))
    delete_order = reversed(topological_sort(asset_models))
    for asset_model_batch in delete_order:
        for asset_model in asset_model_batch:
            delete_asset_model_assets(sw_client, asset_model)
            delete_asset_model(sw_client, asset_model['assetModelId'])
    for time_series_alias in time_series_aliases(sw_client):
        sw_client.delete_time_series(time_series_alias)
        print(f"Deleted TimeSeries '{time_series_alias}'")


if __name__ == '__main__':
    sw_client = boto3.client('iotsitewise')
    delete_sitewise_resources(sw_client)
