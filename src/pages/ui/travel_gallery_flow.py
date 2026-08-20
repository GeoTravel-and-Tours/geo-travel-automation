# src/pages/ui/travel_gallery_flow.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from src.core.base_page import BasePage
import time


class TravelGalleryPage(BasePage):
    """Page Object for Travel Gallery functionality"""
    
    def __init__(self, driver):
        super().__init__(driver)
    
    # ========== LOCATORS ==========
    # Navigation
    TRAVEL_GALLERY_MENU = (
        By.XPATH,
        "//a[normalize-space()='Travel Gallery']"
    )

    TRAVEL_GALLERY_HEADER = (
        By.XPATH,
        "//h3[normalize-space()='Travel Gallery']"
    )

    # Gallery Page
    GALLERY_CONTAINER = (
        By.XPATH,
        "//main[.//h3[normalize-space()='Travel Gallery']]"
    )

    TOUR_CARDS = (
        By.XPATH,
        "//main[.//h3[normalize-space()='Travel Gallery']]"
        "//div[contains(@class, 'cursor-pointer')]"
    )

    FIRST_TOUR_CARD = (
        By.XPATH,
        "(//main[.//h3[normalize-space()='Travel Gallery']]"
        "//div[contains(@class, 'cursor-pointer')])[1]"
    )
    
    # Tour Detail Page Elements
    TOUR_DETAIL_CONTAINER = (
        By.XPATH,
        "//main[.//img]"
    )

    TOUR_DETAIL_IMAGES = (
        By.XPATH,
        "//main//img"
    )
    MODAL_CONTAINER = (By.XPATH, "//main[@data-sentry-component='GalleryPage']")
    MODAL_IMAGES = (By.XPATH, "//main[@data-sentry-component='GalleryPage']//img")
    MODAL_CLOSE_BTN = (By.XPATH, "//main[@data-sentry-component='GalleryPage']//button[contains(@class, 'absolute')]")
    IMAGE_CONTAINERS = (
        By.XPATH,
        "//main[.//img]"
        "//div[contains(@class, 'group') and .//img]"
    )
    
    # ========== PAGE METHODS ==========
    
    def open(self, base_url):
        """Open the application homepage"""
        self.logger.info("Opening application homepage")
        self.driver.get(base_url)
        return self
    
    def navigate_to_travel_gallery(self):
        """Navigate to Travel Gallery page from homepage"""
        self.logger.info("Navigating to Travel Gallery page")
        
        try:
            # Try to find Travel Gallery link (works for both desktop and mobile)
            gallery_menu = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='Travel Gallery']"))
            )
            gallery_menu.click()
            
            # Wait for page to load
            self.waiter.wait_for_present(self.TRAVEL_GALLERY_HEADER, timeout=15)
            self.waiter.wait_for_present(self.GALLERY_CONTAINER, timeout=15)
            
            # Verify URL contains gallery
            assert "gallery" in self.driver.current_url.lower() or "travel" in self.driver.current_url.lower(), \
                "URL should contain 'gallery' or 'travel'"
            
            self.logger.info("Successfully navigated to Travel Gallery page")
            return self
            
        except Exception as e:
            self.logger.error(f"Failed to navigate to Travel Gallery page: {e}")
            raise
    
    def verify_gallery_page_loaded(self):
        """Verify Travel Gallery page is fully loaded"""
        self.logger.info("Verifying Travel Gallery page loaded")
        
        try:
            # Check header is visible
            header = self.waiter.wait_for_visible(self.TRAVEL_GALLERY_HEADER, timeout=10)
            assert header.is_displayed(), "Travel Gallery header should be visible"
            
            # Check gallery container is present
            self.waiter.wait_for_present(self.GALLERY_CONTAINER, timeout=10)
            
            self.logger.info("Travel Gallery page verified")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to verify gallery page: {e}")
            return False
    
    def click_first_tour(self):
        """Click on the first tour card"""
        self.logger.info("Clicking on first tour card")
        
        try:
            # Wait for tour cards to be present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located(self.TOUR_CARDS)
            )
            
            # Click on the first tour card
            first_tour = self.waiter.wait_for_clickable(self.FIRST_TOUR_CARD, timeout=10)
            self.javascript.scroll_to_element(first_tour)
            first_tour.click()
            
            self.logger.info("Successfully clicked on first tour")
            return self
            
        except Exception as e:
            self.logger.error(f"Failed to click on first tour: {e}")
            raise
    
    def click_on_any_tour(self, index=0):
        """Click on a tour card by index"""
        self.logger.info(f"Clicking on tour card at index {index}")
        
        try:
            tour_cards = self.waiter.wait_for_present_all(self.TOUR_CARDS, timeout=10)
            assert len(tour_cards) > index, f"Tour card at index {index} not found"
            
            tour_card = tour_cards[index]
            self.javascript.scroll_to_element(tour_card)
            tour_card.click()
            
            self.logger.info(f"Successfully clicked on tour card {index}")
            return self
            
        except Exception as e:
            self.logger.error(f"Failed to click on tour card at index {index}: {e}")
            raise
    
    def wait_for_tour_detail_load(self, timeout=15):
        """Wait for tour detail/gallery view to load."""
        self.logger.info("Waiting for tour detail to load")

        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.TOUR_DETAIL_CONTAINER)
            )

            WebDriverWait(self.driver, timeout).until(
                lambda driver: len(
                    driver.find_elements(*self.TOUR_DETAIL_IMAGES)
                ) > 0
            )

            self.logger.info("Tour detail loaded with images")
            return True

        except TimeoutException as e:
            self.logger.error(
                f"Tour detail did not load. "
                f"Current URL: {self.driver.current_url}"
            )
            raise AssertionError(
                f"Tour detail page did not load. "
                f"Current URL: {self.driver.current_url}"
            ) from e
    
    def verify_gallery_has_tours(self):
        """Verify that gallery page has at least one tour card"""
        self.logger.info("Verifying gallery has tour cards")
        
        try:
            tour_cards = self.driver.find_elements(*self.TOUR_CARDS)
            count = len(tour_cards)
            self.logger.info(f"Found {count} tour cards")
            
            assert count > 0, "No tour cards found on gallery page"
            return count
            
        except Exception as e:
            self.logger.error(f"Failed to verify tour cards: {e}")
            return 0
        
    def click_tour_image(self, image_index=0):
        """Hover over a gallery image and click its view button."""
        self.logger.info(
            f"Clicking view button on image {image_index + 1}"
        )

        containers = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located(self.IMAGE_CONTAINERS)
        )

        if len(containers) <= image_index:
            raise AssertionError(
                f"No image container found at index {image_index}. "
                f"Found {len(containers)} containers."
            )

        container = containers[image_index]

        self.javascript.scroll_to_element(container)

        ActionChains(self.driver).move_to_element(container).perform()

        eye_button = WebDriverWait(self.driver, 10).until(
            lambda driver: container.find_element(
                By.XPATH,
                ".//button"
            )
        )

        eye_button.click()

        self.logger.info(
            f"Clicked view button on image {image_index + 1}"
        )

        return self
        
    def close_image_viewer(self):
        """Close the image viewer modal"""
        self.logger.info("Closing image viewer")
        
        try:
            # Try ESC key first
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(1)
            
            self.logger.info("Image viewer closed")
            return self
            
        except Exception as e:
            self.logger.error(f"Failed to close image viewer: {e}")
            raise