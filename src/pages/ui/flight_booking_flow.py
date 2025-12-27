# src/pages/ui/flight_booking_flow.py

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
    Geo Travel Flight Booking Flow
    Handles flight search, selection, passenger info, and payment process
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
    AMSTERDAM_SCHIPHOL_OPTION = (By.XPATH, "//*[contains(text(), 'Amsterdam') or contains(text(), 'Schiphol')]")\
    
    # Date Selection
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
        super().__init__(driver)

    def is_flight_search_form_visible(self):
        """Verify flight search form is visible on the page"""
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
        """Select departure airport - AGGRESSIVE FALLBACK APPROACH"""
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
        """Select departure airport with retry mechanism"""
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
        """Select destination airport - IMPROVED WITH BETTER HANDLING"""
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
        Selects the departure date dynamically.
        :param days_ahead: Number of days from today (default 1 = tomorrow)
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
        """Perform complete flight search flow - SIMPLIFIED AND FIXED"""
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
        """Verify that the search form has been properly filled - SIMPLIFIED"""
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
        """Check if search session is properly initialized"""
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
        """Check if flight search results are displayed"""
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
        """Select a flight by clicking 'View flight details' button"""
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
        """Fill passenger information form with test data"""
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
        """Save passenger information and continue to next step"""
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
        """Check if payment page is accessible"""
        try:
            payment_section = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(self.PAYMENT_SECTION)
            )
            return payment_section.is_displayed()
        except:
            return False

    def select_payment_method(self):
        """Select payment method from available options"""
        try:
            flutterwave_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.FLUTTERWAVE_OPTION)
            )
            flutterwave_option.click()
            return True
        except:
            return False

    def is_page_loaded(self, timeout=15):
        """Check if flight booking page is fully loaded and ready for interaction"""
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
        """Debug method to see all available UI elements"""
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