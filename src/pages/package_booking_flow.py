# src/pages/package_booking_flow.py

from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from src.core.base_page import BasePage
import time

class PackageBookingFlow(BasePage):
    """
    
    """
    
    # Locators
    PACKAGE_BUTTON = (By.XPATH, "//button[normalize-space()='Package']")
    
    # Locators
    TRIP_TYPE_DROPDOWN = (By.XPATH, "//div[@class='relative']//div[@data-sentry-element='Listbox']")
    GROUP_OPTION = (By.XPATH, "//span[normalize-space()='group']")
    COUNTRY_SELECTOR = (By.XPATH, "//div[contains(@class,'h-full relative')]")
    COUNTRY_INPUT = (By.XPATH, "//input[@placeholder='Enter country']")
    COUNTRY_SEARCH_RESULT = (By.XPATH, "//h6[contains(text(),'NIGERIA')]")
    TRAVEL_DATE_SELECTOR = (By.CSS_SELECTOR, "div[class='w-full flex items-center px-3.5 min-h-12 h-full py-2 rounded-md border border-gray-300 cursor-pointer justify-between']")
    SEARCH_PACKAGES_BUTTON = (By.CSS_SELECTOR, "body > div:nth-child(2) > div:nth-child(2) > div:nth-child(2) > div:nth-child(2) > form:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > button:nth-child(1)")

    VIEW_PACKAGE_BUTTON = (By.CSS_SELECTOR, "body > main:nth-child(2) > div:nth-child(3) > section:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(2) > section:nth-child(1) > div:nth-child(2) > button:nth-child(7)")

    PRICE_OPTION = (By.CSS_SELECTOR, "body > div:nth-child(2) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2)")
    BOOK_RESERVATION_BUTTON = (By.CSS_SELECTOR, "body > div:nth-child(2) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > button:nth-child(2)")

    FULL_NAME_INPUT = (By.NAME, "fullName")
    EMAIL_INPUT = (By.NAME, "email")
    PHONE_INPUT = (By.CSS_SELECTOR, "input[placeholder='Phone number']")
    PROCEED_TO_PAYMENT_BUTTON = (By.CSS_SELECTOR, "body > div:nth-child(29) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > footer:nth-child(4) > div:nth-child(1) > button:nth-child(1)")

    
    def __init__(self, driver):
        super().__init__(driver)


    def select_trip_type(self):
        """Select trip type as group"""
        self.logger.info("Selecting trip type as 'group'")
        self.element.click(self.TRIP_TYPE_DROPDOWN)
        self.element.click(self.GROUP_OPTION)
        self.logger.info("Trip type selected: group")
        return self

    def select_country(self, country_code):
        """Select country from dropdown"""
        self.logger.info(f"Selecting country: {country_code}")
        self.element.click(self.COUNTRY_SELECTOR)
        self.element.click(self.COUNTRY_INPUT)

        # Enter country code and select from results
        self.element.type(self.COUNTRY_INPUT, country_code)
        self.element.click(self.COUNTRY_SEARCH_RESULT)
        self.logger.info(f"Country selected: {country_code}")
        return self

    def select_travel_date(self):
        """Open travel date selector and pick a date"""
        # Open the calendar
        self.logger.info("Opening travel date selector")
        self.element.click(self.TRAVEL_DATE_SELECTOR)
        time.sleep(2)  # Wait for calendar to open

        # Find and click the first available future date
        available_dates = self.driver.find_elements(
            By.CSS_SELECTOR, "button:not([disabled])"
        )
        for date in available_dates:
            if date.text.isdigit() and 1 <= int(date.text) <= 31:
                # Pick a date in the future (assuming today is lower number)
                if int(date.text) > 10:
                    date.click()
                    self.logger.info(f"Selected travel date: {date.text}")
                    break

        time.sleep(2)  # Wait for date selection to process
        return self
    
    def is_search_session_initialized(self, search_term="packages", timeout=30):
        """Check if search session is properly initialized with configurable search term"""
        try:
            current_url = self.driver.current_url
            self.logger.info(f"Checking for '{search_term}' in {current_url} (waiting up to {timeout}s)...")

            WebDriverWait(self.driver, timeout).until(
                lambda driver: search_term in driver.current_url
            )

            current_url = self.driver.current_url
            self.logger.info(f"✅ Found '{search_term}' in URL: {current_url}")
            return True

        except TimeoutException:
            current_url = self.driver.current_url
            self.logger.warning(f"'{search_term}' not found in URL after {timeout}s")
            self.logger.info(f"   Current URL: {current_url}")
            return False
        except Exception as e:
            self.logger.error(f"Error checking search session: {e}")
            return False

    def search_packages(self):
        """Click search packages button"""
        self.logger.info("Clicking Search Packages button")
        return self.element.click(self.SEARCH_PACKAGES_BUTTON)

    def click_package(self):
        """Click on Package button"""
        self.logger.info("Clicking Package button")
        return self.element.click(self.PACKAGE_BUTTON)

    def click_view_package(self):
        """Click on View Package button"""
        self.logger.info("Clicking View Package button")
        # Scroll further down (300 pixels past the element)
        self.javascript.execute_script(
            "arguments[0].scrollIntoView(true); window.scrollBy(0, 300);", 
            self.driver.find_element(*self.VIEW_PACKAGE_BUTTON)
        )
        time.sleep(1)
        return self.element.click(self.VIEW_PACKAGE_BUTTON)

    def select_price_option(self):
        """Select price option"""
        self.logger.info("Selecting price option")
        self.javascript.execute_script("arguments[0].scrollIntoView(true);", self.driver.find_element(*self.BOOK_RESERVATION_BUTTON))
        return self.element.click(self.PRICE_OPTION)

    def click_book_reservation(self):
        """Click Book Reservation button using JavaScript"""
        self.logger.info("Clicking Book Reservation button")
        element = self.driver.find_element(*self.BOOK_RESERVATION_BUTTON)
        self.driver.execute_script("arguments[0].click();", element)
        element.click()
        return self

    def fill_booking_form(self, full_name, email, phone):
        """Fill out the booking form in modal"""
        self.logger.info("Filling out booking form in modal")
        
        # Wait for modal to load and target it directly
        time.sleep(2)
        
        try:
            # Find the modal container
            modal = self.driver.find_element(By.CSS_SELECTOR, "#headlessui-dialog-panel-«r3j»")
            self.logger.info("Modal found successfully")
            
            # Find form fields within the modal
            name_field = modal.find_element(By.XPATH, ".//input[contains(@placeholder,'Enter your full name')]")
            email_field = modal.find_element(By.XPATH, ".//input[@placeholder='Enter your email address']")
            phone_field = modal.find_element(By.XPATH, ".//input[@placeholder='Phone number']")
            
            self.logger.info("All form fields found within modal")
            
            # Fill the form
            name_field.clear()
            name_field.send_keys(full_name)
            self.logger.info("Full name filled")
            
            email_field.clear()
            email_field.send_keys(email)
            self.logger.info("Email filled")

            phone_field.clear()
            phone_field.send_keys(phone)
            self.logger.info("Phone filled")

        except Exception as e:
            self.logger.error(f"Failed to fill form in modal: {e}")
            # Fallback: try without modal context
            try:
                self.logger.info("Trying fallback without modal context...")
                name_field = self.driver.find_element(By.XPATH, "//input[contains(@placeholder,'Enter your full name')]")
                name_field.send_keys(full_name)
                self.logger.info("Full name filled (fallback)")
            except:
                self.logger.error("Fallback also failed")

        return self