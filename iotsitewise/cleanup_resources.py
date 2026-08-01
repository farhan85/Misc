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


def wait_for_computation_model_deleted(sw_client, comp_model_id):
    wait_for_resource_deleted(f'ComputationalModel {comp_model_id}',
        lambda: sw_client.describe_computation_model(computationModelId=comp_model_id)['computationModelStatus'])


def wait_for_workspace_deleted(sw_client, workspace_name):
    wait_for_resource_deleted(f'Workspace {workspace_name}',
        lambda: sw_client.describe_workspace(workspaceName=workspace_name)['workspaceStatus'])


def wait_for_dataset_deleted(sw_client, dataset_id, workspace_name=None):
    params = {'datasetId': dataset_id}
    if workspace_name is not None:
        params['workspaceName'] = workspace_name
    wait_for_resource_deleted(f'Dataset {dataset_id}',
        lambda: sw_client.describe_dataset(**params)['datasetStatus'])


def paginate_list(list_func, output_key, return_val_func, params=None):
    params = params or {}
    while True:
        response = list_func(**params)
        for resource in response[output_key]:
            yield return_val_func(resource)
        if 'nextToken' not in response:
            break
        params['nextToken'] = response['nextToken']


def all_asset_models(sw_client):
    paginator = sw_client.get_paginator('list_asset_models')
    for response in paginator.paginate():
        for asset_model in response['assetModelSummaries']:
            yield sw_client.describe_asset_model(assetModelId=asset_model['id'])


def asset_ids(sw_client, asset_model_id):
    paginator = sw_client.get_paginator('list_assets')
    for response in paginator.paginate(assetModelId=asset_model_id):
        for asset in response['assetSummaries']:
            yield asset['id']


def list_associated_assets(sw_client, asset_id, hierarchy_ids):
    paginator = sw_client.get_paginator('list_associated_assets')
    for hierarchy_id in hierarchy_ids:
        for response in paginator.paginate(assetId=asset_id, hierarchyId=hierarchy_id):
            for child_asset in response['assetSummaries']:
                yield {'assetId': asset_id,
                       'childAssetId': child_asset['id'],
                       'hierarchyId': hierarchy_id}


def gateway_ids(sw_client):
    paginator = sw_client.get_paginator('list_gateways')
    for response in paginator.paginate():
        for gateway in response['gatewaySummaries']:
            yield gateway['gatewayId']


def portal_ids(sw_client):
    paginator = sw_client.get_paginator('list_portals')
    for response in paginator.paginate():
        for portal in response['portalSummaries']:
            yield portal['id']


def project_ids(sw_client, portal_id):
    paginator = sw_client.get_paginator('list_projects')
    for response in paginator.paginate(portalId=portal_id):
        for project in response['projectSummaries']:
            yield project['id']


def dashboard_ids(sw_client, project_id):
    paginator = sw_client.get_paginator('list_dashboards')
    for response in paginator.paginate(projectId=project_id):
        for dashboard in response['dashboardSummaries']:
            yield dashboard['id']


def access_policy_ids(sw_client, resource_id, resource_type):
    paginator = sw_client.get_paginator('list_access_policies')
    for response in paginator.paginate(resourceId=resource_id, resourceType=resource_type):
        for policy in response['accessPolicySummaries']:
            yield policy['id']


def computation_model_ids(sw_client):
    paginator = sw_client.get_paginator('list_computation_models')
    for response in paginator.paginate():
        for computation_model in response['computationModelSummaries']:
            yield computation_model['id']


def workspace_names(sw_client):
    paginator = sw_client.get_paginator('list_workspaces')
    for response in paginator.paginate():
        for workspace in response['workspaceSummaries']:
            yield workspace['name']


def dataset_ids(sw_client, source_type, workspace_name=None):
    params = { 'sourceType': source_type }
    if workspace_name is not None:
        params['workspaceName'] = workspace_name
    paginator = sw_client.get_paginator('list_datasets')
    for response in paginator.paginate(**params):
        for dataset in response['datasetSummaries']:
            yield dataset['id']


def time_series_aliases(sw_client):
    paginator = sw_client.get_paginator('list_time_series')
    for response in paginator.paginate():
        for time_series in response['TimeSeriesSummaries']:
            yield time_series['alias']


def topological_sort(asset_models):
    asset_model_id_map = dict((am['assetModelId'], am) for am in asset_models)

    adjacency_graph = {}
    for am in asset_models:
        am_id = am['assetModelId']
        adjacency_graph.setdefault(am_id, set())
        # Parent models must be deleted before child models
        for child_id in (h['childAssetModelId'] for h in am['assetModelHierarchies']):
            adjacency_graph.setdefault(child_id, set()).add(am_id)
        # Asset models must be deleted before interfaces
        for int_id in (i['id'] for i in am.get('interfaceDetails', [])):
            adjacency_graph.setdefault(int_id, set()).add(am_id)

    # Apply Kahn's algorithm to construct the topological sort
    while adjacency_graph:
        next_batch = set(am_id for am_id, parent_ids in adjacency_graph.items() if len(parent_ids) == 0)
        yield [asset_model_id_map[am_id] for am_id in next_batch]
        for am_id in next_batch:
            # Remove the processed parent IDs from the graph
            del adjacency_graph[am_id]
        for parent_ids in adjacency_graph.values():
            # Remove the processed parent IDs from the current parent IDs set
            parent_ids.difference_update(next_batch)


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
        sw_client.get_waiter('asset_not_exists').wait(assetId=asset_id)
        print('done')


def delete_asset_model(sw_client, asset_model_id):
    print(f'Deleting AssetModel {asset_model_id}...', end='', flush=True)
    sw_client.delete_asset_model(assetModelId=asset_model_id)
    sw_client.get_waiter('asset_model_not_exists').wait(assetModelId=asset_model_id)
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
    sw_client.get_waiter('portal_not_exists').wait(portalId=portal_id)
    print('done')


def delete_gateways(sw_client):
    for gateway_id in gateway_ids(sw_client):
        sw_client.delete_gateway(gatewayId=gateway_id)
        print(f'Deleted gateway: {gateway_id}')


def delete_portals(sw_client):
    for portal_id in list(portal_ids(sw_client)):
        delete_portal(sw_client, portal_id)


def delete_computation_models(sw_client):
    for comp_model_id in computation_model_ids(sw_client):
        print(f'Deleting ComputationModel {comp_model_id}...', end='', flush=True)
        sw_client.delete_computation_model(computationModelId=comp_model_id)
        wait_for_computation_model_deleted(sw_client, comp_model_id)
        print('done')


def delete_workspaces(sw_client):
    for workspace_name in workspace_names(sw_client):
        for dataset_id in dataset_ids(sw_client, 'SITEWISE', workspace_name):
            print(f'Deleting Dataset {dataset_id}...', end='', flush=True)
            sw_client.delete_dataset(datasetId=dataset_id, workspaceName=workspace_name)
            wait_for_dataset_deleted(sw_client, dataset_id, workspace_name)
            print('done')

        print(f'Deleting Workspace {workspace_name}...', end='', flush=True)
        sw_client.delete_workspace(workspaceName=workspace_name)
        wait_for_workspace_deleted(sw_client, workspace_name)
        print('done')


def delete_kendra_datasets(sw_client):
    for dataset_id in dataset_ids(sw_client, 'KENDRA'):
        print(f'Deleting Dataset {dataset_id}...', end='', flush=True)
        sw_client.delete_dataset(datasetId=dataset_id)
        wait_for_dataset_deleted(sw_client, dataset_id)
        print('done')


def delete_models_and_assets(sw_client):
    asset_models = list(all_asset_models(sw_client))
    for asset_model_batch in topological_sort(asset_models):
        for asset_model in asset_model_batch:
            delete_asset_model_assets(sw_client, asset_model)
            delete_asset_model(sw_client, asset_model['assetModelId'])


def delete_timeseries(sw_client):
    for time_series_alias in time_series_aliases(sw_client):
        sw_client.delete_time_series(alias=time_series_alias)
        print(f"Deleted TimeSeries '{time_series_alias}'")


if __name__ == '__main__':
    sw_client = boto3.client('iotsitewise')

    delete_gateways(sw_client)
    delete_portals(sw_client)
    delete_computation_models(sw_client)
    delete_workspaces(sw_client)
    delete_kendra_datasets(sw_client)
    delete_models_and_assets(sw_client)
    delete_timeseries(sw_client)
