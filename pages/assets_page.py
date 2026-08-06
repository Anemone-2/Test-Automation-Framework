from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

from pages.base_page import BasePage


class AssetsPage(BasePage):
    PAGE_HEADING = (By.CSS_SELECTOR, '.content-header h1.pagetitle')
    ASSETS_TABLE = (By.ID, 'assetsListingTable')
    TABLE_SEARCH = (By.CSS_SELECTOR, 'input[type="search"][aria-label="Search"]')

    def open(self):
        super().open('hardware')
        self.wait.until(ec.visibility_of_element_located(self.ASSETS_TABLE))
        return self

    def heading(self):
        return self.wait.until(
            ec.visibility_of_element_located(self.PAGE_HEADING),
        ).text.strip()

    def is_search_available(self):
        return self.wait.until(
            ec.visibility_of_element_located(self.TABLE_SEARCH),
        ).is_enabled()
