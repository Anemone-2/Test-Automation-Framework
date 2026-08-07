from urllib.parse import urljoin

from selenium.webdriver.support.ui import WebDriverWait


class BasePage:
    def __init__(self, driver, base_url, timeout=10):
        self.driver = driver
        self.base_url = base_url.rstrip('/') + '/'
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)

    def open(self, path=''):
        self.driver.get(urljoin(self.base_url, path.lstrip('/')))
        return self
