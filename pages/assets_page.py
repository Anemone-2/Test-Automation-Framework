from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec

from pages.asset_details_page import AssetDetailsPage
from pages.base_page import BasePage


class AssetsPage(BasePage):
    PAGE_HEADING = (By.CSS_SELECTOR, '.content-header h1.pagetitle')
    ASSETS_TABLE = (By.ID, 'assetsListingTable')
    TABLE_SEARCH = (By.CSS_SELECTOR, 'input.search-input[type="search"]')
    TABLE_ROWS = (By.CSS_SELECTOR, '#assetsListingTable tbody tr')

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

    def search(self, keyword):
        search_box = self.wait.until(
            ec.visibility_of_element_located(self.TABLE_SEARCH),
        )
        search_box.clear()
        search_box.send_keys(keyword)
        search_box.send_keys(Keys.ENTER)
        return self.wait.until(lambda _: self._find_row(keyword))

    def open_asset_details(self, asset_tag):
        row = self.search(asset_tag)
        links = row.find_elements(By.TAG_NAME, 'a')
        asset_link = next(
            (link for link in links if link.text.strip() == asset_tag),
            None,
        )
        assert asset_link is not None, f'Asset link not found: {asset_tag}'
        asset_link.click()
        self.wait.until(ec.url_contains('/hardware/'))
        return AssetDetailsPage(
            self.driver,
            self.base_url,
            self.timeout,
        )

    def _find_row(self, keyword):
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        return next(
            (row for row in rows if keyword in row.text),
            False,
        )
