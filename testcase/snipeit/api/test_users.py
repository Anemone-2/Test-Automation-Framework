import allure
import pytest

from testcase.snipeit.helpers import build_user_payload


pytestmark = [pytest.mark.snipeit, pytest.mark.api]


def track_unexpected_success(factory, body):
    payload = body.get('payload') or {}
    if body.get('status') == 'success' and payload.get('id'):
        factory.track('users', body['payload']['id'])


@allure.feature('用户管理')
class TestUserManagement:

    @pytest.mark.smoke
    @allure.title('USER-001 创建可领用资产的已启用用户')
    def test_create_user(self, snipeit_client, snipeit_resource_factory, unique_name):
        expected = build_user_payload(unique_name)

        user = snipeit_resource_factory.create('users', expected)
        response = snipeit_client.get(f"users/{user['id']}")

        assert response.status_code == 200
        actual = response.json()
        assert actual['username'] == expected['username']
        assert actual['first_name'] == expected['first_name']
        assert actual['last_name'] == expected['last_name']
        assert actual['email'] == expected['email']
        assert actual['activated'] is True

    @pytest.mark.regression
    @pytest.mark.parametrize(
        ('missing_fields', 'expected_error'),
        [
            (('first_name',), 'first_name'),
            (('username',), 'username'),
            (('password', 'password_confirmation'), 'password'),
        ],
        ids=['缺少姓名', '缺少用户名', '缺少密码'],
    )
    @allure.title('USER-002 缺少必填字段时拒绝创建用户')
    def test_create_user_missing_required_field(
            self,
            missing_fields,
            expected_error,
            snipeit_client,
            snipeit_resource_factory,
            unique_name,
    ):
        request_body = build_user_payload(unique_name)
        for field in missing_fields:
            request_body.pop(field)

        response = snipeit_client.post('users', json=request_body)
        assert response.status_code == 200
        body = response.json()
        track_unexpected_success(snipeit_resource_factory, body)

        assert body['status'] == 'error', body
        assert expected_error in body['messages'], body

    @pytest.mark.regression
    @allure.title('USER-003 重复用户名时拒绝创建用户')
    def test_duplicate_username_is_rejected(
            self,
            snipeit_client,
            snipeit_resource_factory,
            unique_name,
    ):
        original = build_user_payload(unique_name)
        snipeit_resource_factory.create('users', original)
        duplicate = build_user_payload(
            unique_name,
            username=original['username'],
            email=f"{unique_name('email')}@example.test",
        )

        response = snipeit_client.post('users', json=duplicate)
        assert response.status_code == 200
        body = response.json()
        track_unexpected_success(snipeit_resource_factory, body)

        assert body['status'] == 'error', body
        assert 'username' in body['messages'], body

        result = snipeit_client.get(
            'users',
            params={'search': original['username'], 'limit': 100},
        ).json()
        exact_matches = [
            row for row in result['rows']
            if row['username'] == original['username']
        ]
        assert len(exact_matches) == 1

    @pytest.mark.smoke
    @allure.title('USER-004 按用户名精确查询用户')
    def test_search_user_by_username(
            self,
            snipeit_client,
            snipeit_resource_factory,
            unique_name,
    ):
        expected = build_user_payload(unique_name)
        user = snipeit_resource_factory.create('users', expected)

        response = snipeit_client.get(
            'users',
            params={'search': expected['username'], 'limit': 100},
        )

        assert response.status_code == 200
        exact_matches = [
            row for row in response.json()['rows']
            if row['username'] == expected['username']
        ]
        assert len(exact_matches) == 1
        assert exact_matches[0]['id'] == user['id']

    @pytest.mark.regression
    @allure.title('USER-005 修改用户姓名和职位')
    def test_update_user(
            self,
            snipeit_client,
            snipeit_resource_factory,
            unique_name,
    ):
        user = snipeit_resource_factory.create(
            'users',
            build_user_payload(unique_name),
        )
        changes = {
            'first_name': 'Updated',
            'last_name': 'Engineer',
            'jobtitle': 'Senior Test Engineer',
        }

        response = snipeit_client.patch(f"users/{user['id']}", json=changes)
        assert response.status_code == 200
        assert response.json()['status'] == 'success'

        actual = snipeit_client.get(f"users/{user['id']}").json()
        assert actual['first_name'] == changes['first_name']
        assert actual['last_name'] == changes['last_name']
        assert actual['jobtitle'] == changes['jobtitle']

    @pytest.mark.regression
    @allure.title('USER-006 查询不存在的用户时返回业务错误')
    def test_unknown_user_returns_business_error(self, snipeit_client):
        response = snipeit_client.get('users/999999999')

        assert response.status_code == 200
        body = response.json()
        assert body['status'] == 'error'
        assert body['payload'] is None
        assert isinstance(body['messages'], str)
        assert body['messages'].strip()

    @pytest.mark.regression
    @allure.title('USER-007 删除未领用资产的用户')
    def test_delete_user(
            self,
            snipeit_client,
            snipeit_resource_factory,
            unique_name,
    ):
        expected = build_user_payload(unique_name)
        user = snipeit_resource_factory.create('users', expected)

        snipeit_resource_factory.delete('users', user['id'])

        detail = snipeit_client.get(f"users/{user['id']}").json()
        assert detail['status'] == 'error'
        result = snipeit_client.get(
            'users',
            params={'search': expected['username'], 'limit': 100},
        ).json()
        assert all(
            row['username'] != expected['username']
            for row in result['rows']
        )
