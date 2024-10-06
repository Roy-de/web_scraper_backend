import logging
import os
import shutil

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


class BaseSelenium:
    logging.getLogger('selenium').setLevel(logging.DEBUG)

    def __init__(self, browser: str = 'chrome', implicit_wait: int = 10):
        # Initialize the WebDriver based on the browser type
        if browser == 'chrome':
            chrome_options = ChromeOptions()
            chrome_options.page_load_strategy = 'eager'
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--log-level=4")
            chrome_options.add_argument("--window-size=1920x1080")
            chrome_options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.5735.199 Safari/537.36")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Prevent detection
            chrome_options.add_argument("--enable-javascript")  # Ensure JS is enabled
            prefs = {
                "profile.managed_default_content_settings.images": 2,  # Disable images
                "profile.default_content_setting_values.notifications": 2,  # Disable notifications
                "profile.managed_default_content_settings.stylesheets": 2  # Disable CSS
            }
            driver_path = self.get_chrome_driver_path()

            service = Service(driver_path)

            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        elif browser == 'firefox':
            firefox_options = FirefoxOptions()
            firefox_options.add_argument("--disable-dev-shm-usage")
            firefox_options.add_argument("--headless")  # Example option, run in headless mode
            firefox_options.add_argument("--no-sandbox")
            self.driver = webdriver.Firefox(options=firefox_options)
        else:
            raise ValueError(f"Browser {browser} is not supported.")

        self.driver.implicitly_wait(implicit_wait)
        self.result = None

    logging.getLogger('selenium').setLevel(logging.CRITICAL)

    @staticmethod
    def get_chrome_driver_path():
        """Get the path of the ChromeDriver, downloading it to the project if not present."""
        # Specify the project-specific directory to store the driver
        project_dir = os.path.dirname(os.path.abspath(__file__))  # Get the path of this script
        driver_dir = os.path.join(project_dir, 'drivers')  # Create a 'drivers' folder in the project
        os.makedirs(driver_dir, exist_ok=True)

        # Check if chromedriver is already downloaded in the specified folder
        custom_driver_path = os.path.join(driver_dir, 'chromedriver')

        # Check if chromedriver already exists in the project directory
        if os.path.exists(custom_driver_path):
            print("ChromeDriver already exists in project directory.")
            return custom_driver_path

        # Download the ChromeDriver using ChromeDriverManager
        print("Downloading ChromeDriver...")
        downloaded_driver_path = ChromeDriverManager().install()

        # Copy the downloaded driver to the custom directory
        shutil.copy(downloaded_driver_path, custom_driver_path)

        return custom_driver_path  # Return the path of the ChromeDriver in the project directory

    def navigate_to_page(self, url: str):
        """Navigate to the given URL."""
        self.driver.get(url)

    def find_element(self, by: By, value: str):
        """Find an element on the page."""
        try:
            return self.driver.find_element(by, value)
        except NoSuchElementException:
            print(f"Element not found: {value}")
            return None

    def wait_for_element(self, by: By, value: str, timeout: int = 10):
        """Wait for an element to be present on the page."""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            print(f"Timed out waiting for element: {value}")
            return None

    def click_element(self, by: By, value: str):
        """Click an element on the page."""
        element = self.find_element(by, value)
        if element:
            element.click()

    def enter_text(self, by: By, value: str, text: str):
        """Enter text into an input field."""
        element = self.find_element(by, value)
        if element:
            element.clear()
            element.send_keys(text)

    def close_browser(self):
        """Close the browser."""
        self.driver.quit()

    def take_screenshot(self, file_name: str):
        """Take a screenshot of the current page."""
        self.driver.save_screenshot(file_name)

    def run(self):
        """Main method to be overridden by child classes with specific test steps."""
        raise NotImplementedError("You must override the run() method in a subclass.")
