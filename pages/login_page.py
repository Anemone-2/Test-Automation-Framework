from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

from pages.base_page import BasePage


class LoginPage(BasePage):
    USERNAME = (By.ID, 'username')
    PASSWORD = (By.ID, 'password-field')
    SUBMIT = (By.ID, 'submit')

    def open(self):
        return super().open('login')

    def login(self, username, password):
        self.wait.until(ec.visibility_of_element_located(self.USERNAME)).send_keys(
            username,
        )
        self.driver.find_element(*self.PASSWORD).send_keys(password)
        self.driver.find_element(*self.SUBMIT).click()
        self.wait.until(lambda driver: '/login' not in driver.current_url)
        return self
