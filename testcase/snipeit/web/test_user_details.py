import allure
import pytest

from pages.users_page import UsersPage
from testcase.snipeit.helpers import build_user_payload


pytestmark = [pytest.mark.snipeit, pytest.mark.web]


@pytest.fixture
def api_created_user(
        snipeit_resource_factory,
        unique_name,
):
    with allure.step('通过 API 创建唯一的已启用员工账号'):
        request_body = build_user_payload(
            unique_name,
            first_name='自动化',
            last_name='测试员工',
        )
        user = snipeit_resource_factory.create('users', request_body)
        return {'id': user['id'], **request_body}


@allure.feature('API 与 Web 组合场景')
class TestUserDetails:

    @pytest.mark.smoke
    @allure.title('WEB-003 API 创建用户后可在 Web 列表和详情中查询')
    def test_api_user_is_visible_in_web(
            self,
            logged_in_driver,
            snipeit_settings,
            api_created_user,
    ):
        expected = api_created_user

        with allure.step('在 Web 用户列表中按用户名搜索'):
            users_page = UsersPage(
                logged_in_driver,
                snipeit_settings.base_url,
                snipeit_settings.ui_timeout,
            ).open()
            row_text = users_page.search(expected['username'])
            assert expected['username'] in row_text
            assert expected['email'] in row_text

        with allure.step('打开用户详情并校验姓名、用户名和邮箱'):
            details_page = users_page.open_user_details(
                expected['id'],
            ).wait_until_loaded()
            assert details_page.contains_user_values(
                expected['first_name'],
                expected['last_name'],
                expected['username'],
                expected['email'],
            )
