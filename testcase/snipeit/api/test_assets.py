import allure
import pytest

from testcase.snipeit.helpers import find_status_id


pytestmark = [pytest.mark.snipeit, pytest.mark.api]


def track_unexpected_success(factory, endpoint, body):
    payload = body.get('payload') or {}
    if body.get('status') == 'success' and payload.get('id'):
        factory.track(endpoint, payload['id'])


@pytest.fixture
def asset_dependencies(
        snipeit_client,
        snipeit_resource_factory,
        unique_name,
):
    category = snipeit_resource_factory.create('categories', {
        'name': unique_name('category'),
        'category_type': 'asset',
    })
    manufacturer = snipeit_resource_factory.create('manufacturers', {
        'name': unique_name('manufacturer'),
    })
    location = snipeit_resource_factory.create('locations', {
        'name': unique_name('location'),
    })
    model = snipeit_resource_factory.create('models', {
        'name': unique_name('model'),
        'model_number': unique_name('model_number'),
        'category_id': category['id'],
        'manufacturer_id': manufacturer['id'],
    })
    return {
        'category': category,
        'manufacturer': manufacturer,
        'location': location,
        'model': model,
        'ready_status_id': find_status_id(snipeit_client, 'deployable'),
    }


@pytest.fixture
def create_asset(asset_dependencies, snipeit_resource_factory, unique_name):
    def create(**overrides):
        request_body = {
            'asset_tag': unique_name('asset'),
            'name': 'Automation Test Laptop',
            'serial': unique_name('serial'),
            'model_id': asset_dependencies['model']['id'],
            'status_id': asset_dependencies['ready_status_id'],
            'rtd_location_id': asset_dependencies['location']['id'],
            'notes': 'Created by the Snipe-IT automation suite',
        }
        request_body.update(overrides)
        resource = snipeit_resource_factory.create('hardware', request_body)
        return resource, request_body

    return create


@allure.feature('硬件资产管理')
class TestAssetManagement:

    @pytest.mark.smoke
    @allure.title('ASSET-002 创建可领用状态的硬件资产')
    def test_create_deployable_asset(self, create_asset, snipeit_client):
        asset, expected = create_asset()

        response = snipeit_client.get(f"hardware/{asset['id']}")
        assert response.status_code == 200
        actual = response.json()
        assert actual['asset_tag'] == expected['asset_tag']
        assert actual['serial'] == expected['serial']
        assert actual['model']['id'] == expected['model_id']
        assert actual['status_label']['id'] == expected['status_id']

    @pytest.mark.regression
    @pytest.mark.parametrize(
        ('missing_field', 'expected_error'),
        [
            ('model_id', 'model_id'),
            ('status_id', 'status_id'),
        ],
        ids=['缺少资产型号', '缺少资产状态'],
    )
    @allure.title('ASSET-003 缺少型号或状态时拒绝创建资产')
    def test_create_asset_missing_required_relation(
            self,
            missing_field,
            expected_error,
            asset_dependencies,
            snipeit_client,
            snipeit_resource_factory,
            unique_name,
    ):
        request_body = {
            'asset_tag': unique_name('asset'),
            'model_id': asset_dependencies['model']['id'],
            'status_id': asset_dependencies['ready_status_id'],
        }
        request_body.pop(missing_field)

        response = snipeit_client.post('hardware', json=request_body)
        assert response.status_code == 200
        body = response.json()
        track_unexpected_success(snipeit_resource_factory, 'hardware', body)

        assert body['status'] == 'error', body
        assert expected_error in body['messages'], body

    @pytest.mark.regression
    @pytest.mark.parametrize(
        ('invalid_field', 'expected_error'),
        [
            ('model_id', 'model_id'),
            ('status_id', 'status_id'),
        ],
        ids=['型号不存在', '状态不存在'],
    )
    @allure.title('ASSET-004 型号或状态不存在时拒绝创建资产')
    def test_create_asset_with_unknown_relation(
            self,
            invalid_field,
            expected_error,
            asset_dependencies,
            snipeit_client,
            snipeit_resource_factory,
            unique_name,
    ):
        request_body = {
            'asset_tag': unique_name('asset'),
            'model_id': asset_dependencies['model']['id'],
            'status_id': asset_dependencies['ready_status_id'],
        }
        request_body[invalid_field] = 999999999

        response = snipeit_client.post('hardware', json=request_body)
        assert response.status_code == 200
        body = response.json()
        track_unexpected_success(snipeit_resource_factory, 'hardware', body)

        assert body['status'] == 'error', body
        assert expected_error in body['messages'], body

    @pytest.mark.regression
    @allure.title('ASSET-005 重复资产标签时拒绝创建资产')
    def test_duplicate_asset_tag_is_rejected(
            self,
            create_asset,
            asset_dependencies,
            snipeit_client,
            snipeit_resource_factory,
            unique_name,
    ):
        original, original_request = create_asset()
        duplicate_request = {
            'asset_tag': original_request['asset_tag'],
            'serial': unique_name('serial'),
            'model_id': asset_dependencies['model']['id'],
            'status_id': asset_dependencies['ready_status_id'],
        }

        response = snipeit_client.post('hardware', json=duplicate_request)
        assert response.status_code == 200
        body = response.json()
        track_unexpected_success(snipeit_resource_factory, 'hardware', body)

        assert body['status'] == 'error', body
        assert 'asset_tag' in body['messages'], body

        result = snipeit_client.get(
            'hardware',
            params={'search': original_request['asset_tag'], 'limit': 100},
        ).json()
        exact_matches = [
            row for row in result['rows']
            if row['asset_tag'] == original_request['asset_tag']
        ]
        assert len(exact_matches) == 1
        assert exact_matches[0]['id'] == original['id']

    @pytest.mark.smoke
    @allure.title('ASSET-006 按资产 ID 查询设备详情')
    def test_get_asset_by_id(self, create_asset, snipeit_client):
        asset, expected = create_asset()

        response = snipeit_client.get(f"hardware/{asset['id']}")

        assert response.status_code == 200
        actual = response.json()
        assert actual['id'] == asset['id']
        assert actual['asset_tag'] == expected['asset_tag']
        assert actual['name'] == expected['name']
        assert actual['notes'] == expected['notes']

    @pytest.mark.smoke
    @allure.title('ASSET-007 按唯一资产标签查询设备')
    def test_get_asset_by_tag(self, create_asset, snipeit_client):
        asset, expected = create_asset()

        response = snipeit_client.get(
            f"hardware/bytag/{expected['asset_tag']}",
        )

        assert response.status_code == 200
        actual = response.json()
        assert actual['id'] == asset['id']
        assert actual['asset_tag'] == expected['asset_tag']

    @pytest.mark.regression
    @allure.title('ASSET-008 按关键词、状态和型号组合筛选资产')
    def test_filter_assets(
            self,
            create_asset,
            asset_dependencies,
            snipeit_client,
    ):
        asset, expected = create_asset(name='Filter Target Laptop')

        response = snipeit_client.get('hardware', params={
            'search': expected['asset_tag'],
            'status_id': asset_dependencies['ready_status_id'],
            'model_id': asset_dependencies['model']['id'],
            'limit': 100,
        })

        assert response.status_code == 200
        exact_matches = [
            row for row in response.json()['rows']
            if row['asset_tag'] == expected['asset_tag']
        ]
        assert len(exact_matches) == 1
        assert exact_matches[0]['id'] == asset['id']
        assert exact_matches[0]['status_label']['id'] == expected['status_id']
        assert exact_matches[0]['model']['id'] == expected['model_id']

    @pytest.mark.regression
    @allure.title('ASSET-009 修改资产名称和备注')
    def test_update_asset(self, create_asset, snipeit_client):
        asset, _ = create_asset()
        changes = {
            'name': 'Updated Automation Laptop',
            'notes': 'Updated by ASSET-009',
        }

        response = snipeit_client.patch(
            f"hardware/{asset['id']}",
            json=changes,
        )
        assert response.status_code == 200
        assert response.json()['status'] == 'success'

        actual = snipeit_client.get(f"hardware/{asset['id']}").json()
        assert actual['name'] == changes['name']
        assert actual['notes'] == changes['notes']

    @pytest.mark.regression
    @allure.title('ASSET-010 删除未领用的硬件资产')
    def test_delete_asset(
            self,
            create_asset,
            snipeit_client,
            snipeit_resource_factory,
    ):
        asset, expected = create_asset()

        snipeit_resource_factory.delete('hardware', asset['id'])

        result = snipeit_client.get(
            'hardware',
            params={'search': expected['asset_tag'], 'limit': 100},
        ).json()
        assert all(
            row['asset_tag'] != expected['asset_tag']
            for row in result['rows']
        )
