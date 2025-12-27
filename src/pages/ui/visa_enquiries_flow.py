from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from src.core.base_page import BasePage
from src.utils.logger import GeoLogger
from datetime import datetime, timedelta
import time
import random
from selenium.common.exceptions import StaleElementReferenceException

    

from utils.page_info import PageInfoUtils


class VisaPage(BasePage):
    """Page Object for Visa Enquiries functionality"""
    
    def __init__(self, driver):
        super().__init__(driver)
    
    # ========== LOCATORS ==========
    # Menu & Navigation
    VISA_MENU_ITEM = (By.XPATH, "//a[contains(@class, 'Visa') or contains(text(), 'Visa')]")
    GET_STARTED_BUTTON = (By.XPATH, "//button[normalize-space()='Get Started']")
    
    # Personal Information
    FIRST_NAME_INPUT = (By.CSS_SELECTOR, "input[placeholder='Enter your first name']")
    LAST_NAME_INPUT = (By.CSS_SELECTOR, "input[placeholder='Enter your last name']")
    EMAIL_INPUT = (By.CSS_SELECTOR, "input[placeholder='Enter your email']")
    PHONE_INPUT = (By.CSS_SELECTOR, "input[placeholder='Phone number']")
    
    # Dropdowns
    COUNTRY_ORIGIN_DROPDOWN = (By.XPATH, "//fieldset[.//*[contains(text(), 'country of origin')]]//button")
    COUNTRY_OPTION_TEMPLATE = (By.XPATH, "//div[@role='option' and contains(., '{}')]")
    
    PASSPORT_AVAILABILITY_DROPDOWN = (By.XPATH, "//fieldset[.//*[contains(text(), 'passport availability')]]//button")
    PASSPORT_OPTION_TEMPLATE = (By.XPATH, "//span[text()='{}' and @class]")
    
    TRAVEL_DATE_INPUT = (By.CSS_SELECTOR, "body > div:nth-child(1) > main:nth-child(2) > section:nth-child(1) > div:nth-child(1) > div:nth-child(2) > section:nth-child(1) > div:nth-child(2) > form:nth-child(2) > div:nth-child(4) > fieldset:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1)")
    
    DESTINATION_COUNTRY_DROPDOWN = (By.XPATH, "//fieldset[.//*[contains(text(), 'destination country')]]//button")
    DESTINATION_OPTION_TEMPLATE = (By.XPATH, "//span[text()='{}' and ancestor::div[@role='listbox']]")
    
    VISA_TYPE_DROPDOWN = (By.XPATH, "//fieldset[.//*[contains(text(), 'visa type')]]//button")
    VISA_TYPE_OPTION_TEMPLATE = (By.XPATH, "//span[text()='{}' and @class]")
    
    # Message
    MESSAGE_TEXTAREA = (By.CSS_SELECTOR, "textarea[placeholder*='Write your message']")
    
    # Action Buttons
    SUBMIT_APPLICATION_BTN = (By.XPATH, "//button[contains(text(), 'Submit application')]")
    CANCEL_BTN = (By.XPATH, "//button[contains(text(), 'Cancel')]")
    
    # Success/Confirmation
    SUCCESS_MESSAGE = (By.CSS_SELECTOR, "[class*='success'], [class*='Success'], .text-green-500")
    CONFIRMATION_MODAL = (By.CSS_SELECTOR, "[role='dialog'], .modal, .popup")
    FORM_CONTAINER = (By.CSS_SELECTOR, "section.bg-white.rounded-2xl, form")
    
    # Page Elements
    PAGE_TITLE = (By.XPATH, "//h1[contains(text(), 'Visa')]")
    FORM_SECTION = (By.CLASS_NAME, "mt-5")
    
    
    def get_future_date(self, days=1):
        return (datetime.today() + timedelta(days=days)).strftime("%d")
    
    # ========== PAGE METHODS ==========
    
    def open(self, base_url):
        """Open the application and navigate to Visa page"""
        self.logger.info("Opening application homepage")
        self.driver.get(base_url)
        return self
    
    def navigate_to_visa(self):
        """Navigate to Visa page from homepage"""
        self.logger.info("Navigating to Visa page")
        visa_menu_btn = None
        try:
            visa_menu = self.waiter.wait_for_clickable(self.VISA_MENU_ITEM, timeout=15)
            visa_menu.click()
            visa_menu_btn = visa_menu
            self.waiter.wait_for_present(self.PAGE_TITLE, timeout=15)
            assert "visa" in self.driver.current_url.lower(), "URL should contain 'visa'"
            
            self.logger.info("Successfully navigated to Visa page")
            return self
        except Exception as e:
            self._last_interacted_element = visa_menu_btn
            self.logger.error(f"Failed to navigate to Visa page: {e}")
            raise
    
    def click_get_started(self, retries=3, delay=2):
        """Click Get Started button to open visa application form with retry on failure"""
        self.logger.info("Clicking 'Get Started' button")

        attempt = 0
        get_started_btn = None
        while attempt < retries:
            try:
                get_started_btn = self.waiter.wait_for_clickable(self.GET_STARTED_BUTTON, timeout=30)
                # Scroll to element
                self.javascript.scroll_to_element(get_started_btn)

                get_started_btn.click()
                get_started_btn = get_started_btn  # store for last interacted element
                self.waiter.wait_for_present(self.FORM_SECTION, timeout=10)

                self.logger.info("Visa application form opened")
                return self  # success, exit method

            except Exception as e:
                attempt += 1
                self._last_interacted_element = get_started_btn
                self.logger.warning(f"Attempt {attempt} failed: {e}")
                if attempt < retries:
                    self.logger.info(f"Retrying to click 'Get Started' button (Attempt {attempt + 1})...")
                    # Refresh the page
                    self.driver.refresh()
                    self.waiter.wait_for_clickable(self.GET_STARTED_BUTTON, timeout=30)
                    time.sleep(delay)  # wait a bit before retrying

        # If we reach here, all retries failed
        self.logger.error(f"Failed to click Get Started button after {retries} attempts")

    
    def fill_personal_details(self, first_name, last_name, email, phone, timeout=30):
        """Fill personal information section"""
        self.logger.info("Filling personal details")
        
        try:
            # First Name
            self.element.type(self.FIRST_NAME_INPUT, "QA Bot", timeout)
            
            # Last Name
            self.element.type(self.LAST_NAME_INPUT, "GEO", timeout)
            
            # Email
            self.element.type(self.EMAIL_INPUT, "geo.qa.bot@gmail.com", timeout=10)

            # Phone
            self.element.type(self.PHONE_INPUT, "07080702920", timeout=10)
            
            self.logger.info("Personal details filled successfully")
            return self
            
        except Exception as e:
            self.logger.error(f"Failed to fill personal details: {e}")
            raise
    
    def select_country_origin(self, country):
        """Select country of origin from dropdown"""
        self.logger.info(f"Selecting country of origin: {country}")
        dropdown_btn = None
        option_btn = None
        
        try:
            # Open dropdown
            dropdown = self.waiter.wait_for_clickable(self.COUNTRY_ORIGIN_DROPDOWN, timeout=10)
            self.javascript.scroll_to_element(dropdown)
            dropdown.click()
            dropdown_btn = dropdown
            time.sleep(1)
            
            # Select option
            country_locator = (self.COUNTRY_OPTION_TEMPLATE[0], 
                             self.COUNTRY_OPTION_TEMPLATE[1].format(country.lower()))
            option = self.waiter.wait_for_clickable(country_locator)
            option.click()
            option_btn = option
            
            self.logger.info(f"Country of origin '{country}' selected")
            return self
            
        except Exception as e:
            self._last_interacted_element = dropdown_btn or option_btn
            self.logger.error(f"Failed to select country of origin '{country}': {e}")
            raise
    
    def select_passport_availability(self, option="yes"):
        """Select passport availability option"""
        self.logger.info(f"Selecting passport availability: {option}")
        dropdown_btn = None
        option_element_btn = None
        
        try:
            # Open dropdown
            dropdown = self.waiter.wait_for_clickable(self.PASSPORT_AVAILABILITY_DROPDOWN, timeout=10)
            # self.javascript.scroll_to_element(dropdown)
            dropdown.click()
            dropdown_btn = dropdown
            time.sleep(1)
            
            # Select option
            passport_locator = (self.PASSPORT_OPTION_TEMPLATE[0],
                              self.PASSPORT_OPTION_TEMPLATE[1].format(option))
            option_element = self.waiter.wait_for_clickable(passport_locator)
            option_element.click()
            option_element_btn = option_element
            
            self.logger.info(f"Passport availability '{option}' selected")
            return self
            
        except Exception as e:
            self._last_interacted_element = dropdown_btn or option_element_btn
            self.logger.error(f"Failed to select passport availability '{option}': {e}")
            raise
    
    def select_travel_date(self, date_text=None):
        """Select travel date from date picker"""
        self.logger.info("Selecting travel date")
        date_text = self.get_future_date(1) if date_text is None else date_text
        date_input_btn = None
        
        try:
            date_input = self.waiter.wait_for_clickable(self.TRAVEL_DATE_INPUT)
            self.javascript.scroll_to_element(date_input)
            date_input.click()
            date_input_btn = date_input
            time.sleep(2)
            
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
            
            self.logger.info("Date picker opened successfully")
            return self
            
        except Exception as e:
            self._last_interacted_element = date_input_btn
            self.logger.error(f"Failed to select travel date: {e}")
            raise

    def select_destination_country(self):
        """Select any destination country from the dropdown"""
        self.logger.info("Selecting any destination country")
        dropdown_btn = None
        chosen_option_btn = None

        try:
            dropdown = self.waiter.wait_for_clickable(self.DESTINATION_COUNTRY_DROPDOWN, timeout=10)
            self.javascript.scroll_to_element(dropdown)
            dropdown.click()
            dropdown_btn = dropdown

            # Wait until listbox options are actually visible
            WebDriverWait(self.driver, 10).until(
                lambda d: len(d.find_elements(By.XPATH, "//div[@role='listbox']//span")) > 0
            )

            options = self.driver.find_elements(By.XPATH, "//div[@role='listbox']//span")
            chosen_option = random.choice(options)
            option_text = chosen_option.text
            self.logger.info(f"Auto-selecting destination: {option_text}")

            for _ in range(3):
                try:
                    self.javascript.scroll_to_element(chosen_option)
                    chosen_option.click()
                    chosen_option_btn = chosen_option
                    return self
                except StaleElementReferenceException:
                    time.sleep(1)
                    options = self.driver.find_elements(By.XPATH, "//div[@role='listbox']//span")
                    chosen_option = random.choice(options)

            raise Exception("Failed to select destination after retries")

        except Exception as e:
            self._last_interacted_element = dropdown_btn or chosen_option_btn
            self.logger.error(f"Failed to select destination: {e}")
            raise


    def select_visa_type(self):
        """Select any visa type from the dropdown"""
        self.logger.info("Selecting any visa type")
        dropdown_btn = None
        chosen_option_btn = None

        try:
            dropdown = self.waiter.wait_for_clickable(self.VISA_TYPE_DROPDOWN, timeout=10)
            self.javascript.scroll_to_element(dropdown)
            dropdown.click()
            dropdown_btn = dropdown

            WebDriverWait(self.driver, 10).until(
                lambda d: len(d.find_elements(By.XPATH, "//div[@role='listbox']//span")) > 0
            )

            options = self.driver.find_elements(By.XPATH, "//div[@role='listbox']//span")
            chosen_option = random.choice(options)
            option_text = chosen_option.text
            self.logger.info(f"Auto-selecting visa type: {option_text}")

            for _ in range(3):
                try:
                    self.javascript.scroll_to_element(chosen_option)
                    chosen_option.click()
                    chosen_option_btn = chosen_option
                    return self
                except StaleElementReferenceException:
                    time.sleep(1)
                    options = self.driver.find_elements(By.XPATH, "//div[@role='listbox']//span")
                    chosen_option = random.choice(options)

            raise Exception("Failed to select visa type after retries")

        except Exception as e:
            self._last_interacted_element = dropdown_btn or chosen_option_btn
            self.logger.error(f"Failed to select visa type: {e}")
            raise



    
    def fill_message(self, message):
        """Fill additional message"""
        self.logger.info("Filling additional message")
        
        try:
            textarea = self.waiter.wait_for_visible(self.MESSAGE_TEXTAREA, timeout=10)
            textarea.send_keys(message)
            
            self.logger.info("Message filled successfully")
            return self
            
        except Exception as e:
            self.logger.error(f"Failed to fill message: {e}")
            raise
    
    def submit_application(self):
        """Submit the visa application"""
        self.logger.info("Submitting visa application")
        submit_btn = None
        
        try:
            submit_button = self.waiter.wait_for_clickable(self.SUBMIT_APPLICATION_BTN, timeout=10)
            submit_button.click()
            submit_btn = submit_button
            
            # Wait for some response
            time.sleep(2)
            self.logger.info("Visa application submitted")
            return self
            
        except Exception as e:
            self._last_interacted_element = submit_btn
            self.logger.error(f"Failed to submit application: {e}")
            raise
    
    def cancel_application(self):
        """Cancel the visa application"""
        self.logger.info("Cancelling visa application")
        cancel_btn = None
        
        try:
            cancel_button = self.waiter.wait_for_clickable(self.CANCEL_BTN, timeout=10)
            cancel_button.click()
            cancel_btn = cancel_button
            
            self.logger.info("Visa application cancelled")
            return self
            
        except Exception as e:
            self._last_interacted_element = cancel_btn
            self.logger.error(f"Failed to cancel application: {e}")
            raise
    
    def is_form_visible(self):
        """Check if visa application form is visible"""
        try:
            form = self.pageinfo.find_element(*self.FORM_SECTION)
            return form.is_displayed()
        except:
            return False
    
    def is_success_message_displayed(self):
        """Check if success message is displayed after submission"""
        try:
            success_element = self.waiter.wait_for_visible(self.SUCCESS_MESSAGE, timeout=10)
            return success_element.is_displayed()
        except:
            return False
    
    def get_form_fields_status(self):
        """Get status of all form fields"""
        fields_status = {}
        
        field_locators = [
            ("first_name", self.FIRST_NAME_INPUT),
            ("last_name", self.LAST_NAME_INPUT),
            ("email", self.EMAIL_INPUT),
            ("phone", self.PHONE_INPUT),
            ("message", self.MESSAGE_TEXTAREA)
        ]
        
        for field_name, locator in field_locators:
            try:
                element = self.driver.find_element(*locator)
                fields_status[field_name] = {
                    "visible": element.is_displayed(),
                    "enabled": element.is_enabled(),
                    "value": element.get_attribute("value") or ""
                }
            except:
                fields_status[field_name] = {
                    "visible": False,
                    "enabled": False,
                    "value": ""
                }
        
        return fields_status
    
    def wait_for_form_load(self, timeout=15, max_retries=2):
        """Wait for visa application form to load"""
        self.logger.info("Waiting for visa form to load")
        
        for attempt in range(max_retries):
            try:
                self.waiter.wait_for_present(self.FORM_SECTION, timeout=10)
                self.waiter.wait_for_clickable(self.FIRST_NAME_INPUT, timeout=10)
                self.logger.info("Visa form loaded successfully")
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Form load attempt {attempt + 1} failed, retrying...")
                    time.sleep(2)
                else:
                    self.logger.error(f"Visa form failed to load after {max_retries} attempts: {e}")
                    return False