import json
from uuid import uuid4

import allure
import pytest

from base.snipeit_client import SnipeItClient
from common.snipeit_database import SnipeItDatabase
from conf.snipeit_settings import SnipeItSettings
from testcase.snipeit.helpers import build_user_payload, find_status_id


class SnipeItResourceFactory:
    """Create API test data and remove it in reverse dependency order."""

    def __init__(self, client):
        self.client = client
        self.created = []

    def create(self, endpoint, data):
        response = self.client.post(endpoint, json=data)
        assert response.status_code == 200

        body = response.json()
        assert body['status'] == 'success', body
        resource = body['payload']
        assert resource['id']
        self.created.append((endpoint, resource['id']))
        return resource

    def track(self, endpoint, resource_id):
        resource = (endpoint, resource_id)
        if resource not in self.created:
            self.created.append(resource)

    def delete(self, endpoint, resource_id):
        response = self.client.delete(f'{endpoint}/{resource_id}')
        assert response.status_code == 200
        body = response.json()
        assert body['status'] == 'success', body
        resource = (endpoint, resource_id)
        if resource in self.created:
            self.created.remove(resource)
        return body

    def cleanup(self):
        errors = []
        for endpoint, resource_id in reversed(self.created):
            response = self.client.delete(f'{endpoint}/{resource_id}')
            try:
                body = response.json()
            except ValueError:
                body = {'response': response.text}
            if response.status_code != 200 or body.get('status') != 'success':
                errors.append({
                    'endpoint': endpoint,
                    'id': resource_id,
                    'http_status': response.status_code,
                    'body': body,
                })

        allure.attach(
            json.dumps(
                {'created': self.created, 'cleanup_errors': errors},
                ensure_ascii=False,
                indent=2,
            ),
            name='测试数据清理结果',
            attachment_type=allure.attachment_type.JSON,
        )
        assert not errors, f'Failed to clean Snipe-IT test data: {errors}'


class AssetFlowContext:
    """Shared asset lifecycle data and operations for API and Web tests."""

    def __init__(self, client, factory, unique_name):
        self.client = client
        self.factory = factory
        self.unique_name = unique_name
        self.assigned_asset_ids = set()

        self.user = factory.create(
            'users',
            build_user_payload(unique_name),
        )
        self.category = factory.create('categories', {
            'name': unique_name('category'),
            'category_type': 'asset',
        })
        self.manufacturer = factory.create('manufacturers', {
            'name': unique_name('manufacturer'),
        })
        self.location = factory.create('locations', {
            'name': unique_name('location'),
        })
        self.model = factory.create('models', {
            'name': unique_name('model'),
            'model_number': unique_name('model_number'),
            'category_id': self.category['id'],
            'manufacturer_id': self.manufacturer['id'],
        })
        self.ready_status_id = find_status_id(client, 'deployable')
        self.pending_status_id = find_status_id(client, 'pending')

    def create_asset(self, status_id=None):
        request_body = {
            'asset_tag': self.unique_name('asset'),
            'name': 'Automation Flow Laptop',
            'serial': self.unique_name('serial'),
            'model_id': self.model['id'],
            'status_id': status_id or self.ready_status_id,
            'rtd_location_id': self.location['id'],
        }
        asset = self.factory.create('hardware', request_body)
        return asset, request_body

    def checkout(self, asset_id, user_id=None):
        response = self.client.post(f'hardware/{asset_id}/checkout', json={
            'checkout_to_type': 'user',
            'assigned_user': user_id or self.user['id'],
            'note': 'Checked out by the automation suite',
        })
        body = response.json()
        if response.status_code == 200 and body.get('status') == 'success':
            self.assigned_asset_ids.add(asset_id)
        return response

    def checkin(self, asset_id):
        response = self.client.post(f'hardware/{asset_id}/checkin', json={
            'note': 'Checked in by the automation suite',
        })
        body = response.json()
        if response.status_code == 200 and body.get('status') == 'success':
            self.assigned_asset_ids.discard(asset_id)
        return response

    def cleanup_assignments(self):
        for asset_id in list(self.assigned_asset_ids):
            self.checkin(asset_id)


@pytest.fixture(scope='session')
def system_login():
    """Override the legacy mock-server login for Snipe-IT tests."""
    yield


@pytest.fixture(scope='session')
def snipeit_settings():
    return SnipeItSettings.load()


@pytest.fixture
def snipeit_client(snipeit_settings):
    client = SnipeItClient(snipeit_settings)
    yield client
    client.close()


@pytest.fixture
def anonymous_snipeit_client(snipeit_settings):
    client = SnipeItClient(snipeit_settings, token=None)
    yield client
    client.close()


@pytest.fixture
def unique_name():
    def build(label):
        return f'autotest_{label}_{uuid4().hex[:10]}'

    return build


@pytest.fixture
def snipeit_resource_factory(snipeit_client):
    factory = SnipeItResourceFactory(snipeit_client)
    yield factory
    factory.cleanup()


@pytest.fixture
def asset_flow_context(snipeit_client, snipeit_resource_factory, unique_name):
    context = AssetFlowContext(
        snipeit_client,
        snipeit_resource_factory,
        unique_name,
    )
    yield context
    context.cleanup_assignments()


@pytest.fixture
def snipeit_db(snipeit_settings):
    return SnipeItDatabase(snipeit_settings)
