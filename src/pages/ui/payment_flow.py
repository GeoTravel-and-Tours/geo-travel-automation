# src/pages/ui/payment_flow.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.core.base_page import BasePage
from src.utils.wait_strategy import WaitStrategy
import time

class PaymentPage(BasePage):
    """
    Handles Flutterwave payment flow for packages and flights
    """
    
    # Flutterwave Payment Locators
    PROCEED_TO_PAYMENT_BUTTON = (By.XPATH, "//button[normalize-space()='Proceed to payment']")
    TEST_MODE_BANNER = (By.XPATH, "//*[contains(text(), 'test mode') or contains(text(), 'TEST MODE')]")
    CARD_OPTION = (By.XPATH, "//*[contains(text(), 'Card')]")
    CARD_NUMBER_INPUT = (By.ID, "cardnumber")
    EXPIRY_DATE_INPUT = (By.ID, "expiry") 
    CVV_INPUT = (By.ID, "cvv")
    PAY_BUTTON = (By.XPATH, "//button[contains(text(), 'Pay NGN')]")
    
    # Test card details for Flutterwave test mode
    TEST_CARD_DETAILS = {
        "card_number": "5531886652142950",
        "expiry": "09/32", 
        "cvv": "564",
        "pin": "3310",
        "otp": "12345"
    }

    def __init__(self, driver):
        super().__init__(driver)

    def proceed_to_payment(self):
        """Click proceed to payment button"""
        self.logger.info("Clicking 'Proceed to payment' button")
        try:
            proceed_button = self.element.click(self.PROCEED_TO_PAYMENT_BUTTON)
            self._last_interacted_element = proceed_button
            return proceed_button
        except Exception as e:
            self.logger.error(f"Failed to click 'Proceed to payment' button: {e}")
            raise
    
    def complete_payment_flow(self):
        """Complete Flutterwave payment using card - STOPPED AT TEST MODE VERIFICATION"""
        try:
            self.logger.info("=== Starting Flutterwave Card Payment ===")
            
            # Wait for flutterwave to load completely
            WebDriverWait(self.driver, 20).until(
                EC.url_contains("flutterwave")
            )
            self.logger.info("✅ Navigated to Flutterwave URL")

            # 🔥 SIMPLIFIED: Switch to the first iframe directly
            self.logger.info("🔍 Switching to Flutterwave iframe...")
            
            # Wait for iframe and switch to it
            iframe = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "iframe"))
            )
            self.driver.switch_to.frame(iframe)
            self.logger.info("✅ Switched to Flutterwave iframe")

            # Wait for test mode banner instead of fixed sleep
            self.logger.info("🔍 Waiting for test mode banner...")
            test_banner = WebDriverWait(self.driver, 15).until(
                EC.visibility_of_element_located(self.TEST_MODE_BANNER)
            )
            assert test_banner.is_displayed(), "Test mode banner should be visible"
            self.logger.info("✅ Flutterwave test mode verified")

            # Switch back to main content
            self.driver.switch_to.default_content()
            self.logger.info("✅ Switched back to main content")
            
            return True  # Successfully reached test mode

        except Exception as e:
            self.logger.error(f"❌ Failed to reach Flutterwave test mode: {e}")
            # Ensure we switch back if an exception occurs
            try:
                self.driver.switch_to.default_content()
            except:
                pass
            return False
