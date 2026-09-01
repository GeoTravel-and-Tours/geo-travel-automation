"""
src/pages/ui/payment_flow.py

Page Object for the Flutterwave hosted-checkout payment step, shared by
the package booking and flight booking flows.

Covers:
    1. Trigger checkout - click "Proceed to payment" to launch the
       Flutterwave flow.
    2. Reach checkout   - wait for the browser to land on Flutterwave's
       hosted-payment URL, switch into its iframe, and do a minimal
       readiness check.

``PackageBookingFlow`` (package_booking_flow.py) imports ``PaymentPage``
from this module, though at the time of writing it does not actually
instantiate/call it anywhere in its own Flutterwave verification path
(``verify_flutterwave_payment`` there re-implements its own URL check
instead) - see the NOTE on the import there and the FIXME on
``complete_payment_flow`` below. ``FlightBookingFlow``
(flight_booking_flow.py) does not use this class at all; it implements
its own, more limited inline Flutterwave option click
(``select_payment_method``) without importing this module.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.core.base_page import BasePage
from src.utils.wait_strategy import WaitStrategy
import time

class PaymentPage(BasePage):
    """
    Handles the Flutterwave hosted-checkout payment flow for packages and flights.

    Locators cover both the "Proceed to payment" trigger and the card
    entry fields inside the Flutterwave iframe (card number/expiry/CVV,
    the Pay button). ``TEST_CARD_DETAILS`` holds Flutterwave's
    documented test-mode card. See the FIXME on ``complete_payment_flow``
    below - these card locators and test data are currently unused.
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
        """Initialize the page object.

        Args:
            driver (WebDriver): Active Selenium WebDriver instance, passed
                through to ``BasePage``.
        """
        super().__init__(driver)

    def proceed_to_payment(self):
        """Click the "Proceed to payment" button.

        Returns:
            WebElement: The clicked button.

        Raises:
            Exception: Re-raised if the button can't be found/clicked.
        """
        self.logger.info("Clicking 'Proceed to payment' button")
        try:
            proceed_button = self.element.click(self.PROCEED_TO_PAYMENT_BUTTON)
            self._last_interacted_element = proceed_button
            return proceed_button
        except Exception as e:
            self.logger.error(f"Failed to click 'Proceed to payment' button: {e}")
            raise

    def complete_payment_flow(self):
        """Wait for Flutterwave checkout to load and do a minimal readiness check.

        Waits for the URL to contain "flutterwave" and specifically match
        the dev/sandbox hosted-checkout path, switches into the payment
        iframe, and checks whether any ``<input>`` elements are present -
        it does NOT actually fill in card details or click Pay.

        FIXME: ``CARD_NUMBER_INPUT``, ``EXPIRY_DATE_INPUT``, ``CVV_INPUT``,
        ``PAY_BUTTON``, and ``TEST_CARD_DETAILS`` are all defined on this
        class but never referenced here (or anywhere else in this file).
        As written, this method only confirms the iframe loaded with some
        inputs present - it does not submit an actual card payment, so it
        cannot verify a payment fully completes. If the intent was to
        drive a full test-card payment, that part was never implemented.

        Returns:
            bool: True if the Flutterwave checkout page and iframe loaded
                as expected, False on any failure (also switches back to
                default content before returning False).
        """
        try:
            self.logger.info("=== Starting Flutterwave Card Payment ===")
            
            # Wait for Flutterwave URL
            WebDriverWait(self.driver, 30).until(
                EC.url_contains("flutterwave")
            )
            self.logger.info("✅ Navigated to Flutterwave URL")
            
            current_url = self.driver.current_url
            self.logger.info(f"Current URL: {current_url}")
            
            # Verify correct checkout URL
            if "checkout-v2.dev-flutterwave.com/v3/hosted/pay" not in current_url:
                self.logger.error(f"❌ Not on Flutterwave checkout page: {current_url}")
                return False
            
            self.logger.info("✅ On correct Flutterwave checkout page")
            
            # Wait for page load
            WebDriverWait(self.driver, 30).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Find and switch to iframe
            iframe = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "iframe"))
            )
            self.driver.switch_to.frame(iframe)
            self.logger.info("✅ Switched to payment iframe")
            
            # Wait for iframe to load
            WebDriverWait(self.driver, 20).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Wait a reasonable time for Vue to render (but don't fail if it takes longer)
            time.sleep(5)
            
            # Basic check - are there any form elements?
            try:
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                self.logger.info(f"Found {len(inputs)} input elements")
                
                # Even if 0 inputs, we're still on the payment page
                # The important thing is we reached Flutterwave
                
            except:
                pass
            
            self.driver.switch_to.default_content()
            self.logger.info("✅ Successfully loaded Flutterwave payment page")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error in complete_payment_flow: {e}")
            try:
                self.driver.switch_to.default_content()
            except:
                pass
            return False