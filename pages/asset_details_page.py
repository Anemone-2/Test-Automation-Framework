from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

from pages.base_page import BasePage


class AssetDetailsPage(BasePage):
    PAGE_HEADING = (By.CSS_SELECTOR, '.content-header h1.pagetitle')
    PAGE_BODY = (By.TAG_NAME, 'body')

    def wait_until_loaded(self):
        self.wait.until(ec.visibility_of_element_located(self.PAGE_HEADING))
        return self

    def contains_asset_values(self, *expected_values):
        def values_are_visible(driver):
            page_text = driver.find_element(*self.PAGE_BODY).text
            return all(value in page_text for value in expected_values)

        return bool(self.wait.until(values_are_visible))
