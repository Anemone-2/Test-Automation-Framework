import allure
import pytest

from pages.assets_page import AssetsPage
from pages.login_page import LoginPage


pytestmark = [pytest.mark.snipeit, pytest.mark.web]


@allure.feature('Snipe-IT web authentication')
class TestWebLogin:

    @pytest.mark.smoke
    @allure.title('WEB-001 Administrator can log in and open the asset list')
    def test_admin_login_opens_asset_list(
            self,
            browser_driver,
            snipeit_settings,
    ):
        with allure.step('Log in through the Snipe-IT web interface'):
            LoginPage(
                browser_driver,
                snipeit_settings.base_url,
                snipeit_settings.ui_timeout,
            ).open().login(
                snipeit_settings.admin_username,
                snipeit_settings.admin_password,
            )

        with allure.step('Open and verify the asset list page'):
            assets_page = AssetsPage(
                browser_driver,
                snipeit_settings.base_url,
                snipeit_settings.ui_timeout,
            ).open()
            assert assets_page.heading() == 'Assets'
            assert assets_page.is_search_available()
