from pathlib import Path

import allure
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f'rep_{report.when}', report)
def build_driver(settings):
    if settings.browser == 'edge':
        options = webdriver.EdgeOptions()
        driver_class = webdriver.Edge
        service_class = EdgeService
        cache_folder = 'msedgedriver'
        executable_name = 'msedgedriver.exe'
    elif settings.browser == 'chrome':
        options = webdriver.ChromeOptions()
        driver_class = webdriver.Chrome
        service_class = ChromeService
        cache_folder = 'chromedriver'
        executable_name = 'chromedriver.exe'
    else:
        raise ValueError(
            f'Unsupported SNIPEIT_BROWSER: {settings.browser}. '
            'Use edge or chrome.'
        )

    if settings.headless:
        options.add_argument('--headless=new')
    options.add_argument('--window-size=1440,1000')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver_path = settings.driver_path or find_cached_driver(
        cache_folder,
        executable_name,
    )
    if driver_path:
        return driver_class(
            service=service_class(executable_path=driver_path),
            options=options,
        )
    return driver_class(options=options)


def find_cached_driver(cache_folder, executable_name):
    driver_root = Path.home() / '.cache' / 'selenium' / cache_folder
    candidates = list(driver_root.glob(f'**/{executable_name}'))
    if not candidates:
        return ''

    def version_key(path):
        try:
            return tuple(int(part) for part in path.parent.name.split('.'))
        except ValueError:
            return (0,)

    return str(max(candidates, key=version_key))


@pytest.fixture
def browser_driver(request, snipeit_settings):
    driver = build_driver(snipeit_settings)
    driver.set_page_load_timeout(snipeit_settings.ui_timeout)
    yield driver

    report = getattr(request.node, 'rep_call', None)
    if report and report.failed:
        allure.attach(
            driver.get_screenshot_as_png(),
            name='Web failure screenshot',
            attachment_type=allure.attachment_type.PNG,
        )
        allure.attach(
            driver.page_source,
            name='Web failure page source',
            attachment_type=allure.attachment_type.HTML,
        )
    driver.quit()
