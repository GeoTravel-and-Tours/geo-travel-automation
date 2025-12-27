# src/utils/navigation.py

from src.utils.logger import GeoLogger
from src.utils.wait_strategy import WaitStrategy
from src.utils.javascript import JavaScriptUtils
from selenium.webdriver.common.by import By
import time

class NavigationUtils:
    """Dedicated class for browser navigation"""

    def __init__(self, driver):
        self.driver = driver
        self.logger = GeoLogger(name="NavigationUtils")
        self.waiter = WaitStrategy(driver)
        self.javascript = JavaScriptUtils(driver)

    def go_to_url(self, url):
        """Navigate to URL"""
        self.logger.info(f"Navigating to URL: {url}")
        self.driver.get(url)

    def refresh_page(self):
        """Refresh current page"""
        self.logger.info("Refreshing current page")
        self.driver.refresh()

    def go_back(self):
        """Go back to previous page"""
        self.logger.info("Going back to previous page")
        self.driver.back()
        self.waiter.wait_for_page_load(timeout=10)
        
    def go_forward(self):
        """Go forward to next page"""
        self.logger.info("Going forward to next page")
        self.driver.forward()
        self.waiter.wait_for_page_load(timeout=10)

    def get_current_url(self):
        """Get current URL"""
        self.logger.info("Getting current URL")
        return self.driver.current_url
    
    def current_url_contains(self, text):
        return text.lower() in self.get_current_url().lower()


    def get_page_title(self):
        """Get page title"""
        self.logger.info("Getting page title")
        return self.driver.title
    
    def get_navigation_links(self, max_links=10):
        """Get clickable navigation links from the page"""
        self.logger.info("Finding navigation links")
        links = self.driver.find_elements(By.TAG_NAME, "a")

        clickable_links = []
        for link in links[:max_links]:
            try:
                href = link.get_attribute("href")
                if (href and 
                    "javascript" not in href.lower() and 
                    link.is_displayed() and 
                    link.is_enabled()):
                    clickable_links.append({
                        'element': link,
                        'href': href,
                        'text': link.text.strip()[:50]  # Truncate long text
                    })
            except Exception as e:
                self.logger.debug(f"Skipping link: {e}")
                continue
            
        self.logger.info(f"Found {len(clickable_links)} clickable links out of {len(links)} total")
        return clickable_links

    def click_navigation_link(self, link_element, link_info):
        """Click a navigation link and return new URL"""
        try:
            self.logger.info(f"Clicking navigation link: {link_info['href']}")

            # Scroll into view and click using JavaScript for reliability
            self.javascript.execute_script("arguments[0].scrollIntoView({block: 'center'});", link_element)
            self.javascript.execute_script("arguments[0].click();", link_element)

            # Wait for navigation
            time.sleep(3)  # Basic wait, you might want to use WebDriverWait instead
            self.javascript.wait_for_page_load(10)

            new_url = self.get_current_url()
            self.logger.success(f"Navigation successful: {link_info['href']} -> {new_url}")
            return new_url

        except Exception as e:
            self.logger.warning(f"Failed to click link {link_info['href']}: {e}")
            return None

    def test_navigation_works(self, initial_url, max_attempts=3):
        """Test that navigation works by clicking links"""
        self.logger.info("=== Testing Navigation Functionality ===")

        links = self.get_navigation_links(max_links=max_attempts)

        if not links:
            self.logger.warning("No suitable navigation links found")
            return False, "No clickable links found"

        for i, link_info in enumerate(links, 1):
            self.logger.info(f"Attempt {i}/{len(links)}: Testing link to {link_info['href']}")

            new_url = self.click_navigation_link(link_info['element'], link_info)

            if new_url and new_url != initial_url:
                self.logger.success(f"Navigation verified: {initial_url} → {new_url}")
                return True, f"Successfully navigated to {new_url}"

        self.logger.warning("All navigation attempts failed or didn't change URL")
        return False, "No successful navigation occurred"