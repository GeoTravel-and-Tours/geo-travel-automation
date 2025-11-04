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


class FlightBookingFlow(BasePage):
    """
    Geo Travel Flight Booking Flow
    Handles flight search, selection, passenger info, and payment process
    """
    
    # ===== PAGE LOCATORS =====
    
    # Page indicator
    PAGE_INDICATOR = (By.TAG_NAME, "li")
    
    # Flight Search Form
    FLIGHT_SEARCH_FORM = (By.CSS_SELECTOR, "form[data-sentry-element='Form']")
    
    # Trip Type Selectors
    TRIP_TYPE_CONTAINER = (By.XPATH, "//div[@class='grid grid-cols-2 gap-3.5']//div//div[@class='relative']//div[@data-sentry-element='Listbox']")
    TRIP_TYPE_DROPDOWN = (By.CSS_SELECTOR, "button[id*='headlessui-listbox-button-']")
    ONE_WAY_OPTION = (By.XPATH, "//span[normalize-space()='one way']")
    
    # Airport Selection
    FROM_DROPDOWN = (By.CSS_SELECTOR, "button[id*='headlessui-listbox-button-']:nth-child(4)")
    TO_DROPDOWN = (By.CSS_SELECTOR, "button[id*='headlessui-listbox-button-']:nth-child(5)")
    AIRPORT_SEARCH_INPUT = (By.CSS_SELECTOR, "input[placeholder='Enter city or airport']")
    
    # Airport Options
    LONDON_HEATHROW_OPTION = (By.XPATH, "//h6[contains(text(),'London')]")
    AMSTERDAM_SCHIPHOL_OPTION = (By.XPATH, "//p[contains(text(),'Amsterdam Airport Schiphol')]")
    GENERIC_AIRPORT_OPTION = (By.XPATH, "//h6")  # Fallback
    
    # Date Selection
    DEPARTURE_DATE_FIELD = (By.XPATH, "//div[contains(@class, 'cursor-pointer') and contains(., 'Departure Date')]")
    AVAILABLE_DATES = (By.CSS_SELECTOR, "button:not([disabled])")
    
    # Search Button
    SEARCH_FLIGHTS_BUTTON = (By.XPATH, "//button[contains(text(), 'Search flights')]")
    SEARCH_BUTTON_ALT = (By.CSS_SELECTOR, "button[class*='bg-mainblue']")
    
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
                
                try:
                    screenshot_path = self.screenshot.capture_element_screenshot(
                        forms[0], 
                        "flight_search_form",
                        browser_info={"test": "flight_search_form_visibility"}
                    )
                    self.logger.info(f"Flight search form screenshot captured: {screenshot_path}")
                except Exception as screenshot_error:
                    self.logger.warning(f"Could not capture form screenshot: {screenshot_error}")
                
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error checking flight search form: {e}")
            return False

    def select_one_way_trip(self):
        """Select One Way trip type"""
        try:
            self.logger.info("Selecting One Way trip type...")

            # Try multiple selectors for trip container
            trip_container_selectors = [
                self.TRIP_TYPE_CONTAINER,
                self.TRIP_TYPE_DROPDOWN,
                (By.XPATH, "//div[contains(@class, 'relative') and .//span[contains(text(), 'round trip')]]"),
            ]

            trip_container = None
            for selector in trip_container_selectors:
                try:
                    trip_container = self.waiter.wait_for_clickable(selector, timeout=10)
                    self.logger.info("Found trip container")
                    break
                except:
                    continue
                
            if not trip_container:
                self.logger.warning("Trip type container not found")
                return False

            # Click to open dropdown
            trip_container.click()
            self.logger.info("Clicked trip type dropdown")
            time.sleep(2)

            # Select One Way option
            one_way_selectors = [
                self.ONE_WAY_OPTION,
                (By.XPATH, "//*[contains(text(), 'One Way')]"),
                (By.CSS_SELECTOR, "[id*='headlessui-listbox-option-']:nth-child(2)"),
            ]

            for selector in one_way_selectors:
                try:
                    one_way_option = self.waiter.wait_for_clickable(selector, timeout=5)
                    option_text = one_way_option.text.lower()
                    if 'one way' in option_text or 'oneway' in option_text:
                        one_way_option.click()
                        self.logger.info("One Way trip type selected successfully")
                        time.sleep(2)
                        return True
                except:
                    continue
                
            self.logger.warning("One Way option not found")
            return False

        except Exception as e:
            self.logger.warning(f"Could not select One Way: {e}")
            return False

    def select_from_airport(self, airport_name="Heathrow"):
        """Select departure airport"""
        self.logger.info(f"Selecting from airport: {airport_name}")

        try:
            # Click FROM dropdown directly using the correct selector
            from_dropdown = self.waiter.wait_for_clickable(self.FROM_DROPDOWN, timeout=10)
            from_dropdown.click()
            self.logger.info("Clicked FROM dropdown")
            time.sleep(2)

            # Wait for and fill search input
            search_input = self.waiter.wait_for_clickable(self.AIRPORT_SEARCH_INPUT, timeout=10)
            search_input.clear()
            search_input.send_keys(airport_name)
            self.logger.info(f"Typed airport name: {airport_name}")
            time.sleep(3)

            # Select airport from suggestions
            if "heathrow" in airport_name.lower():
                airport_option = self.waiter.wait_for_clickable(self.LONDON_HEATHROW_OPTION, timeout=10)
            else:
                airport_option = self.waiter.wait_for_clickable(
                    (By.XPATH, f"//*[contains(text(), '{airport_name}')]"), 
                    timeout=10
                )

            airport_option.click()
            self.logger.info(f"Selected airport: {airport_name}")
            time.sleep(2)
            return True

        except Exception as e:
            self.logger.error(f"Failed to select from airport {airport_name}: {e}")
            self.screenshot.capture_screenshot("select_from_airport_error")
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
                    try:
                        self.driver.refresh()
                        self.waiter.wait_for_page_load(timeout=10)
                        time.sleep(2)
                    except:
                        pass

        self.logger.error(f"All {max_retries} attempts failed for departure airport selection")
        return False

    def select_to_airport(self, airport_name="Schiphol"):
        """Select destination airport"""
        self.logger.info(f"Selecting to airport: {airport_name}")

        try:
            # Click TO dropdown directly using the correct selector
            to_dropdown = self.waiter.wait_for_clickable(self.TO_DROPDOWN, timeout=10)
            to_dropdown.click()
            self.logger.info("Clicked TO dropdown")
            time.sleep(2)

            # Wait for and fill search input
            search_input = self.waiter.wait_for_clickable(self.AIRPORT_SEARCH_INPUT, timeout=10)
            search_input.clear()
            search_input.send_keys(airport_name)
            self.logger.info(f"Typed destination airport: {airport_name}")
            time.sleep(3)

            # Select airport from suggestions
            if "schiphol" in airport_name.lower():
                airport_option = self.waiter.wait_for_clickable(self.AMSTERDAM_SCHIPHOL_OPTION, timeout=10)
            else:
                airport_option = self.waiter.wait_for_clickable(
                    (By.XPATH, f"//*[contains(text(), '{airport_name}')]"), 
                    timeout=10
                )

            airport_option.click()
            self.logger.info(f"Selected destination airport: {airport_name}")
            time.sleep(2)
            return True

        except Exception as e:
            self.logger.error(f"Failed to select to airport {airport_name}: {e}")
            self.screenshot.capture_screenshot("select_to_airport_error")
            return False

    def select_departure_date(self):
        """Select departure date from calendar"""
        self.logger.info("Selecting departure date...")
        
        departure_field = self.waiter.wait_for_clickable(self.DEPARTURE_DATE_FIELD, timeout=10)
        departure_field.click()
        time.sleep(2)

        # Find and click the first available future date
        available_dates = self.driver.find_elements(*self.AVAILABLE_DATES)
        for date in available_dates:
            if date.text.isdigit() and 1 <= int(date.text) <= 31:
                if int(date.text) > 10:  # Pick a future date
                    date.click()
                    self.logger.info(f"Selected departure date: {date.text}")
                    break

        time.sleep(2)

    def perform_basic_flight_search(self):
        """Perform complete flight search flow"""
        from_city = "Heathrow"
        to_city = "Schiphol"
    
        self.logger.info(f"Performing ONE WAY flight search: {from_city} → {to_city}")
    
        try:
            # Step 1: Select One Way trip type
            one_way_selected = self.select_one_way_trip()
            if not one_way_selected:
                self.logger.warning("Could not select One Way, proceeding with default trip type")
    
            time.sleep(4)
    
            # Step 2: Select departure airport with retry
            from_success = self.select_from_airport_with_retry(from_city, max_retries=2)
            if not from_success:
                raise Exception(f"Failed to select departure airport: {from_city}")
    
            # Step 3: Select destination airport
            to_success = self.select_to_airport(to_city)
            if not to_success:
                raise Exception(f"Failed to select destination airport: {to_city}")
    
            # Step 4: Verify form is filled
            if not self.verify_search_form_filled():
                self.logger.error("Search form validation failed!")
                raise Exception("Search form not properly filled")
    
            # Step 5: Click search button
            search_button_selectors = [
                self.SEARCH_FLIGHTS_BUTTON,
                self.SEARCH_BUTTON_ALT,
                (By.CSS_SELECTOR, "div[class='hidden lg:flex gap-2'] button"),
            ]
    
            search_button = None
            for selector in search_button_selectors:
                try:
                    search_button = self.waiter.wait_for_clickable(selector, timeout=15)
                    self.logger.info("Found search button")
                    break
                except:
                    continue
                
            if not search_button:
                self.logger.error("Search button not found")
                raise Exception("Search button not found")
    
            self.driver.execute_script("arguments[0].click();", search_button)
            self.logger.info("Search button clicked")
    
            # Step 6: Wait for search results
            time.sleep(8)
    
            try:
                self.waiter.wait_for_url_contains("searchId=", timeout=15)
                self.logger.info("Search session initialized with searchId")
            except:
                self.logger.warning("URL didn't update with searchId, but continuing...")
    
            time.sleep(3)
            self.logger.info("Flight search completed successfully")
    
        except Exception as e:
            self.logger.error(f"Flight search failed: {e}")
            self.screenshot.capture_screenshot("flight_search_error")
            raise

    def verify_search_form_filled(self):
        """Verify that the search form has been properly filled for One Way"""
        try:
            from_field = self.driver.find_element(*self.FROM_DROPDOWN)
            from_text = from_field.text
            has_from = "Select" not in from_text and "------" not in from_text

            to_field = self.driver.find_element(*self.TO_DROPDOWN)
            to_text = to_field.text
            has_to = "Select" not in to_text and "------" not in to_text

            self.logger.info(f"From field filled: {has_from} (text: {from_text})")
            self.logger.info(f"To field filled: {has_to} (text: {to_text})")

            return has_from and has_to
        except Exception as e:
            self.logger.error(f"Error verifying search form: {e}")
            return False

    def is_search_session_initialized(self, search_term="searchId=", timeout=30):
        """Check if search session is properly initialized"""
        try:
            current_url = self.driver.current_url
            self.logger.info(f"Checking for '{search_term}' in {current_url} (waiting up to {timeout}s)...")

            WebDriverWait(self.driver, timeout).until(
                lambda driver: search_term in driver.current_url
            )

            current_url = self.driver.current_url
            self.logger.info(f"Found '{search_term}' in URL: {current_url}")
            return True

        except TimeoutException:
            current_url = self.driver.current_url
            self.logger.warning(f"'{search_term}' not found in URL after {timeout}s")
            self.logger.info(f"   Current URL: {current_url}")
            return False
        except Exception as e:
            self.logger.error(f"Error checking search session: {e}")
            return False

    def are_search_results_displayed(self):
        """Check if flight search results are displayed"""
        try:
            self.logger.info("Checking for search results dynamically...")

            if not self.is_search_session_initialized():
                self.logger.warning("No active search session found (missing searchId)")
                return False

            current_url = self.driver.current_url
            search_id = current_url.split("searchId=")[-1] if "searchId=" in current_url else "unknown"
            self.logger.info(f"Checking results for search session: {search_id}")

            # Method 1: Check for result containers
            result_containers = self.driver.find_elements(*self.RESULT_CONTAINERS)
            flight_containers = []
            for container in result_containers:
                container_text = container.text.lower()
                if any(keyword in container_text for keyword in ['flight', 'airline', 'depart', 'arrive', 'price', '₦', 'select']):
                    flight_containers.append(container)

            if flight_containers:
                self.logger.info(f"Found {len(flight_containers)} potential flight containers for search {search_id}")
                return True

            # Method 2: Check for dynamic components
            data_components = self.driver.find_elements(*self.DYNAMIC_COMPONENTS)
            if data_components:
                self.logger.info(f"Found {len(data_components)} dynamic components for search {search_id}")
                return True

            # Method 3: Check for flight data patterns
            page_text = self.driver.page_source.lower()
            flight_patterns = [
                r'\d{1,2}:\d{2}\s*[ap]m',
                r'₦\s*\d+[,.\d]*',
                r'\d+h\s*\d+m',
            ]

            patterns_found = sum(1 for pattern in flight_patterns if re.search(pattern, page_text))
            if patterns_found >= 2:
                self.logger.info(f"Found flight data patterns for search {search_id}")
                return True

            self.logger.warning(f"No dynamic search results detected for session: {search_id}")
            return False

        except Exception as e:
            self.logger.error(f"Error in dynamic search results check: {e}")
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
            self.logger.info("Scrolling to button with reliable method...")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", target_button)
            self.driver.execute_script("window.scrollBy(0, -100);")
            time.sleep(2)

            actions = ActionChains(self.driver)
            actions.move_to_element(target_button).perform()
            time.sleep(1)

            self.waiter.wait_for_clickable(target_button, timeout=10)
            self.screenshot.capture_element_screenshot(target_button, f"before_click_flight_{flight_index}")

            # Try multiple click methods
            try:
                self.driver.execute_script("arguments[0].click();", target_button)
                self.logger.info("Clicked using JavaScript - most reliable method")
            except Exception as js_error:
                self.logger.warning(f"JavaScript click failed: {js_error}, trying standard click")
                try:
                    target_button.click()
                    self.logger.info("Clicked using standard Selenium click")
                except Exception as std_error:
                    self.logger.error(f"All click methods failed: {std_error}")
                    return False

            try:
                self.waiter.wait_for_page_load(timeout=15)
                self.logger.info("Page navigation detected")
            except:
                self.logger.info("No page navigation - may be same-page flow")

            self.screenshot.capture_screenshot("after_flight_selection")
            self.logger.success("Flight selection completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to select flight: {e}")
            self.screenshot.capture_screenshot("flight_selection_failed")
            return False

    def fill_passenger_information(self):
        """Fill passenger information form with test data"""
        try:
            # Full Name
            full_name_input = self.waiter.wait_for_clickable(self.FULL_NAME_INPUT, timeout=10)
            full_name_input.clear()
            full_name_input.send_keys("Smoke Test")

            # Title selection
            title_dropdown = self.waiter.wait_for_clickable(self.TITLE_DROPDOWN, timeout=10)
            title_dropdown.click()
            mr_option = self.waiter.wait_for_clickable(self.MR_OPTION, timeout=10)
            mr_option.click()

            # Gender selection
            gender_dropdown = self.waiter.wait_for_clickable(self.GENDER_DROPDOWN, timeout=10)
            gender_dropdown.click()
            male_option = self.waiter.wait_for_clickable(self.MALE_OPTION, timeout=10)
            male_option.click()

            # Date of Birth
            dob_field = self.waiter.wait_for_clickable(self.DOB_FIELD, timeout=10)
            dob_field.click()

            # Select year and month
            year_select = self.waiter.wait_for_clickable(self.YEAR_SELECT, timeout=10)
            Select(year_select).select_by_visible_text("2002")
            month_select = self.waiter.wait_for_clickable(self.MONTH_SELECT, timeout=10)
            Select(month_select).select_by_visible_text("June")

            # Contact information
            phone_input = self.waiter.wait_for_clickable(self.PHONE_INPUT, timeout=10)
            phone_input.clear()
            phone_input.send_keys("7080702920")

            email_input = self.waiter.wait_for_clickable(self.EMAIL_INPUT, timeout=10)
            email_input.clear()
            email_input.send_keys("elonmusk@yopmail.com")

            passport_input = self.waiter.wait_for_clickable(self.PASSPORT_INPUT, timeout=10)
            passport_input.clear()
            passport_input.send_keys("1234567890123")

            # Country information
            country_origin_dropdown = self.waiter.wait_for_clickable(self.COUNTRY_ORIGIN_DROPDOWN, timeout=10)
            country_origin_dropdown.click()
            nigeria_option = self.waiter.wait_for_clickable(self.NIGERIA_OPTION, timeout=10)
            nigeria_option.click()

            issuing_country_dropdown = self.waiter.wait_for_clickable(self.ISSUING_COUNTRY_DROPDOWN, timeout=10)
            issuing_country_dropdown.click()
            nigeria_issuing_option = self.waiter.wait_for_clickable(self.NIGERIA_OPTION, timeout=10)
            nigeria_issuing_option.click()

            # Passport expiry
            expiry_date_field = self.waiter.wait_for_clickable(self.PASSPORT_EXPIRY_FIELD, timeout=10)
            expiry_date_field.click()
            expiry_year_select = self.waiter.wait_for_clickable(self.YEAR_SELECT, timeout=10)
            Select(expiry_year_select).select_by_visible_text("2011")

            return True
        except Exception as e:
            self.logger.error(f"Error filling passenger information: {e}")
            return False

    def save_passenger_info_and_continue(self):
        """Save passenger information and continue to next step"""
        try:
            save_button = self.waiter.wait_for_clickable(self.SAVE_CONTINUE_BUTTON, timeout=10)
            self.driver.execute_script("arguments[0].scrollIntoView();", save_button)
            time.sleep(1)
            save_button.click()
            return True
        except:
            return False

    def is_payment_page_accessible(self):
        """Check if payment page is accessible"""
        try:
            payment_section = self.waiter.wait_for_visible(self.PAYMENT_SECTION, timeout=10)
            return payment_section.is_displayed()
        except:
            return False

    def select_payment_method(self):
        """Select payment method from available options"""
        try:
            flutterwave_option = self.waiter.wait_for_clickable(self.FLUTTERWAVE_OPTION, timeout=10)
            flutterwave_option.click()
            return True
        except:
            return False

    def proceed_to_payment(self):
        """Proceed to payment final step"""
        try:
            proceed_button = self.waiter.wait_for_clickable(self.PROCEED_PAYMENT_BUTTON, timeout=10)
            proceed_button.click()
            return True
        except:
            return False

    def is_error_message_displayed(self):
        """Check if any error message is displayed on the page"""
        try:
            error_elements = self.driver.find_elements(*self.ERROR_ELEMENTS)
            return len(error_elements) > 0
        except:
            return False

    def get_error_message_text(self):
        """Get error message text if present"""
        try:
            error_elements = self.driver.find_elements(*self.ERROR_ELEMENTS)
            if error_elements:
                return error_elements[0].text
            return None
        except:
            return None

    def is_page_loaded(self, timeout=15):
        """Check if flight booking page is fully loaded and ready for interaction"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

            element = self.waiter.wait_for_visible(self.PAGE_INDICATOR, timeout)
            if not element.is_displayed():
                self.logger.warning("Flight booking indicator element not visible")
                return False

            self.logger.info("Flight booking page fully loaded and interactive")
            return True

        except TimeoutException:
            self.logger.error("Page load timeout - flight booking page not ready")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error while checking page load: {e}")
            return False
    
    def debug_page_locators(self):
        """Debug method to see what locators are available on the page"""
        self.logger.info("=== DEBUGGING PAGE LOCATORS ===")

        # Check FROM dropdown selectors
        from_selectors = [
            self.FROM_DROPDOWN,
            self.FROM_BUTTON,
            (By.CSS_SELECTOR, "button[id*='headlessui-listbox-button-']:first-child"),
            (By.XPATH, "//button[contains(text(), 'From')]"),
            (By.XPATH, "//div[contains(text(), 'From')]"),
            (By.XPATH, "//*[contains(@placeholder, 'From')]"),
        ]

        for i, selector in enumerate(from_selectors):
            try:
                elements = self.driver.find_elements(*selector)
                self.logger.info(f"Selector {i} {selector}: Found {len(elements)} elements")
                for j, elem in enumerate(elements):
                    self.logger.info(f"  Element {j}: text='{elem.text}' visible={elem.is_displayed()}")
            except Exception as e:
                self.logger.info(f"Selector {i} {selector}: Error - {e}")

        # Log current page state
        self.logger.info(f"Current URL: {self.driver.current_url}")
        self.logger.info(f"Page title: {self.driver.title}")

        # Take screenshot for visual debugging
        self.screenshot.capture_screenshot("debug_locators")