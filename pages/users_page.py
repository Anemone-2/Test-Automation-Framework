from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as ec

from pages.base_page import BasePage
from pages.user_details_page import UserDetailsPage


class UsersPage(BasePage):
    USERS_TABLE = (By.ID, 'ListingTable')
    TABLE_SEARCH = (By.CSS_SELECTOR, 'input.search-input[type="search"]')
    TABLE_ROWS = (By.CSS_SELECTOR, 'table#ListingTable tbody tr')

    def open(self):
        super().open('users')
        self.wait.until(ec.visibility_of_element_located(self.USERS_TABLE))
        return self

    def search(self, keyword):
        search_box = self.wait.until(
            ec.visibility_of_element_located(self.TABLE_SEARCH),
        )
        search_box.clear()
        search_box.send_keys(keyword)
        search_box.send_keys(Keys.ENTER)
        return self.wait.until(lambda _: self._find_filtered_row_text(keyword))

    def open_user_details(self, user_id):
        user_link = self.wait.until(
            ec.element_to_be_clickable((
                By.CSS_SELECTOR,
                f'table#ListingTable tbody a[href$="/users/{user_id}"]',
            )),
        )
        self.driver.execute_script('arguments[0].click();', user_link)
        self.wait.until(ec.url_contains(f'/users/{user_id}'))
        return UserDetailsPage(
            self.driver,
            self.base_url,
            self.timeout,
        )

    def _find_filtered_row_text(self, keyword):
        try:
            rows = self.driver.find_elements(*self.TABLE_ROWS)
            populated_rows = [row.text for row in rows if row.text.strip()]
        except StaleElementReferenceException:
            return False
        if not populated_rows:
            return False
        if not all(keyword in row_text for row_text in populated_rows):
            return False
        return populated_rows[0]
