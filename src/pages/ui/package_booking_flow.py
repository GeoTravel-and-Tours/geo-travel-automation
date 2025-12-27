# src/pages/package_booking_flow.py

from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from src.core.base_page import BasePage
from src.pages.ui.payment_flow import PaymentPage
from selenium.webdriver.common.action_chains import ActionChains
import time

class PackageBookingFlow(BasePage):
    """
    Page Object Model for Package Booking Flow
    Handles the complete package booking process from search to payment
    """
    
    # ===== LOCATORS =====
    # Navigation & Search
    PACKAGE_BUTTON = (By.XPATH, "//button[normalize-space()='Package']")
    TRIP_TYPE_DROPDOWN = (By.XPATH, "//div[@class='relative']//div[@data-sentry-element='Listbox']")
    GROUP_OPTION = (By.XPATH, "//span[normalize-space()='group']")
    COUNTRY_SELECTOR = (By.XPATH, "//div[contains(@class,'h-full relative')]")
    COUNTRY_INPUT = (By.XPATH, "//input[@placeholder='Enter country']")
    COUNTRY_SEARCH_RESULT = (By.XPATH, "//h6[contains(text(),'NIGERIA')]")
    TRAVEL_DATE_SELECTOR = (By.CSS_SELECTOR, "div[class='w-full flex items-center px-3.5 min-h-12 h-full py-2 rounded-md border border-gray-300 cursor-pointer justify-between']")
    SEARCH_PACKAGES_BUTTON = (By.CSS_SELECTOR, "body > div:nth-child(1) > div:nth-child(2) > div:nth-child(2) > div:nth-child(2) > form:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > button:nth-child(1)")

    # Package Selection
    VIEW_PACKAGE_BUTTON = (By.XPATH, "(//button[normalize-space()='View package'])[1]")
    PRICE_OPTION = (By.CSS_SELECTOR, "body > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2)")
    BOOK_RESERVATION_BUTTON = (By.CSS_SELECTOR, "body > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > button:nth-child(2)")

    # Booking Form
    FULL_NAME_INPUT = (By.NAME, "fullName")
    EMAIL_INPUT = (By.NAME, "email")
    PHONE_INPUT = (By.CSS_SELECTOR, "input[placeholder='Phone number']")
    PROCEED_TO_PAYMENT_BUTTON = (By.CSS_SELECTOR, "body > div:nth-child(29) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > footer:nth-child(4) > div:nth-child(1) > button:nth-child(1)")
    
    # Modal Locators
    MODAL_BACKGROUND = (By.CSS_SELECTOR, "div.fixed.inset-0.bg-black\\/60")
    MODAL_FULL_NAME_INPUT = (By.XPATH, "//input[contains(@placeholder,'Enter your full name')]")
    MODAL_EMAIL_INPUT = (By.XPATH, "//input[@placeholder='Enter your email address']")
    MODAL_TRAVEL_DATE_INPUT = (By.CSS_SELECTOR, "input[placeholder='Select a date ']")
    MODAL_PHONE_INPUT = (By.XPATH, "//input[@placeholder='Phone number']")
    MODAL_PROCEED_BUTTON = (By.XPATH, "//button[normalize-space()='Proceed to checkout']")
    
    # Booking Confirmation Modal
    CLOSE_MODAL_BUTTON = (By.XPATH, "//button[@aria-label='Close modal']")
    TERMS_CHECKBOX = (By.XPATH, "//input[@aria-label='Terms and policy']")
    PROCEED_TO_PAYMENT_BUTTON = (By.XPATH, "//button[normalize-space()='Proceed to payment']")

    def __init__(self, driver):
        """Initialize PackageBookingFlow with driver"""
        super().__init__(driver)

    # ===== SEARCH & NAVIGATION METHODS =====
    
    def click_package(self):
        """Click on Package button in navigation"""
        self.logger.info("Clicking Package button")
        try:
            click_btn = self.element.click(self.PACKAGE_BUTTON)
            self._last_interacted_element = click_btn
            return click_btn
        except Exception as e:
            self.logger.error(f"Failed to click Package button: {e}")
            raise

    def select_trip_type(self):
        """Select trip type as group"""
        self.logger.info("Selecting trip type as 'group'")
        trip_dropdown_btn = None
        group_option_btn = None

        try:
            # Wait for dropdown to be clickable
            trip_dropdown = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.TRIP_TYPE_DROPDOWN)
            )
            trip_dropdown.click()
            trip_dropdown_btn = trip_dropdown
            self.logger.info("Clicked trip type dropdown")
            time.sleep(2)

            # Wait for group option and click
            group_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.GROUP_OPTION)
            )
            group_option.click()
            group_option_btn = group_option
            self.logger.info("Trip type selected: group")
            time.sleep(2)

            return self

        except Exception as e:
            self.logger.error(f"Failed to select trip type: {e}")
            self._last_interacted_element = trip_dropdown_btn or group_option_btn
            raise

    def select_country(self, country_name):
        """Select country from dropdown"""
        self.logger.info(f"Selecting country: {country_name}")
        country_selector_btn = None
        country_input_btn = None
        country_result_btn = None

        try:
            # Step 1: Click country selector
            country_selector = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.COUNTRY_SELECTOR)
            )
            country_selector.click()
            country_selector_btn = country_selector
            self.logger.info("Clicked country selector")
            time.sleep(2)

            # Step 2: Wait for and click country input
            country_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.COUNTRY_INPUT)
            )
            country_input.click()
            country_input_btn = country_input
            self.logger.info("Clicked country input")
            time.sleep(1)

            # Step 3: Type country name
            country_input.clear()
            time.sleep(2)
            country_input.send_keys(country_name)
            self.logger.info(f"Typed country: {country_name}")
            time.sleep(2)

            # Step 4: Select from results with better waiting
            country_result = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.COUNTRY_SEARCH_RESULT)
            )
            country_result.click()
            country_result_btn = country_result
            self.logger.info(f"Country selected: {country_name}")
            time.sleep(2)

            return self

        except Exception as e:
            self.logger.error(f"Failed to select country {country_name}: {e}")
            self._last_interacted_element = country_selector_btn or country_input_btn or country_result_btn
            raise

    def select_travel_date(self):
        """Open travel date selector and pick a date"""
        self.logger.info("Opening travel date selector")
        travel_date_btn = None
        date_btn = None

        try:
            # Click to open date picker
            travel_date_btn = self.element.click(self.TRAVEL_DATE_SELECTOR)
            time.sleep(2)  # Wait for calendar to open

            # Find and click the first available future date
            available_dates = self.driver.find_elements(By.CSS_SELECTOR, "button:not([disabled])")
            for date in available_dates:
                if date.text.isdigit() and 1 <= int(date.text) <= 31:
                    if int(date.text) > 10:  # pick future date
                        date.click()
                        date_btn = date
                        self.logger.info(f"Selected travel date: {date.text}")
                        break

            self._last_interacted_element = date_btn or travel_date_btn
            time.sleep(2)
            return self

        except Exception as e:
            self._last_interacted_element = date_btn or travel_date_btn
            self.logger.error(f"Failed to select travel date: {e}")
            raise


    def search_packages(self):
        """Click search packages button"""
        self.logger.info("Clicking Search Packages button")
        try:
            search_btn = self.element.click(self.SEARCH_PACKAGES_BUTTON)
            self._last_interacted_element = search_btn
            return search_btn
        except Exception as e:
            self.logger.error(f"Failed to click Search Packages button: {e}")
            raise
    
    def is_search_session_initialized(self, search_term="packages", timeout=30):
        """Check if search session is properly initialized with configurable search term"""
        try:
            current_url = self.driver.current_url
            self.logger.info(f"Checking for '{search_term}' in {current_url} (waiting up to {timeout}s)...")

            WebDriverWait(self.driver, timeout).until(
                lambda driver: search_term in driver.current_url
            )

            current_url = self.driver.current_url
            self.logger.info(f"Search session initialized successfully - Found '{search_term}' in URL: {current_url}")
            return True

        except TimeoutException:
            current_url = self.driver.current_url
            self.logger.warning(f"'{search_term}' not found in URL after {timeout}s")
            self.logger.info(f"Current URL: {current_url}")
            return False
        except Exception as e:
            self.logger.error(f"Error checking search session: {e}")
            return False

    # ===== PACKAGE SELECTION METHODS =====

    def click_view_package(self):
        """Click on View Package button"""
        self.logger.info("Clicking View Package button")
        try:
            # Scroll further down (500 pixels past the element)
            self.javascript.execute_script(
                "arguments[0].scrollIntoView(true); window.scrollBy(0, 500);", 
                self.driver.find_element(*self.VIEW_PACKAGE_BUTTON)
            )
            time.sleep(1)
            click_view_package_btn = self.element.click(self.VIEW_PACKAGE_BUTTON)
            self._last_interacted_element = click_view_package_btn
            return click_view_package_btn
        except Exception as e:
            self.logger.error(f"Failed to click View Package button: {e}")
            raise
    
    def select_price_option(self):
        """Select price option with better click handling"""
        self.logger.info("Selecting price option")

        try:
            # Wait for the element to be present and visible
            price_option = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(self.PRICE_OPTION)
            )

            # Scroll to the element with more offset to ensure it's in view
            self.driver.execute_script("""
                arguments[0].scrollIntoView({
                    behavior: 'smooth',
                    block: 'center',
                    inline: 'center'
                });
            """, price_option)

            # Wait a bit for scroll to complete
            time.sleep(2)

            # Try JavaScript click first (bypasses overlay issues)
            self.logger.info("Attempting JavaScript click")
            self.driver.execute_script("arguments[0].click();", price_option)

            # Wait for selection to take effect
            time.sleep(3)

            self.logger.info("Price option selected successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to select price option: {e}")

            # Alternative: Try clicking via ActionChains
            try:
                self.logger.info("Trying ActionChains click")
                actions = ActionChains(self.driver)
                actions.move_to_element(price_option).click().perform()
                time.sleep(3)
                self.logger.info("Price option selected via ActionChains")
                return True
            except Exception as e2:
                self.logger.error(f"ActionChains also failed: {e2}")
                self._last_interacted_element = price_option
                return False

    # ===== BOOKING FLOW METHODS =====

    def handle_booking_flow(self):
        """Complete booking flow including modal handling"""
        self.logger.info("Starting complete booking flow")

        # Step 1: Click Book Reservation
        self.click_book_reservation()

        # Step 2: Fill modal form
        self.fill_booking_modal()
        
        # Step 3: Handle second modal (terms and conditions)
        self.handle_second_modal()

        # Step 4: Verify we're ready for payment (but don't proceed to payment gateway)
        self.verify_payment_ready()
        
    def handle_second_modal(self):
        """Handle the second modal with terms and conditions"""
        self.logger.info("Handling second modal with terms and conditions")
        close_btn = None
        terms_checkbox_btn = None
        
        try:
            # Wait for second modal to appear
            WebDriverWait(self.driver, 15).until(
                EC.visibility_of_element_located(self.CLOSE_MODAL_BUTTON)
            )
            self.logger.info("Second modal is visible")
    
            # Step 1: Click Close modal button (the 'X' button)
            self.logger.info("Clicking Close modal button")
            close_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.CLOSE_MODAL_BUTTON)
            )
            close_button.click()
            close_btn = close_button
            self.logger.info("Closed modal successfully")
            time.sleep(2)
    
            # Step 2: Wait for the page to stabilize after modal close
            self.logger.info("Waiting for page to stabilize after modal close")
            time.sleep(3)  # Increased wait for stability
    
            # Step 3: Scroll the Terms checkbox into view and ensure it's clickable
            self.logger.info("Scrolling Terms checkbox into view")
            terms_checkbox = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(self.TERMS_CHECKBOX)
            )
            
            # Scroll to the checkbox using JavaScript
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", terms_checkbox)
            self.logger.info("Scrolled Terms checkbox to center of view")
            time.sleep(2)
    
            # Step 4: Use JavaScript to click the checkbox (bypasses overlay issues)
            self.logger.info("Clicking Terms and Conditions checkbox using JavaScript")
            self.driver.execute_script("arguments[0].click();", terms_checkbox)
            self.logger.info("Terms and Conditions checkbox selected via JavaScript")
            time.sleep(2)
    
            # Step 5: Verify the checkbox is actually checked
            is_checked = self.driver.execute_script("return arguments[0].checked;", terms_checkbox)
            if is_checked:
                self.logger.info("✅ Terms and Conditions checkbox is successfully checked")
            else:
                self.logger.warning("Terms checkbox might not be checked, trying alternative approach")
                # Try clicking again with explicit wait
                terms_checkbox = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable(self.TERMS_CHECKBOX)
                )
                terms_checkbox.click()
                terms_checkbox_btn = terms_checkbox
                self.logger.info("Terms checkbox clicked via regular method")
    
        except Exception as e:
            self.logger.error(f"Error handling second modal: {str(e)}")
            self._last_interacted_element = close_btn or terms_checkbox_btn
            raise
        
    def verify_payment_ready(self):
        """Verify that the booking flow is complete and ready for payment"""
        self.logger.info("Verifying booking flow is complete and ready for payment")

        try:
            # Check that Proceed to Payment button is present and enabled
            proceed_payment_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(self.PROCEED_TO_PAYMENT_BUTTON)
            )

            if proceed_payment_button.is_enabled():
                self.logger.success("✅ Booking flow completed successfully - Ready for payment")
                return True
            else:
                self.logger.warning("Proceed to Payment button is not enabled")
                return False

        except Exception as e:
            self.logger.error(f"Error verifying payment readiness: {str(e)}")
            return False

    def click_book_reservation(self):
        """Clicks the Book Reservation button with better scrolling"""
        self.logger.info("Clicking Book Reservation button")

        try:
            book_reservation_button = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable(self.BOOK_RESERVATION_BUTTON)
            )

            # Better scrolling to ensure element is clickable
            self.driver.execute_script("""
                arguments[0].scrollIntoView({
                    behavior: 'smooth',
                    block: 'center',
                    inline: 'center'
                });
                window.scrollBy(0, -100);  // Adjust for any fixed headers
            """, book_reservation_button)

            time.sleep(2)  # Wait for scroll to complete

            # Try JavaScript click first
            self.driver.execute_script("arguments[0].click();", book_reservation_button)

            self.logger.info("Book Reservation button clicked successfully")

        except Exception as e:
            self.logger.error(f"Failed to click Book Reservation: {str(e)}")
            raise

    def fill_booking_modal(self):
        """Fills out the booking modal form with test data"""
        self.logger.info("Filling booking modal form")

        # Wait for modal to be fully loaded
        WebDriverWait(self.driver, 15).until(
            EC.visibility_of_element_located(self.MODAL_BACKGROUND)
        )

        # Wait for form content to be loaded
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(self.MODAL_FULL_NAME_INPUT)
        )

        self.logger.info("Booking modal is visible, filling form...")

        # Test data
        test_data = {
            "full_name": "GEO Bot",
            "email": "geo.qa.bot@gmail.com", 
            "phone": "1234567890",
            "travel_date": "31/12/2025"
        }
        proceed_btn = None

        try:
            # Full Name
            full_name_field = self.driver.find_element(*self.MODAL_FULL_NAME_INPUT)
            full_name_field.clear()
            full_name_field.send_keys(test_data["full_name"])
            self.logger.info(f"Filled full name: {test_data['full_name']}")

            # Email Address
            email_field = self.driver.find_element(*self.MODAL_EMAIL_INPUT)
            email_field.clear()
            email_field.send_keys(test_data["email"])
            self.logger.info(f"Filled email: {test_data['email']}")
            
            # Travel Date - Use calendar selection instead of direct input
            self.logger.info("Selecting travel date from calendar")
            travel_date_field = self.driver.find_elements(*self.MODAL_TRAVEL_DATE_INPUT)
            if travel_date_field and travel_date_field[0].is_displayed():
                self.logger.info("Travel date field is visible")
                travel_date_field[0].click()
                time.sleep(2)
                # Select a date from the calendar popup
                self.select_date_from_calendar(test_data["travel_date"])
                time.sleep(2)
                self.logger.info("Clicked travel date field - waiting for calendar to open")


            # Phone Number
            phone_field = self.driver.find_element(*self.MODAL_PHONE_INPUT)
            phone_field.clear()
            phone_field.send_keys(test_data["phone"])
            self.logger.info(f"Filled phone: {test_data['phone']}")

            # Small delay to ensure all fields are properly filled
            time.sleep(2)
            
            # Wait for Proceed button to become enabled
            self.wait_for_proceed_button_enabled()

            # Click Proceed to Checkout
            proceed_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.MODAL_PROCEED_BUTTON)
            )
            proceed_button.click()
            proceed_btn = proceed_button
            self.logger.info("Clicked 'Proceed to checkout'")

        except Exception as e:
            self.logger.error(f"Error filling booking modal: {str(e)}")
            self._last_interacted_element = proceed_btn
            raise
        
    def select_date_from_calendar(self, date_string):
        """
        Select date from calendar popup
        Date format: "05/11/2025" (day/month/year)
        """
        self.logger.info(f"Selecting date from calendar: {date_string}")

        try:
            # Parse the date
            day, month, year = date_string.split('/')

            # Wait for calendar to be visible
            calendar_popup = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "[role='dialog']"))
            )
            self.logger.info("Calendar popup is visible")

            # Try to find and click the specific date
            # Look for the day number in the calendar
            date_cell_xpath = f"//button[text()='{int(day)}' and not(@disabled)]"

            date_cell = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, date_cell_xpath))
            )

            date_cell.click()
            self.logger.info(f"Selected date: {date_string}")
            time.sleep(2)

        except TimeoutException:
            self.logger.warning("Could not find specific date cell, trying alternative approach")

            # Alternative: Click today's date or any available date
            available_dates = self.driver.find_elements(
                By.CSS_SELECTOR, "button:not([disabled])"
            )

            for date_element in available_dates:
                if date_element.text.isdigit() and 1 <= int(date_element.text) <= 31:
                    date_element.click()
                    self.logger.info(f"Selected available date: {date_element.text}")
                    time.sleep(2)
                    break

    def wait_for_proceed_button_enabled(self, timeout=10):
        """Waits for the Proceed to checkout button to become enabled"""
        self.logger.info("Waiting for Proceed button to become enabled...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                proceed_button = self.driver.find_element(*self.MODAL_PROCEED_BUTTON)
                
                # Check if button is enabled (not disabled)
                if proceed_button.is_enabled():
                    self.logger.info("Proceed button is now enabled")
                    return True
                
                self.logger.info("Proceed button still disabled, waiting...")
                time.sleep(1)
                
            except Exception as e:
                self.logger.warning(f"Error checking button state: {e}")
                time.sleep(1)
        
        self.logger.error("Proceed button did not become enabled within timeout")
        return False

    def wait_for_booking_confirmation(self):
        """Waits for booking confirmation or next page load"""
        self.logger.info("Waiting for booking confirmation...")

        try:
            # Wait for either checkout page or confirmation
            WebDriverWait(self.driver, 30).until(
                lambda driver: "checkout" in driver.current_url.lower() or 
                              "confirmation" in driver.current_url.lower() or
                              "success" in driver.current_url.lower()
            )
            self.logger.info("Successfully navigated to next booking step")
        except TimeoutException:
            self.logger.info("Continuing with booking flow...")
            
    def complete_booking_with_payment(self):
        """Complete booking including payment flow"""
        self.logger.info("=== Completing Booking with Payment ===")

        # Initialize payment page and complete payment
        payment_page = PaymentPage(self.driver)

        # Click proceed to payment
        payment_page.proceed_to_payment()

        # Complete Flutterwave payment
        payment_success = payment_page.complete_payment_flow()

        if payment_success:
            self.logger.success("🎉 Package booking with payment completed successfully!")
            return True
        else:
            self.logger.error("❌ Payment flow failed")
            return False
        
    def wait_for_booking_modal(self, timeout=10):
        """Wait until booking modal is visible"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.MODAL_BACKGROUND)
            )
            return True
        except TimeoutException:
            return False
