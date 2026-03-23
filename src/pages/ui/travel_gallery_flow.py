# src/pages/ui/travel_gallery_flow.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from src.core.base_page import BasePage
import time


class TravelGalleryPage(BasePage):
    """Page Object for Travel Gallery functionality"""
    
    def __init__(self, driver):
        super().__init__(driver)
    
    # ========== LOCATORS ==========
    # Navigation
    TRAVEL_GALLERY_MENU = (By.XPATH, "//a[@class='py-2 hover:bg-slate-100 transition-all truncate text-base'][normalize-space()='Travel Gallery']")
    TRAVEL_GALLERY_HEADER = (By.XPATH, "//h3[normalize-space()='Travel Gallery']")
    
    # Gallery Page Elements
    GALLERY_CONTAINER = (By.XPATH, "//main[@data-sentry-component='Page']")
    FIRST_TOUR_CARD = (By.XPATH, "//main[@data-sentry-component='Page']//div[1]//div[1]//div[2]")
    TOUR_CARDS = (By.XPATH, "//main[@data-sentry-component='Page']//div[contains(@class, 'cursor-pointer')]")
    
    # Tour Detail Page Elements
    MODAL_CONTAINER = (By.XPATH, "//main[@data-sentry-component='GalleryPage']")
    MODAL_IMAGES = (By.XPATH, "//main[@data-sentry-component='GalleryPage']//img")
    MODAL_CLOSE_BTN = (By.XPATH, "//main[@data-sentry-component='GalleryPage']//button[contains(@class, 'absolute')]")
    
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
        """Wait for tour detail page to load with images"""
        self.logger.info("Waiting for tour detail to load")
        
        try:
            # Wait for the gallery page component to be present
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(self.MODAL_CONTAINER)
            )
            
            # Wait for images to be present
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located(self.MODAL_IMAGES)
            )
            
            self.logger.info("Tour detail loaded with images")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load tour detail: {e}")
            return False
    
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
        """Hover over image and click the eye icon to view"""
        self.logger.info(f"Clicking view button on image {image_index + 1}")
        
        try:
            # Get the image container that has the overlay button
            image_containers = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'relative')]//div[contains(@class, 'group')]"))
            )
            
            assert len(image_containers) > image_index, f"No image container at index {image_index} found"
            
            # Hover over the image container to reveal the eye button
            container = image_containers[image_index]
            ActionChains(self.driver).move_to_element(container).perform()
            time.sleep(1)
            
            # Click the eye button
            eye_button = container.find_element(By.XPATH, ".//button[contains(@class, 'bg-white/90')]")
            eye_button.click()
            time.sleep(1)
            
            self.logger.info(f"Clicked view button on image {image_index + 1}")
            return self
            
        except Exception as e:
            self.logger.error(f"Failed to click view button: {e}")
            raise
        
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