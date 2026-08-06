import allure
import pytest

from testcase.snipeit.helpers import build_user_payload, find_status_id


pytestmark = [pytest.mark.snipeit, pytest.mark.api]


class AssetFlowContext:
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


@pytest.fixture
def asset_flow_context(snipeit_client, snipeit_resource_factory, unique_name):
    context = AssetFlowContext(
        snipeit_client,
        snipeit_resource_factory,
        unique_name,
    )
    yield context
    context.cleanup_assignments()


@allure.feature('资产领用、归还与数据一致性')
class TestAssetFlows:

    @pytest.mark.smoke
    @allure.title('FLOW-001 将可领用设备分配给用户')
    def test_checkout_asset_to_user(self, asset_flow_context):
        context = asset_flow_context
        asset, _ = context.create_asset()

        response = context.checkout(asset['id'])

        assert response.status_code == 200
        assert response.json()['status'] == 'success'
        actual = context.client.get(f"hardware/{asset['id']}").json()
        assert actual['assigned_to']['id'] == context.user['id']
        assert actual['assigned_to']['type'] == 'user'

    @pytest.mark.regression
    @allure.title('FLOW-002 拒绝重复领用同一设备')
    def test_duplicate_checkout_is_rejected(self, asset_flow_context):
        context = asset_flow_context
        asset, _ = context.create_asset()
        first = context.checkout(asset['id'])
        assert first.json()['status'] == 'success'

        second = context.checkout(asset['id'])

        assert second.status_code == 200
        assert second.json()['status'] == 'error'
        actual = context.client.get(f"hardware/{asset['id']}").json()
        assert actual['assigned_to']['id'] == context.user['id']

    @pytest.mark.regression
    @allure.title('FLOW-003 Pending 状态设备禁止领用')
    def test_pending_asset_cannot_be_checked_out(self, asset_flow_context):
        context = asset_flow_context
        asset, _ = context.create_asset(context.pending_status_id)

        response = context.checkout(asset['id'])

        assert response.status_code == 200
        assert response.json()['status'] == 'error'
        actual = context.client.get(f"hardware/{asset['id']}").json()
        assert actual['assigned_to'] is None

    @pytest.mark.regression
    @allure.title('FLOW-004 不存在的用户不能领用设备')
    def test_checkout_to_unknown_user_is_rejected(self, asset_flow_context):
        context = asset_flow_context
        asset, _ = context.create_asset()

        response = context.checkout(asset['id'], user_id=999999999)

        assert response.status_code == 200
        assert response.json()['status'] == 'error'
        actual = context.client.get(f"hardware/{asset['id']}").json()
        assert actual['assigned_to'] is None

    @pytest.mark.smoke
    @allure.title('FLOW-005 查询用户已领用的资产')
    def test_query_assets_assigned_to_user(self, asset_flow_context):
        context = asset_flow_context
        asset, expected = context.create_asset()
        assert context.checkout(asset['id']).json()['status'] == 'success'

        response = context.client.get(f"users/{context.user['id']}/assets")

        assert response.status_code == 200
        matches = [
            row for row in response.json()['rows']
            if row['asset_tag'] == expected['asset_tag']
        ]
        assert len(matches) == 1
        assert matches[0]['id'] == asset['id']

    @pytest.mark.smoke
    @allure.title('FLOW-006 正常归还已领用设备')
    def test_checkin_asset(self, asset_flow_context):
        context = asset_flow_context
        asset, _ = context.create_asset()
        assert context.checkout(asset['id']).json()['status'] == 'success'

        response = context.checkin(asset['id'])

        assert response.status_code == 200
        assert response.json()['status'] == 'success'
        actual = context.client.get(f"hardware/{asset['id']}").json()
        assert actual['assigned_to'] is None
        assert actual['status_label']['id'] == context.ready_status_id

    @pytest.mark.regression
    @allure.title('FLOW-007 拒绝重复归还同一设备')
    def test_duplicate_checkin_is_rejected(self, asset_flow_context):
        context = asset_flow_context
        asset, _ = context.create_asset()
        assert context.checkout(asset['id']).json()['status'] == 'success'
        first = context.checkin(asset['id'])
        assert first.json()['status'] == 'success'

        second = context.checkin(asset['id'])

        assert second.status_code == 200
        assert second.json()['status'] == 'error'
        actual = context.client.get(f"hardware/{asset['id']}").json()
        assert actual['assigned_to'] is None

    @pytest.mark.regression
    @allure.title('FLOW-008 操作历史包含领用和归还记录')
    def test_asset_history(self, asset_flow_context):
        context = asset_flow_context
        asset, _ = context.create_asset()
        assert context.checkout(asset['id']).json()['status'] == 'success'
        assert context.checkin(asset['id']).json()['status'] == 'success'

        response = context.client.get(f"hardware/{asset['id']}/history")

        assert response.status_code == 200
        action_types = {row['action_type'] for row in response.json()['rows']}
        assert 'checkout' in action_types
        assert 'checkin from' in action_types

    @pytest.mark.smoke
    @allure.title('FLOW-009 MySQL 资产领用状态与 API 一致')
    def test_mysql_assignment_state(self, asset_flow_context, snipeit_db):
        context = asset_flow_context
        asset, expected = context.create_asset()
        assert context.checkout(asset['id']).json()['status'] == 'success'

        api_asset = context.client.get(f"hardware/{asset['id']}").json()
        db_asset = snipeit_db.query_one(
            'SELECT id, asset_tag, assigned_to, assigned_type, status_id, '
            'checkout_counter, deleted_at FROM assets WHERE id = %s',
            (asset['id'],),
        )

        assert db_asset['asset_tag'] == expected['asset_tag']
        assert db_asset['assigned_to'] == context.user['id']
        assert db_asset['assigned_type'] == 'App\\Models\\User'
        assert db_asset['status_id'] == context.ready_status_id
        assert db_asset['checkout_counter'] == 1
        assert db_asset['deleted_at'] is None
        assert api_asset['assigned_to']['id'] == db_asset['assigned_to']

    @pytest.mark.regression
    @allure.title('FLOW-010 MySQL 包含完整的领用和归还审计日志')
    def test_mysql_checkout_and_checkin_logs(self, asset_flow_context, snipeit_db):
        context = asset_flow_context
        asset, _ = context.create_asset()
        assert context.checkout(asset['id']).json()['status'] == 'success'
        assert context.checkin(asset['id']).json()['status'] == 'success'

        logs = snipeit_db.query_all(
            'SELECT action_type, item_type, item_id, target_type, target_id '
            'FROM action_logs WHERE item_type = %s AND item_id = %s '
            'ORDER BY id',
            ('App\\Models\\Asset', asset['id']),
        )
        action_types = [row['action_type'] for row in logs]

        assert 'checkout' in action_types
        assert 'checkin from' in action_types
        checkout = next(row for row in logs if row['action_type'] == 'checkout')
        assert checkout['target_type'] == 'App\\Models\\User'
        assert checkout['target_id'] == context.user['id']
