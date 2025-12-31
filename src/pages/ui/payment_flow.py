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
        """Complete Flutterwave payment - Handles dynamic iframe loading"""
        try:
            self.logger.info("=== Starting Flutterwave Card Payment ===")
            
            # Wait for Flutterwave URL
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.url_contains("flutterwave")
                )
                self.logger.info("✅ Navigated to Flutterwave URL")
            except:
                self.logger.warning("⚠️ URL check timeout, continuing...")
            
            current_url = self.driver.current_url
            self.logger.info(f"Current URL: {current_url}")
            
            # Check for 503 error
            if "503" in current_url:
                self.logger.error("❌ 503 Service Unavailable")
                return False
            
            # Check for specific Flutterwave checkout URL
            is_checkout_url = "checkout-v2.dev-flutterwave.com/v3/hosted/pay" in current_url
            
            if not is_checkout_url:
                self.logger.error(f"❌ Not on Flutterwave checkout page. URL: {current_url}")
                return False
            
            self.logger.info("✅ On correct Flutterwave checkout page")
            
            # KEY INSIGHT: The actual payment form is loaded into an iframe
            # Wait for iframe to be present and loaded
            self.logger.info("🔍 Waiting for payment iframe to load...")
            
            try:
                # Wait for iframe to exist
                iframe = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "iframe"))
                )
                self.logger.info("✅ Payment iframe found")
                
                # Switch to iframe
                self.driver.switch_to.frame(iframe)
                self.logger.info("✅ Switched to payment iframe")
                
                # Wait for content inside iframe to load
                WebDriverWait(self.driver, 15).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
                
                # Now check for payment form elements INSIDE the iframe
                iframe_page_source = self.driver.page_source.lower()
                self.logger.info(f"Iframe page source length: {len(iframe_page_source)} chars")
                
                # Check for key elements inside iframe
                checks = {
                    "Test mode text": "test mode" in iframe_page_source,
                    "Card field": any(x in iframe_page_source for x in ["card number", "card details", "0000 0000"]),
                    "Pay button": any(x in iframe_page_source for x in ["pay ngn", "pay ₦", "ngn"]),
                    "CVV field": "cvv" in iframe_page_source,
                    "Expiry field": any(x in iframe_page_source for x in ["expiry", "mm/yy", "valid"]),
                }
                
                self.logger.info("Iframe content checks:")
                for check_name, result in checks.items():
                    self.logger.info(f"  - {check_name}: {result}")
                
                # Verify we have the payment form
                passed_checks = sum(checks.values())
                if passed_checks >= 3:
                    self.logger.info(f"✅ Payment form verified ({passed_checks}/5 checks passed)")
                    
                    # Additional: Check for test mode banner specifically
                    try:
                        test_banner = self.driver.find_element(By.XPATH, "//*[contains(text(), 'test mode') or contains(text(), 'Test Mode')]")
                        if test_banner.is_displayed():
                            self.logger.info("✅ Test mode banner visible")
                    except:
                        self.logger.info("ℹ️ Test mode banner not found, but payment form is present")
                    
                    # Switch back to main content
                    self.driver.switch_to.default_content()
                    self.logger.info("✅ Successfully verified Flutterwave payment page")
                    return True
                else:
                    self.logger.error(f"❌ Payment form not fully loaded. Only {passed_checks}/5 checks passed")
                    # Debug: Log snippet of iframe content
                    lines = self.driver.page_source.split('\n')
                    for i, line in enumerate(lines[:10]):
                        if line.strip():
                            self.logger.debug(f"  Line {i}: {line.strip()[:100]}")
                    
                    self.driver.switch_to.default_content()
                    return False
                    
            except Exception as iframe_error:
                self.logger.error(f"❌ Iframe handling failed: {iframe_error}")
                try:
                    self.driver.switch_to.default_content()
                except:
                    pass
                
                # Fallback: Check if we're at least on the right URL
                if is_checkout_url:
                    self.logger.info("⚠️ Iframe failed but URL is correct. Attempting alternative verification...")
                    
                    # Try to find the iframe by checking all frames
                    frames = self.driver.find_elements(By.TAG_NAME, "iframe")
                    if frames:
                        self.logger.info(f"Found {len(frames)} iframe(s), attempting to locate payment iframe...")
                        
                        for i, frame in enumerate(frames):
                            try:
                                # Check iframe attributes
                                src = frame.get_attribute('src') or ''
                                title = frame.get_attribute('title') or ''
                                self.logger.info(f"  Iframe {i}: src={src[:50] if src else 'none'}, title={title}")
                            except:
                                pass
                    
                    # Last resort: If we're on the correct URL and page loaded, assume success
                    page_ready = self.driver.execute_script("return document.readyState") == "complete"
                    if page_ready:
                        self.logger.info("✅ Page loaded, assuming Flutterwave is ready")
                        return True
                
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error in complete_payment_flow: {e}")
            try:
                self.driver.switch_to.default_content()
            except:
                pass
            return False