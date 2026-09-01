"""
src/pages/ui/visa_enquiries_flow.py

Page Object for the Geo Travel Visa Enquiries flow.

Covers the full flow end to end:
    1. Navigation        - click "Visa" in the nav menu and click
                            "Get Started" to open the application form
                            (with retry-on-failure and a page refresh
                            between attempts).
    2. Personal details   - fill first/last name, email, and phone with
                             fixed test data.
    3. Dropdown selections - country of origin, passport availability,
                             destination country (random), and visa type
                             (random).
    4. Travel date         - pick a day from the date picker.
    5. Message & submit    - fill the additional-message textarea, then
                             submit or cancel the application.

Tests typically chain ``navigate_to_visa()`` -> ``click_get_started()`` ->
``fill_personal_details(...)`` -> the various ``select_*`` dropdown
methods -> ``select_travel_date()`` -> ``fill_message(...)`` ->
``submit_application()``.
"""

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


class VisaPage(BasePage):
    """Page Object for the Visa Enquiries application form.

    Locators are grouped by section: menu/navigation, personal
    information fields, dropdowns (country of origin, passport
    availability, destination country, visa type - each paired with a
    ``*_OPTION_TEMPLATE`` locator that gets ``.format()``-ed with the
    option text to click), the travel date input, the message textarea,
    action buttons, and success/confirmation elements. Self-contained -
    no coupling to other page objects.

    ``self.pageinfo`` (a ``PageInfoUtils`` instance) comes from
    ``BasePage``.
    """

    def __init__(self, driver):
        """Initialize the page object.

        Args:
            driver (WebDriver): Active Selenium WebDriver instance, passed
                through to ``BasePage``.
        """
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
    
    # TRAVEL_DATE_INPUT = (By.CSS_SELECTOR, "body > div:nth-child(1) > main:nth-child(2) > section:nth-child(1) > div:nth-child(1) > div:nth-child(2) > section:nth-child(1) > div:nth-child(2) > form:nth-child(2) > div:nth-child(4) > fieldset:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1)")
    TRAVEL_DATE_INPUT = (By.XPATH, "(//div[@class='flex items-center w-full px-3 py-1 text-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium focus-within:outline-none focus-within:ring-[1.5px] focus-within:ring-mainblue disabled:cursor-not-allowed disabled:opacity-50 border border-gray-300/70 rounded h-11 bg-white'])[1]")
    
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
        """Get the day-of-month (as a zero-padded string) N days from today.

        Args:
            days (int): Number of days ahead of today. Defaults to 1.

        Returns:
            str: Two-digit day-of-month, e.g. "05". Note this only
                returns the day, not the full date - it doesn't roll over
                month/year boundaries, so it's only meaningful when the
                date picker is already showing the current/target month.
        """
        return (datetime.today() + timedelta(days=days)).strftime("%d")

    # ========== PAGE METHODS ==========

    def open(self, base_url):
        """Open the application homepage directly via ``driver.get``.

        Args:
            base_url (str): Full URL of the homepage to load.

        Returns:
            VisaPage: ``self``, for method chaining.
        """
        self.logger.info("Opening application homepage")
        self.driver.get(base_url)
        return self

    def navigate_to_visa(self):
        """Click "Visa" in the nav menu and verify the Visa page loaded.

        Returns:
            VisaPage: ``self``, for method chaining.

        Raises:
            AssertionError: If the URL doesn't contain "visa" after
                navigating.
            Exception: Re-raised for any other navigation failure. The
                clicked nav element is stashed on
                ``self._last_interacted_element`` for debugging.
        """
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
        """Click "Get Started" to open the visa application form, retrying on failure.

        On failure, refreshes the page before the next attempt - works
        around occasional cases where the button is present but not yet
        interactive after page load.

        Args:
            retries (int): Max number of attempts. Defaults to 3.
            delay (int): Seconds to wait between retries. Defaults to 2.

        Returns:
            VisaPage: ``self``, for method chaining.

        Raises:
            Exception: The last attempt's exception, if every retry
                failed.
        """
        self.logger.info("Clicking 'Get Started' button")

        attempt = 0
        get_started_btn = None
        last_exception = None
        while attempt < retries:
            try:
                get_started_btn = self.waiter.wait_for_clickable(self.GET_STARTED_BUTTON, timeout=30)
                # Scroll to element
                self.javascript.scroll_to_element(get_started_btn)

                get_started_btn.click()
                self._last_interacted_element = get_started_btn
                self.waiter.wait_for_present(self.FORM_SECTION, timeout=10)

                self.logger.info("Visa application form opened")
                return self  # success, exit method

            except Exception as e:
                attempt += 1
                last_exception = e
                self._last_interacted_element = get_started_btn
                self.logger.warning(f"Attempt {attempt} failed: {e}")
                if attempt < retries:
                    self.logger.info(f"Retrying to click 'Get Started' button (Attempt {attempt + 1})...")
                    # Refresh the page
                    self.driver.refresh()
                    self.waiter.wait_for_clickable(self.GET_STARTED_BUTTON, timeout=30)
                    time.sleep(delay)  # wait a bit before retrying

        # All retries failed - raise rather than silently returning None,
        # so a chained call fails clearly instead of with an AttributeError.
        self.logger.error(f"Failed to click Get Started button after {retries} attempts")
        raise last_exception

    
    def fill_personal_details(self, first_name, last_name, email, phone, timeout=30):
        """Fill the personal information section (first/last name, email, phone).

        Args:
            first_name (str): First name to enter.
            last_name (str): Last name to enter.
            email (str): Email address to enter.
            phone (str): Phone number to enter.
            timeout (int): Seconds to wait for the first/last name fields
                specifically (the email/phone fields use a fixed 10s
                regardless of this value). Defaults to 30.

        Returns:
            VisaPage: ``self``, for method chaining.

        Raises:
            Exception: Re-raised if any field can't be filled.
        """
        self.logger.info("Filling personal details")

        try:
            # First Name
            self.element.type(self.FIRST_NAME_INPUT, first_name, timeout)

            # Last Name
            self.element.type(self.LAST_NAME_INPUT, last_name, timeout)

            # Email
            self.element.type(self.EMAIL_INPUT, email, timeout=10)

            # Phone
            self.element.type(self.PHONE_INPUT, phone, timeout=10)

            self.logger.info("Personal details filled successfully")
            return self

        except Exception as e:
            self.logger.error(f"Failed to fill personal details: {e}")
            raise
    
    def select_country_origin(self, country):
        """Open the country-of-origin dropdown and select the given country.

        Matches the option via ``COUNTRY_OPTION_TEMPLATE`` formatted with
        ``country.lower()`` - this assumes the option text in the DOM is
        itself lowercase (a pattern used consistently elsewhere in this
        app's dropdowns, e.g. flight_booking_flow.py's literal 'nigeria'
        / 'mr.' / 'male' option text).

        Args:
            country (str): Country name to select (e.g. "Nigeria").

        Returns:
            VisaPage: ``self``, for method chaining.

        Raises:
            Exception: Re-raised if the dropdown or matching option can't
                be found/clicked. The element in progress at failure time
                is stashed on ``self._last_interacted_element``.
        """
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
        """Open the passport-availability dropdown and select an option.

        Args:
            option (str): Option value to select, matched via
                ``PASSPORT_OPTION_TEMPLATE`` (e.g. "yes"/"no"). Defaults
                to "yes".

        Returns:
            VisaPage: ``self``, for method chaining.

        Raises:
            Exception: Re-raised if the dropdown or matching option can't
                be found/clicked.
        """
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
        """Open the date picker and click the target day-of-month.

        Tries to click the day-of-month button matching ``date_text``
        (or ``get_future_date(1)`` when not given) first; if that exact
        day isn't found among the enabled buttons (e.g. it's disabled,
        or the calendar isn't showing the expected month), falls back
        to the first enabled day greater than 10 as a "safely in the
        future" heuristic.

        Args:
            date_text (str, optional): Target day-of-month (e.g. "15").
                Defaults to ``get_future_date(1)`` when None.

        Returns:
            VisaPage: ``self``, for method chaining.

        Raises:
            Exception: Re-raised if the date input can't be opened or
                no matching date button is found/clicked.
        """
        self.logger.info("Selecting travel date")
        date_text = self.get_future_date(1) if date_text is None else date_text
        date_input_btn = None

        try:
            date_input = self.waiter.wait_for_clickable(self.TRAVEL_DATE_INPUT)
            self.javascript.scroll_to_element(date_input)
            date_input.click()
            date_input_btn = date_input
            time.sleep(2)

            available_dates = self.driver.find_elements(
                By.CSS_SELECTOR, "button:not([disabled])"
            )

            target_day = int(date_text)
            selected = False
            for date in available_dates:
                if date.text.isdigit() and int(date.text) == target_day:
                    date.click()
                    self.logger.info(f"Selected travel date: {date.text}")
                    selected = True
                    break

            if not selected:
                self.logger.warning(
                    f"Target day {target_day} not found among enabled dates; "
                    f"falling back to the first enabled day > 10"
                )
                for date in available_dates:
                    if date.text.isdigit() and 1 <= int(date.text) <= 31 and int(date.text) > 10:
                        date.click()
                        self.logger.info(f"Selected travel date: {date.text}")
                        selected = True
                        break

            time.sleep(2)  # Wait for date selection to process

            self.logger.info("Date picker opened successfully")
            return self

        except Exception as e:
            self._last_interacted_element = date_input_btn
            self.logger.error(f"Failed to select travel date: {e}")
            raise

    def select_destination_country(self):
        """Open the destination-country dropdown and pick a random option.

        Retries up to 3 times if the chosen option element goes stale
        between being selected and clicked (re-fetching and re-choosing
        randomly each time), since the listbox can re-render its options.

        Returns:
            VisaPage: ``self``, for method chaining.

        Raises:
            Exception: If no option could be clicked after 3 attempts due
                to staleness, or if any other step fails. The element in
                progress at failure time is stashed on
                ``self._last_interacted_element``.
        """
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
        """Open the visa-type dropdown and pick a random option.

        Same stale-element retry pattern as ``select_destination_country``.
        Note both methods query the generic ``//div[@role='listbox']//span``
        XPath rather than a locator scoped to this specific dropdown -
        relies on only one listbox being open in the DOM at a time.

        Returns:
            VisaPage: ``self``, for method chaining.

        Raises:
            Exception: If no option could be clicked after 3 attempts due
                to staleness, or if any other step fails.
        """
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
        """Type into the additional-message textarea.

        Args:
            message (str): Message text to append (the field isn't
                cleared first, unlike most other fill methods in this
                class).

        Returns:
            VisaPage: ``self``, for method chaining.

        Raises:
            Exception: Re-raised if the textarea can't be found/filled.
        """
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
        """Click "Submit application" and give the app a moment to respond.

        Returns:
            VisaPage: ``self``, for method chaining.

        Raises:
            Exception: Re-raised if the submit button can't be
                found/clicked. The clicked button is stashed on
                ``self._last_interacted_element`` for debugging on
                failure.
        """
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
        """Scroll to and click the "Cancel" button.

        Returns:
            VisaPage: ``self``, for method chaining.

        Raises:
            Exception: Re-raised if the cancel button can't be
                found/clicked.
        """
        self.logger.info("Cancelling visa application")
        cancel_btn = None
        
        try:
            cancel_button = self.waiter.wait_for_clickable(self.CANCEL_BTN, timeout=10)
            self.javascript.scroll_to_element(cancel_button)
            cancel_button.click()
            cancel_btn = cancel_button
            
            self.logger.info("Visa application cancelled")
            return self
            
        except Exception as e:
            self._last_interacted_element = cancel_btn
            self.logger.error(f"Failed to cancel application: {e}")
            raise
    
    def is_form_visible(self):
        """Check if the visa application form section is visible.

        Returns:
            bool: True if visible, False if not found or an error occurred.
        """
        try:
            form = self.pageinfo.find_element(*self.FORM_SECTION)
            return form.is_displayed()
        except:
            return False

    def is_success_message_displayed(self):
        """Check if a success message is displayed after submission.

        Returns:
            bool: True if visible within 10s, False on timeout or any
                other error.
        """
        try:
            success_element = self.waiter.wait_for_visible(self.SUCCESS_MESSAGE, timeout=10)
            return success_element.is_displayed()
        except:
            return False

    def get_form_fields_status(self):
        """Snapshot visibility/enabled/value state for each personal-info field.

        Returns:
            dict: Keyed by field name ("first_name", "last_name",
                "email", "phone", "message"), each mapping to
                ``{"visible": bool, "enabled": bool, "value": str}``.
                A field that can't be found gets all-False/empty values
                rather than raising.
        """
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
        """Wait for the visa application form to load, retrying if it doesn't.

        Args:
            timeout (int): Accepted for interface consistency; the inner
                waits use their own fixed 10s timeout regardless of this
                value.
            max_retries (int): Number of attempts before giving up.
                Defaults to 2.

        Returns:
            bool: True once the form section and first-name field are
                confirmed, False if all attempts failed.
        """
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