import json
from uuid import uuid4

import allure
import pytest

from base.snipeit_client import SnipeItClient
from conf.snipeit_settings import SnipeItSettings


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
            name='Test data cleanup',
            attachment_type=allure.attachment_type.JSON,
        )
        assert not errors, f'Failed to clean Snipe-IT test data: {errors}'


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
