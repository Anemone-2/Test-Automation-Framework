import allure
import pytest

from pages.assets_page import AssetsPage
from pages.login_page import LoginPage


pytestmark = [pytest.mark.snipeit, pytest.mark.web]


@allure.feature('Web 登录与页面访问')
class TestWebLogin:

    @pytest.mark.smoke
    @allure.title('WEB-001 管理员登录后可以打开资产列表')
    def test_admin_login_opens_asset_list(
            self,
            browser_driver,
            snipeit_settings,
    ):
        with allure.step('通过 Snipe-IT Web 页面登录管理员账号'):
            LoginPage(
                browser_driver,
                snipeit_settings.base_url,
                snipeit_settings.ui_timeout,
            ).open().login(
                snipeit_settings.admin_username,
                snipeit_settings.admin_password,
            )

        with allure.step('打开资产列表并校验页面关键元素'):
            assets_page = AssetsPage(
                browser_driver,
                snipeit_settings.base_url,
                snipeit_settings.ui_timeout,
            ).open()
            assert assets_page.heading() == '资产'
            assert assets_page.is_search_available()
