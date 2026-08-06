import allure
import pytest

from base.snipeit_client import SnipeItClient


pytestmark = [pytest.mark.snipeit, pytest.mark.api]


@allure.feature('Snipe-IT API authentication')
class TestAuthentication:

    @pytest.mark.smoke
    @allure.title('AUTH-001 Valid token returns the current administrator')
    def test_valid_token_returns_current_user(self, snipeit_client, snipeit_settings):
        response = snipeit_client.get('users/me')

        assert response.status_code == 200
        body = response.json()
        assert body['username'] == snipeit_settings.admin_username
        assert body['email'] == snipeit_settings.admin_email
        assert body['activated'] is True

    @pytest.mark.smoke
    @allure.title('AUTH-002 Missing token is rejected')
    def test_missing_token_is_rejected(self, anonymous_snipeit_client):
        response = anonymous_snipeit_client.get('users', params={'limit': 1})

        assert response.status_code == 401
        assert response.headers['Content-Type'].startswith('application/json')

    @pytest.mark.regression
    @allure.title('AUTH-003 Invalid token is rejected')
    def test_invalid_token_is_rejected(self, snipeit_settings):
        client = SnipeItClient(snipeit_settings, token='invalid-test-token')
        try:
            response = client.get('users', params={'limit': 1})
        finally:
            client.close()

        assert response.status_code == 401
        assert response.headers['Content-Type'].startswith('application/json')
