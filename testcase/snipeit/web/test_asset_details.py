import allure
import pytest

from pages.assets_page import AssetsPage
from testcase.snipeit.helpers import find_status_id


pytestmark = [pytest.mark.snipeit, pytest.mark.web]


@pytest.fixture
def api_created_asset(
        snipeit_client,
        snipeit_resource_factory,
        unique_name,
):
    category = snipeit_resource_factory.create('categories', {
        'name': unique_name('web_category'),
        'category_type': 'asset',
    })
    manufacturer = snipeit_resource_factory.create('manufacturers', {
        'name': unique_name('web_manufacturer'),
    })
    location = snipeit_resource_factory.create('locations', {
        'name': unique_name('web_location'),
    })
    model = snipeit_resource_factory.create('models', {
        'name': unique_name('web_model'),
        'model_number': unique_name('web_model_number'),
        'category_id': category['id'],
        'manufacturer_id': manufacturer['id'],
    })
    request_body = {
        'asset_tag': unique_name('web_asset'),
        'name': 'Web 自动化测试笔记本',
        'serial': unique_name('web_serial'),
        'model_id': model['id'],
        'status_id': find_status_id(snipeit_client, 'deployable'),
        'rtd_location_id': location['id'],
        'notes': '由 API 创建并通过 Web 页面校验',
    }
    asset = snipeit_resource_factory.create('hardware', request_body)
    return {'id': asset['id'], **request_body}


@allure.feature('API 与 Web 组合场景')
class TestAssetDetails:

    @pytest.mark.smoke
    @allure.title('WEB-002 API 创建资产后可在 Web 列表和详情中查询')
    def test_api_asset_is_visible_in_web(
            self,
            logged_in_driver,
            snipeit_settings,
            api_created_asset,
    ):
        with allure.step('通过 API 创建唯一的测试资产和依赖数据'):
            expected = api_created_asset

        with allure.step('在 Web 资产列表中按资产标签搜索'):
            assets_page = AssetsPage(
                logged_in_driver,
                snipeit_settings.base_url,
                snipeit_settings.ui_timeout,
            ).open()
            row = assets_page.search(expected['asset_tag'])
            assert expected['asset_tag'] in row.text
            assert expected['serial'] in row.text

        with allure.step('打开资产详情并校验标签、名称和序列号'):
            details_page = assets_page.open_asset_details(
                expected['asset_tag'],
            ).wait_until_loaded()
            assert details_page.contains_asset_values(
                expected['asset_tag'],
                expected['name'],
                expected['serial'],
            )
