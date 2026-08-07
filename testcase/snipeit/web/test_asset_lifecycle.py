import allure
import pytest

from pages.assets_page import AssetsPage


pytestmark = [pytest.mark.snipeit, pytest.mark.web]


@allure.feature('资产领用与归还业务闭环')
class TestAssetLifecycle:

    @pytest.mark.smoke
    @allure.title('WEB-004 资产领用与归还状态在 API、Web 和 MySQL 中一致')
    def test_checkout_and_checkin_lifecycle(
            self,
            logged_in_driver,
            snipeit_settings,
            asset_flow_context,
            snipeit_db,
    ):
        context = asset_flow_context

        with allure.step('通过 API 创建资产并领用给测试员工'):
            asset, expected = context.create_asset()
            checkout_response = context.checkout(asset['id'])
            assert checkout_response.status_code == 200
            assert checkout_response.json()['status'] == 'success'
            user = context.client.get(f"users/{context.user['id']}").json()

        with allure.step('校验 MySQL 已记录资产领用关系'):
            assigned = snipeit_db.query_one(
                'SELECT assigned_to, assigned_type FROM assets WHERE id = %s',
                (asset['id'],),
            )
            assert assigned['assigned_to'] == context.user['id']
            assert assigned['assigned_type'] == 'App\\Models\\User'

        with allure.step('在 Web 资产详情校验领用员工及归还入口'):
            details_page = AssetsPage(
                logged_in_driver,
                snipeit_settings.base_url,
                snipeit_settings.ui_timeout,
            ).open().open_asset_details(
                expected['asset_tag'],
            ).wait_until_loaded()
            assert details_page.contains_asset_values(
                expected['asset_tag'],
                user['name'],
            )
            assert details_page.has_checkin_action(asset['id'])

        with allure.step('通过 API 归还资产并校验接口及 MySQL 状态'):
            checkin_response = context.checkin(asset['id'])
            assert checkin_response.status_code == 200
            assert checkin_response.json()['status'] == 'success'
            api_asset = context.client.get(f"hardware/{asset['id']}").json()
            returned = snipeit_db.query_one(
                'SELECT assigned_to, assigned_type FROM assets WHERE id = %s',
                (asset['id'],),
            )
            assert api_asset['assigned_to'] is None
            assert returned['assigned_to'] is None
            assert returned['assigned_type'] is None

        with allure.step('刷新 Web 详情并校验资产重新出现领用入口'):
            logged_in_driver.refresh()
            details_page.wait_until_loaded()
            assert details_page.has_checkout_action(asset['id'])
