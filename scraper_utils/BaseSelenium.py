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
    def __init__(self, browser: str = 'chrome', implicit_wait: int = 10):
        # Initialize the WebDriver based on the browser type
        if browser == 'chrome':
            chrome_options = ChromeOptions()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--headless")
            chrome_options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.5735.199 Safari/537.36")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Prevent detection
            chrome_options.add_argument("--enable-javascript")  # Ensure JS is enabled

            service = Service(ChromeDriverManager().install())

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
