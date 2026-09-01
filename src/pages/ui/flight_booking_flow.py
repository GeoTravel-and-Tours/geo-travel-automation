"""
src/pages/ui/flight_booking_flow.py

Page Object for the Geo Travel one-way flight booking flow.

Covers the full flow end to end:
    1. Search           - select "One Way" as the trip type, pick a
                           departure and destination airport (hardcoded
                           to Heathrow -> Schiphol via
                           ``perform_basic_flight_search``), and pick a
                           departure date (tomorrow, by default).
    2. Results           - verify search results rendered and select a
                           flight by index.
    3. Passenger details  - fill the passenger info form with fixed test
                           data (name/title/gender/phone/email).
    4. Payment            - check the payment section is reachable and
                           click the Flutterwave option.

Most of the airport/dropdown-selection methods use multiple fallback
CSS/XPath strategies and retry loops, because the underlying dropdown
widgets proved unreliable to automate directly - see the NOTE on the
class docstring below for why this differs from package_booking_flow.py.

Tests typically call ``perform_basic_flight_search()`` (which itself
chains trip-type -> from-airport -> to-airport -> date), then
``select_flight()`` -> ``fill_passenger_information()`` ->
``save_passenger_info_and_continue()`` -> ``select_payment_method()``.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from src.core.base_page import BasePage
import time
import re
from datetime import datetime, timedelta


class FlightBookingFlow(BasePage):
    """
    Geo Travel Flight Booking Flow.

    Handles flight search, selection, passenger info, and the start of
    the payment process. Locators are grouped by step (search form, trip
    type, airport selection, date selection, search results, passenger
    info, payment) under the "UPDATED PAGE LOCATORS" heading - many
    airport/dropdown locators intentionally use loose, flexible
    XPath/CSS (e.g. matching on partial text) rather than a single
    precise selector, with fallback selector lists tried in sequence in
    the corresponding methods.

    NOTE: unlike ``package_booking_flow.py`` (which imports and, per its
    own docstring, is meant to delegate to ``PaymentPage`` from
    payment_flow.py for the checkout step), this class does NOT import or
    use ``PaymentPage`` at all. Its own ``select_payment_method`` and
    ``is_payment_page_accessible`` reimplement a much more limited
    Flutterwave-only flow inline, and - unlike
    ``PaymentPage.complete_payment_flow`` or
    ``PackageBookingFlow.verify_flutterwave_payment`` - never actually
    verifies the browser reaches the Flutterwave hosted checkout URL.
    """

    # ===== UPDATED PAGE LOCATORS =====
    
    # Page indicator
    PAGE_INDICATOR = (By.TAG_NAME, "li")
    
    # Flight Search Form
    FLIGHT_SEARCH_FORM = (By.CSS_SELECTOR, "form[data-sentry-element='Form']")
    
    # Trip Type Selectors - UPDATED
    TRIP_TYPE_DROPDOWN = (By.XPATH, "//button[.//span[contains(text(), 'Round Trip')]]")
    ONE_WAY_OPTION = (By.XPATH, "//span[contains(text(), 'one way')]")
    
    # Airport Selection - MORE FLEXIBLE LOCATORS
    FROM_DROPDOWN = (By.XPATH, "//button[.//div[contains(text(), 'From')]]")
    TO_DROPDOWN = (By.XPATH, "//button[.//div[contains(text(), 'To')]]")
    AIRPORT_SEARCH_INPUT = (By.CSS_SELECTOR, "input[placeholder*='city' i], input[placeholder*='airport' i]")

    # Airport Options - MORE FLEXIBLE
    LONDON_HEATHROW_OPTION = (By.XPATH, "//*[contains(text(), 'London') or contains(text(), 'Heathrow')]")
    # NOTE: trailing "\" line-continuation below is a harmless leftover from
    # editing (the assignment above already completes on this line) - it just
    # continues the logical line into the blank line that follows.
    AMSTERDAM_SCHIPHOL_OPTION = (By.XPATH, "//*[contains(text(), 'Amsterdam') or contains(text(), 'Schiphol')]")\

    # Date Selection
    # NOTE: uses raw "xpath" string instead of the By.XPATH constant used by
    # every other locator in this file - works because By.XPATH == "xpath",
    # but inconsistent style.
    DEPARTURE_DATE_FIELD = ("xpath", "//div[contains(@class,'cursor-pointer') and .//p[text()='Departure Date']]")
    AVAILABLE_DATES = (By.CSS_SELECTOR, "button:not([disabled])")
    
    # Search Button
    SEARCH_FLIGHTS_BUTTON = (By.XPATH, "//button[contains(text(), 'Search flights')]")
    
    # Search Results
    VIEW_FLIGHT_DETAILS_BUTTON = (By.XPATH, "//button[normalize-space()='View flight details']")
    RESULT_CONTAINERS = (By.XPATH, "//*[contains(@class, 'result') or contains(@class, 'card') or contains(@class, 'item') or contains(@class, 'grid') or contains(@class, 'list')]")
    DYNAMIC_COMPONENTS = (By.CSS_SELECTOR, "[data-sentry-component]")
    
    # Passenger Information Form
    FULL_NAME_INPUT = (By.XPATH, "//input[@placeholder='Enter your full name']")
    TITLE_DROPDOWN = (By.XPATH, "//div[contains(., 'Select title')]")
    MR_OPTION = (By.XPATH, "//span[normalize-space()='mr.']")
    GENDER_DROPDOWN = (By.XPATH, "//div[contains(., 'Select gender')]")
    MALE_OPTION = (By.XPATH, "//span[normalize-space()='male']")
    DOB_FIELD = (By.XPATH, "//div[contains(@id, 'headlessui-popover-button')]//div")
    YEAR_SELECT = (By.XPATH, "//select[contains(@aria-label,'Choose the Year')]")
    MONTH_SELECT = (By.XPATH, "//select[@aria-label='Choose the Month']")
    PHONE_INPUT = (By.XPATH, "//input[@placeholder='Phone number']")
    EMAIL_INPUT = (By.XPATH, "//input[@placeholder='Enter your email address']")
    # NOTE: PASSPORT_INPUT, COUNTRY_ORIGIN_DROPDOWN, NIGERIA_OPTION,
    # ISSUING_COUNTRY_DROPDOWN, PASSPORT_EXPIRY_FIELD, DOB_FIELD,
    # YEAR_SELECT, and MONTH_SELECT are all defined but never referenced by
    # any method below - fill_passenger_information() only fills full
    # name/title/gender/phone/email. If the live passenger form actually
    # requires passport/DOB/country-of-origin fields, this flow would fail
    # to complete a real booking; these locators look like leftovers from
    # an unfinished or since-simplified form.
    PASSPORT_INPUT = (By.XPATH, "//input[@placeholder='Enter your passport number']")
    COUNTRY_ORIGIN_DROPDOWN = (By.XPATH, "//div[contains(., 'Select country of origin')]")
    NIGERIA_OPTION = (By.XPATH, "//span[normalize-space()='nigeria']")
    ISSUING_COUNTRY_DROPDOWN = (By.XPATH, "//div[contains(., 'Select issuing country')]")
    PASSPORT_EXPIRY_FIELD = (By.XPATH, "//div[contains(@id, 'headlessui-popover-button')]//div")

    # Save and Continue
    SAVE_CONTINUE_BUTTON = (By.XPATH, "//button[normalize-space()='Save changes & Continue']")
    
    # Payment Section
    PAYMENT_SECTION = (By.XPATH, "//section[contains(., 'payment') or contains(., 'Payment')]")
    FLUTTERWAVE_OPTION = (By.XPATH, "//li[contains(., 'Flutterwave')]")
    PROCEED_PAYMENT_BUTTON = (By.XPATH, "//button[normalize-space()='Proceed to payment']")
    
    # Error Handling
    ERROR_ELEMENTS = (By.XPATH, "//div[contains(@class, 'error') or contains(@class, 'Error')]")

    def __init__(self, driver):
        """Initialize the page object.

        Args:
            driver (WebDriver): Active Selenium WebDriver instance, passed
                through to ``BasePage``.
        """
        super().__init__(driver)

    def is_flight_search_form_visible(self):
        """Check if the flight search form is present and displayed.

        Returns:
            bool: True if the form is visible, False if not found,
                hidden, or an error occurred.
        """
        try:
            forms = self.driver.find_elements(*self.FLIGHT_SEARCH_FORM)
            if forms and forms[0].is_displayed():
                self.logger.info("Flight search form is visible")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error checking flight search form: {e}")
            return False

    def select_one_way_trip(self, trip_type="One Way"):
        """Open the trip-type dropdown and select the given trip type.

        Tries a list of alternative dropdown-button selectors and, once
        opened, a list of alternative label spellings for the requested
        type (see ``TRIP_TYPE_ALIASES``) - both loops exist because the
        trip-type widget's exact markup/labels proved inconsistent to
        target with a single selector.

        Args:
            trip_type (str): Trip type to select - one of "one way",
                "round trip", "multi city" (case-insensitive), or any
                other string to try verbatim. Defaults to "One Way".

        Returns:
            bool: True if both the dropdown was opened and a matching
                option was clicked, False otherwise.
        """
        log = self.logger

        log.info(f"Selecting trip type: {trip_type}")

        trip_type = trip_type.lower().strip()

        # Possible labels UI may use
        TRIP_TYPE_ALIASES = {
            "one way": ["One Way", "One-way", "One way", "one way"],
            "round trip": ["Round Trip", "Return", "round trip"],
            "multi city": ["Multi City", "Multicity", "multi city"]
        }

        target_labels = TRIP_TYPE_ALIASES.get(trip_type, [trip_type])

        # --- STEP 1: Try to open the trip type listbox ---
        dropdown_selectors = [
            ("xpath", "//button[contains(., 'Round') or contains(., 'Trip') or contains(., 'Way')]"),
            ("xpath", "//button[contains(@id,'headlessui-listbox-button')]"),
            ("css selector", "button[id*='headlessui-listbox-button']"),
            ("xpath", "//button[contains(@class,'listbox')]"),
            ("xpath", "//button[contains(@class,'cursor-pointer') and contains(@class,'rounded')]"),
            ("xpath", "//button[contains(., 'Trip') or contains(., 'trip')]")
        ]

        opened = False
        for by, selector in dropdown_selectors:
            try:
                log.info(f"Trying trip dropdown selector: {selector}")
                elem = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((by, selector))
                )
                self.javascript.execute_script("arguments[0].scrollIntoView(true);", elem)
                elem.click()
                opened = True
                log.info("Trip type dropdown opened successfully")
                break
            except Exception as e:
                log.warning(f"Dropdown selector failed: {selector} -> {e}")

        if not opened:
            log.error("❌ Could NOT open trip type dropdown")
            return False

        # --- STEP 2: Select the requested trip type ---
        option_found = False
        for label in target_labels:
            try:
                xpath = f"//*[normalize-space(text())='{label}']"
                log.info(f"Trying option selector: {xpath}")

                option = WebDriverWait(self.driver, 7).until(
                    EC.element_to_be_clickable(("xpath", xpath))
                )
                self.javascript.execute_script("arguments[0].scrollIntoView(true);", option)
                option.click()
                option_found = True
                log.info(f"Trip type selected: {label}")
                break
            except:
                continue

        if not option_found:
            log.error(f"❌ Could NOT find trip type option matching: {target_labels}")
            return False

        return True




    def select_from_airport(self, airport_name="Heathrow"):
        """Select the departure ("From") airport, trying multiple fallback strategies.

        Opens the FROM dropdown (primary locator, or one of several
        alternative selectors if that fails), types ``airport_name`` into
        whatever search input appears, then clicks a matching option -
        matched loosely against ``airport_name`` plus the hardcoded
        keywords "london"/"heathrow" as a safety net for this default
        route.

        Args:
            airport_name (str): Airport/city name to search for and
                select. Defaults to "Heathrow".

        Returns:
            bool: True if an option was found and clicked, False if any
                stage (dropdown, search input, or option) couldn't be
                resolved.
        """
        self.logger.info(f"Selecting from airport: {airport_name}")

        try:
            # Wait for page stability
            time.sleep(3)

            # STRATEGY 1: Try the standard approach first
            try:
                from_dropdown = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable(self.FROM_DROPDOWN)
                )
                from_dropdown.click()
                self.logger.info("Clicked FROM dropdown (Strategy 1)")
                time.sleep(2)
            except:
                self.logger.warning("Strategy 1 failed, trying alternative selectors...")

                # STRATEGY 2: Try alternative FROM dropdown selectors
                alternative_selectors = [
                    (By.XPATH, "//button[contains(., 'From')]"),
                    (By.XPATH, "//div[contains(text(), 'From')]"),
                    (By.XPATH, "//*[contains(text(), 'From')]"),
                    (By.CSS_SELECTOR, "button[id*='headlessui']:first-child"),
                ]

                from_dropdown = None
                for selector in alternative_selectors:
                    try:
                        elements = self.driver.find_elements(*selector)
                        for elem in elements:
                            if elem.is_displayed() and elem.is_enabled():
                                from_dropdown = elem
                                self.logger.info(f"Found FROM dropdown with alternative selector: {selector}")
                                break
                        if from_dropdown:
                            break
                    except:
                        continue
                    
                if not from_dropdown:
                    self.logger.error("No FROM dropdown found with any selector")
                    return False

                from_dropdown.click()
                self.logger.info("Clicked FROM dropdown (Strategy 2)")
                time.sleep(2)

            # Wait for search input to appear
            search_input = None
            search_selectors = [
                (By.CSS_SELECTOR, "input[placeholder*='city' i], input[placeholder*='airport' i]"),
                (By.CSS_SELECTOR, "input[type='text'], input[type='search']"),
                (By.TAG_NAME, "input"),
            ]

            for selector in search_selectors:
                try:
                    search_input = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable(selector)
                    )
                    self.logger.info(f"Found search input with selector: {selector}")
                    break
                except:
                    continue
                
            if not search_input:
                self.logger.error("No search input found")
                return False

            # Clear and type airport name
            search_input.clear()
            search_input.send_keys(airport_name)
            self.logger.info(f"Typed: {airport_name}")
            time.sleep(2)

            # Select the airport option
            airport_option = None
            option_selectors = [
                (By.XPATH, f"//*[contains(text(), '{airport_name}')]"),
                (By.XPATH, "//h6[contains(text(), 'London')]"),
                (By.CSS_SELECTOR, "[role='option']"),
                (By.CSS_SELECTOR, "[id*='headlessui-listbox-option-']"),
            ]

            for selector in option_selectors:
                try:
                    elements = self.driver.find_elements(*selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            elem_text = elem.text.lower()
                            if any(keyword in elem_text for keyword in [airport_name.lower(), 'london', 'heathrow']):
                                airport_option = elem
                                self.logger.info(f"Found airport option: {elem.text}")
                                break
                    if airport_option:
                        break
                except:
                    continue
                
            if not airport_option:
                self.logger.error(f"No airport option found for {airport_name}")
                return False

            # Click the option
            airport_option.click()
            self.logger.info(f"Selected: {airport_name}")
            time.sleep(2)
            return True

        except Exception as e:
            self.logger.error(f"Failed to select from airport {airport_name}: {e}")
            self.screenshot.capture_screenshot_on_failure(f"select_from_airport_error")
            return False

    def select_from_airport_with_retry(self, airport_name, max_retries=3):
        """Call ``select_from_airport`` repeatedly until it succeeds or retries run out.

        Args:
            airport_name (str): Airport/city name to select.
            max_retries (int): Max number of attempts. Defaults to 3.

        Returns:
            bool: True as soon as an attempt succeeds, False if every
                attempt fails.
        """
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Attempt {attempt + 1}/{max_retries} to select departure airport")
                
                if self.select_from_airport(airport_name):
                    return True
                    
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    self.logger.info("Waiting 3 seconds before retry...")
                    time.sleep(3)

        self.logger.error(f"All {max_retries} attempts failed for departure airport selection")
        return False

    def select_to_airport(self, airport_name="Schiphol"):
        """Select the destination ("To") airport, with extensive fallback handling.

        Similar shape to ``select_from_airport`` but with extra handling
        for the TO dropdown sometimes starting disabled until the FROM
        airport is chosen (polls up to 10s for it to become enabled,
        falling back to a JS click if it's still reported disabled), and
        a final fallback of pressing Enter to accept whatever option is
        currently highlighted if no option element can be matched
        directly.

        Args:
            airport_name (str): Airport/city name to search for and
                select. Defaults to "Schiphol".

        Returns:
            bool: True if an option was selected (directly, or inferred
                via the Enter-key fallback), False if every strategy
                failed.
        """
        self.logger.info(f"Selecting to airport: {airport_name}")
        
        try:
            # Wait longer after FROM selection to ensure UI updates
            time.sleep(4)
            
            # STRATEGY 1: Try the standard approach first
            try:
                to_dropdown = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(self.TO_DROPDOWN)
                )
                
                # Check if TO dropdown is enabled
                if not to_dropdown.is_enabled():
                    self.logger.info("TO dropdown is disabled, waiting for it to become enabled...")
                    # Wait up to 10 seconds for it to become enabled
                    for i in range(10):
                        time.sleep(1)
                        if to_dropdown.is_enabled():
                            self.logger.info("TO dropdown is now enabled")
                            break
                    else:
                        self.logger.error("TO dropdown remained disabled after 10 seconds")
                        return False
                        
                to_dropdown.click()
                self.logger.info("Clicked TO dropdown (Strategy 1)")
                time.sleep(3)
                
            except Exception as e:
                self.logger.warning(f"Strategy 1 failed: {e}, trying alternative selectors...")
                
                # STRATEGY 2: Try alternative TO dropdown selectors
                alternative_selectors = [
                    (By.XPATH, "//button[contains(., 'To')]"),
                    (By.XPATH, "//div[contains(text(), 'To')]"),
                    (By.XPATH, "//*[contains(text(), 'To')]"),
                    (By.CSS_SELECTOR, "button[id*='headlessui']:nth-child(2)"),
                ]
                
                to_dropdown = None
                for selector in alternative_selectors:
                    try:
                        elements = self.driver.find_elements(*selector)
                        for elem in elements:
                            if elem.is_displayed():
                                to_dropdown = elem
                                self.logger.info(f"Found TO dropdown with alternative selector: {selector}")
                                break
                        if to_dropdown:
                            break
                    except:
                        continue
                    
                if not to_dropdown:
                    self.logger.error("No TO dropdown found with any selector")
                    return False
                    
                # Check if enabled
                if not to_dropdown.is_enabled():
                    self.logger.info("TO dropdown is disabled in strategy 2, trying to force click...")
                    # Try JavaScript click as fallback
                    self.driver.execute_script("arguments[0].click();", to_dropdown)
                else:
                    to_dropdown.click()
                    
                self.logger.info("Clicked TO dropdown (Strategy 2)")
                time.sleep(3)
            
            # Wait for search input to appear
            search_input = None
            search_selectors = [
                (By.CSS_SELECTOR, "input[placeholder*='city' i], input[placeholder*='airport' i]"),
                (By.CSS_SELECTOR, "input[type='text'], input[type='search']"),
                (By.TAG_NAME, "input"),
            ]
            
            for selector in search_selectors:
                try:
                    search_input = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable(selector)
                    )
                    self.logger.info(f"Found search input with selector: {selector}")
                    break
                except:
                    continue
                
            if not search_input:
                self.logger.error("No search input found for TO dropdown")
                # Try typing directly without search input
                actions = ActionChains(self.driver)
                actions.send_keys(airport_name)
                actions.perform()
                self.logger.info(f"Typed {airport_name} directly (no search input)")
                time.sleep(2)
            else:
                # Clear and type airport name
                search_input.clear()
                search_input.send_keys(airport_name)
                self.logger.info(f"Typed: {airport_name}")
                time.sleep(2)
            
            # Select the airport option with multiple strategies
            airport_option = None
            option_selectors = [
                (By.XPATH, f"//*[contains(text(), '{airport_name}')]"),
                (By.XPATH, "//*[contains(text(), 'Amsterdam') or contains(text(), 'Schiphol')]"),
                (By.XPATH, "//h6[contains(text(), 'Amsterdam')]"),
                (By.CSS_SELECTOR, "[role='option']"),
                (By.CSS_SELECTOR, "[id*='headlessui-listbox-option-']"),
            ]
            
            max_attempts = 3
            for attempt in range(max_attempts):
                for selector in option_selectors:
                    try:
                        elements = self.driver.find_elements(*selector)
                        self.logger.info(f"Attempt {attempt + 1}: Found {len(elements)} elements with {selector}")
                        
                        for elem in elements:
                            if elem.is_displayed() and elem.is_enabled():
                                elem_text = elem.text.lower()
                                self.logger.info(f"Checking option: '{elem_text}'")
                                if any(keyword in elem_text for keyword in [airport_name.lower(), 'amsterdam', 'schiphol', 'ams']):
                                    airport_option = elem
                                    self.logger.info(f"Found matching airport option: {elem.text}")
                                    break
                        if airport_option:
                            break
                    except Exception as e:
                        self.logger.warning(f"Selector {selector} failed: {e}")
                
                if airport_option:
                    break
                    
                # If no option found, wait and retry
                if attempt < max_attempts - 1:
                    self.logger.info(f"No option found, waiting 2 seconds before retry {attempt + 2}...")
                    time.sleep(2)
            
            if not airport_option:
                self.logger.error(f"No airport option found for {airport_name} after {max_attempts} attempts")
                
                # FINAL FALLBACK: Try pressing Enter to select whatever is highlighted
                self.logger.info("Trying final fallback: Pressing Enter key")
                actions = ActionChains(self.driver)
                actions.send_keys(Keys.ENTER)
                actions.perform()
                time.sleep(2)
                
                # Check if selection worked by verifying TO dropdown text changed
                try:
                    to_dropdown = self.driver.find_element(By.XPATH, "//button[contains(., 'To')]")
                    to_text = to_dropdown.text.lower()
                    if "select" not in to_text and "------" not in to_text:
                        self.logger.info("TO selection appears successful via Enter key fallback")
                        return True
                    else:
                        self.logger.error("TO selection failed even with Enter key fallback")
                        return False
                except:
                    return False
                
            # Click the found option
            airport_option.click()
            self.logger.info(f"Selected: {airport_name}")
            time.sleep(2)
            
            # Verify selection worked
            try:
                to_dropdown = self.driver.find_element(By.XPATH, "//button[contains(., 'To')]")
                to_text = to_dropdown.text.lower()
                if "select" in to_text or "------" in to_text:
                    self.logger.warning(f"TO selection may not have worked. Current text: {to_text}")
                else:
                    self.logger.info("TO selection verified successfully")
            except:
                self.logger.warning("Could not verify TO selection")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to select to airport {airport_name}: {e}")
            self.screenshot.capture_screenshot_on_failure(f"select_to_airport_error")
            return False

    def select_departure_date(self):
        """
        Open the departure date picker and select tomorrow's date.

        FIXME: the docstring inherited from an earlier version references
        a ``days_ahead`` parameter, but this method takes no parameters
        at all and always hardcodes "tomorrow" (``timedelta(days=1)``) -
        there's no way to select a different offset. Also note the first
        ``departure_field = self.pageinfo.find_element(...)`` result
        below is immediately discarded and re-fetched via
        ``WebDriverWait`` on the next line - the first call does nothing
        useful.

        Returns:
            bool: True if a date was clicked (tomorrow's date if found,
                otherwise the first available enabled day), False on any
                failure.
        """
        try:
            self.logger.info("Selecting departure date...")

            # Step 1: Click the departure date field
            departure_field = self.pageinfo.find_element(self.DEPARTURE_DATE_FIELD, timeout=10)
            departure_field = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.DEPARTURE_DATE_FIELD)
            )
            departure_field.click()

            # Find all enabled day buttons
            available_days = self.driver.find_elements(
                By.CSS_SELECTOR, "button.day:not([disabled])"
            )

            # Pick tomorrow (or the first day greater than today)
            tomorrow_day = (datetime.today() + timedelta(days=1)).day
            for day in available_days:
                if day.text.isdigit() and int(day.text) == tomorrow_day:
                    day.click()
                    self.logger.info(f"Selected departure date: {tomorrow_day}")
                    break
            else:
                self.logger.warning("Tomorrow's date not found, selecting first available date")
                available_days[0].click()

            time.sleep(1)  # wait for selection to process
            return True

        except Exception as e:
            self.logger.error(f"Failed to select departure date: {e}")
            return False

    def perform_basic_flight_search(self):
        """Run the full one-way search flow: trip type, both airports, and date.

        NOTE: ``from_city``/``to_city`` are hardcoded to "Heathrow" and
        "Schiphol" rather than accepted as parameters, so this method
        always searches the same fixed route.

        Chains ``select_one_way_trip`` -> ``select_from_airport_with_retry``
        -> ``select_to_airport`` -> ``select_departure_date``, then
        confirms both airport fields show a selection via
        ``verify_search_form_filled``.

        Returns:
            bool: True if every step succeeded and the form is
                confirmed filled, False if any step failed (details
                logged, no exception propagated to the caller).
        """
        from_city = "Heathrow"
        to_city = "Schiphol"

        self.logger.info(f"Performing ONE WAY flight search: {from_city} → {to_city}")

        try:
            # Step 1: Select One Way trip type
            one_way_selected = self.select_one_way_trip()
            if not one_way_selected:
                self.logger.warning("Could not select One Way, proceeding with default trip type")

            time.sleep(2)

            # Step 2: Select departure airport
            from_success = self.select_from_airport_with_retry(from_city, max_retries=2)
            if not from_success:
                raise Exception(f"Failed to select departure airport: {from_city}")

            # Step 3: Select destination airport
            to_success = self.select_to_airport(to_city)
            if not to_success:
                raise Exception(f"Failed to select destination airport: {to_city}")

            # Step 4: Select departure date (tomorrow by default)
            date_success = self.select_departure_date()
            if not date_success:
                raise Exception("Failed to select departure date")

            # Step 5: Verify form is filled
            if not self.verify_search_form_filled():
                self.logger.error("Search form validation failed!")
                raise Exception("Search form not properly filled")

            self.logger.info("Basic flight search form completed successfully!")
            return True

        except Exception as e:
            self.logger.error(f"Flight search failed: {e}")
            # Capture screenshot
            # self.screenshot.capture_screenshot_on_failure("flight_search_error.png")
            return False

    def verify_search_form_filled(self):
        """Verify neither the FROM nor TO dropdown still shows placeholder text.

        Considers a field "filled" if its text doesn't contain "select"
        or "------" (the widget's placeholder patterns).

        Returns:
            bool: True if both FROM and TO appear filled, False if
                either still shows a placeholder or an error occurred.
        """
        try:
            time.sleep(2)
            
            # Check FROM field
            from_element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(self.FROM_DROPDOWN)
            )
            from_text = from_element.text.lower()
            
            # Check TO field  
            to_element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(self.TO_DROPDOWN)
            )
            to_text = to_element.text.lower()
            
            # Simple validation - should not contain "Select" or "------"
            from_filled = "select" not in from_text and "------" not in from_text
            to_filled = "select" not in to_text and "------" not in to_text
            
            self.logger.info(f"FROM filled: {from_filled} (text: {from_text})")
            self.logger.info(f"TO filled: {to_filled} (text: {to_text})")
            
            return from_filled and to_filled
            
        except Exception as e:
            self.logger.error(f"Error verifying search form: {e}")
            return False

    def is_search_session_initialized(self, search_term="searchId=", timeout=30):
        """Poll the current URL until it contains ``search_term``.

        Args:
            search_term (str): Substring expected to appear in the URL
                once search results have loaded. Defaults to "searchId=".
            timeout (int): Max seconds to wait. Defaults to 30.

        Returns:
            bool: True if found in time, False on timeout or any other
                error.
        """
        try:
            current_url = self.driver.current_url
            self.logger.info(f"Checking for '{search_term}' in {current_url}")

            WebDriverWait(self.driver, timeout).until(
                lambda driver: search_term in driver.current_url
            )

            current_url = self.driver.current_url
            self.logger.info(f"Found '{search_term}' in URL: {current_url}")
            return True

        except TimeoutException:
            current_url = self.driver.current_url
            self.logger.warning(f"'{search_term}' not found in URL after {timeout}s")
            self.logger.info(f"Current URL: {current_url}")
            return False
        except Exception as e:
            self.logger.error(f"Error checking search session: {e}")
            return False

    def are_search_results_displayed(self):
        """Check that a search session started and flight-like results rendered.

        First confirms via ``is_search_session_initialized``, then looks
        for result containers whose text mentions flight-related keywords
        (flight/airline/depart/arrive/price/₦), falling back to a generic
        check for any Sentry-tracked dynamic component if no keyword
        match is found.

        Returns:
            bool: True if a session was initialized AND either flight
                keyword matches or dynamic components were found, False
                otherwise.
        """
        try:
            self.logger.info("Checking for search results...")

            if not self.is_search_session_initialized():
                self.logger.warning("No active search session found")
                return False

            # Method 1: Check for result containers
            result_containers = self.driver.find_elements(*self.RESULT_CONTAINERS)
            flight_containers = []
            for container in result_containers:
                container_text = container.text.lower()
                if any(keyword in container_text for keyword in ['flight', 'airline', 'depart', 'arrive', 'price', '₦']):
                    flight_containers.append(container)

            if flight_containers:
                self.logger.info(f"Found {len(flight_containers)} potential flight containers")
                return True

            # Method 2: Check for dynamic components
            data_components = self.driver.find_elements(*self.DYNAMIC_COMPONENTS)
            if data_components:
                self.logger.info(f"Found {len(data_components)} dynamic components")
                return True

            self.logger.warning("No search results detected")
            return False

        except Exception as e:
            self.logger.error(f"Error in search results check: {e}")
            return False
        
    def select_flight(self, flight_index=0):
        """Click "View flight details" for the flight at the given index.

        Falls back to index 0 if ``flight_index`` is out of range, rather
        than failing. Uses a JS click after scrolling, since the button
        may be behind other elements.

        Args:
            flight_index (int): Zero-based index of the flight to select.
                Defaults to 0.

        Returns:
            bool: True if a button was clicked, False if no results/
                buttons were found or an error occurred.
        """
        try:
            self.logger.info(f"Selecting flight at index {flight_index}")

            if not self.are_search_results_displayed():
                self.logger.error("No search results available to select from")
                return False

            view_buttons = self.driver.find_elements(*self.VIEW_FLIGHT_DETAILS_BUTTON)
            self.logger.info(f"Found {len(view_buttons)} 'View flight details' buttons")

            if not view_buttons:
                self.logger.error("No 'View flight details' buttons found")
                return False

            if flight_index >= len(view_buttons):
                self.logger.warning(f"Requested index {flight_index} not available, selecting first flight")
                flight_index = 0

            target_button = view_buttons[flight_index]

            # Scroll to button
            self.driver.execute_script("arguments[0].scrollIntoView(true);", target_button)
            time.sleep(1)

            # Click using JavaScript
            self.driver.execute_script("arguments[0].click();", target_button)
            self.logger.info("Flight selected successfully")
            time.sleep(3)
            return True

        except Exception as e:
            self.logger.error(f"Failed to select flight: {e}")
            self.screenshot.capture_screenshot_on_failure("flight_selection_failed")
            return False

    def fill_passenger_information(self):
        """Fill the passenger info form with fixed test data (no parameters).

        Fills full name, title ("mr."), gender ("male"), phone, and
        email - all hardcoded rather than accepted as arguments, so this
        is only suitable for test/staging use. Does not fill
        passport/DOB/country-of-origin fields (see the NOTE on those
        locators above).

        Returns:
            bool: True if every field was filled successfully, False on
                any error.
        """
        try:
            # Full Name
            full_name_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.FULL_NAME_INPUT)
            )
            full_name_input.clear()
            full_name_input.send_keys("Smoke Test")

            # Title selection
            title_dropdown = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.TITLE_DROPDOWN)
            )
            title_dropdown.click()
            mr_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.MR_OPTION)
            )
            mr_option.click()

            # Gender selection
            gender_dropdown = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.GENDER_DROPDOWN)
            )
            gender_dropdown.click()
            male_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.MALE_OPTION)
            )
            male_option.click()

            # Contact information
            phone_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.PHONE_INPUT)
            )
            phone_input.clear()
            phone_input.send_keys("7080702920")

            email_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.EMAIL_INPUT)
            )
            email_input.clear()
            email_input.send_keys("geo.qa.bot@gmail.com")

            return True
        except Exception as e:
            self.logger.error(f"Error filling passenger information: {e}")
            return False

    def save_passenger_info_and_continue(self):
        """Scroll to and click "Save changes & Continue".

        Returns:
            bool: True if clicked successfully, False on any error.
        """
        try:
            save_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.SAVE_CONTINUE_BUTTON)
            )
            self.driver.execute_script("arguments[0].scrollIntoView();", save_button)
            time.sleep(1)
            save_button.click()
            return True
        except:
            return False

    def is_payment_page_accessible(self):
        """Check if the payment section is visible on the page.

        Returns:
            bool: True if visible within 10s, False on timeout or any
                other error.
        """
        try:
            payment_section = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(self.PAYMENT_SECTION)
            )
            return payment_section.is_displayed()
        except:
            return False

    def select_payment_method(self):
        """Click the Flutterwave payment option.

        NOTE: this only clicks the option - it does not wait for or
        verify that the browser actually reaches the Flutterwave hosted
        checkout URL (contrast with ``PaymentPage.complete_payment_flow``
        or ``PackageBookingFlow.verify_flutterwave_payment``, both of
        which explicitly wait for the checkout URL). See the class-level
        NOTE about this flow not using ``PaymentPage``.

        Returns:
            bool: True if the option was clicked, False on any error.
        """
        try:
            flutterwave_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.FLUTTERWAVE_OPTION)
            )
            flutterwave_option.click()
            return True
        except:
            return False

    def is_page_loaded(self, timeout=15):
        """Check if the document has reached ``readyState == "complete"``.

        Args:
            timeout (int): Seconds to wait. Defaults to 15.

        Returns:
            bool: True if loaded in time, False on timeout or any other
                error.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            self.logger.info("Flight booking page fully loaded and interactive")
            return True
        except TimeoutException:
            self.logger.error("Page load timeout - flight booking page not ready")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error while checking page load: {e}")
            return False
        
    def debug_ui_elements(self):
        """Log every visible button/input on the page and capture a screenshot.

        Diagnostic helper only (not part of the normal flow) - useful
        when a locator stops matching and you need to see what's
        actually rendered.

        Returns:
            bool: Always True.
        """
        self.logger.info("=== COMPREHENSIVE UI DEBUG ===")

        # Wait for page to load
        time.sleep(3)

        # Check all buttons
        buttons = self.driver.find_elements(By.TAG_NAME, "button")
        self.logger.info(f"Found {len(buttons)} buttons:")
        for i, btn in enumerate(buttons):
            try:
                if btn.is_displayed():
                    text = btn.text.replace('\n', ' | ')
                    if text.strip():
                        btn_id = btn.get_attribute('id') or 'no-id'
                        btn_class = btn.get_attribute('class') or 'no-class'
                        self.logger.info(f"  Button {i}: ID='{btn_id}', Class='{btn_class}', Text='{text}'")
            except:
                pass
            
        # Check all inputs
        inputs = self.driver.find_elements(By.TAG_NAME, "input")
        self.logger.info(f"Found {len(inputs)} inputs:")
        for i, inp in enumerate(inputs):
            try:
                if inp.is_displayed():
                    placeholder = inp.get_attribute('placeholder') or 'no-placeholder'
                    inp_type = inp.get_attribute('type') or 'no-type'
                    self.logger.info(f"  Input {i}: Type='{inp_type}', Placeholder='{placeholder}'")
            except:
                pass
            
        # Take screenshot
        self.screenshot.capture_screenshot_on_failure("ui_debug_comprehensive")

        return True