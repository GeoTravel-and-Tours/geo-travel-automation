# src/pages/dashboard_page.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from src.core.base_page import BasePage
import time
import re


class FlightBookingFlow(BasePage):
    """
    Geo Travel Flight Booking Flow
    Handles flight search, selection, passenger info, and payment process
    """
    
    # Page indicator element
    page_indicator = (By.TAG_NAME, "li")

    def __init__(self, driver):
        super().__init__(driver)

    def is_flight_search_form_visible(self):
        """Verify flight search form is visible on the page"""
        try:
            forms = self.driver.find_elements(By.CSS_SELECTOR, "form[data-sentry-element='Form']")
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
        """Select One Way trip type instead of Round Trip"""
        try:
            self.logger.info("Selecting One Way trip type...")
            
            # First click the trip type dropdown to open options
            trip_dropdown_selectors = [
                (By.CSS_SELECTOR, "button[id*='headlessui-listbox-button-']"),
                (By.XPATH, "//button[contains(., 'Round Trip') or contains(., 'round trip')]"),
                (By.XPATH, "//span[normalize-space()='round trip']/ancestor::button"),
            ]
            
            trip_dropdown = None
            for selector_type, selector_value in trip_dropdown_selectors:
                try:
                    trip_dropdown = self.waiter.wait_for_clickable((selector_type, selector_value), timeout=5)
                    self.logger.info(f"Found trip dropdown with: {selector_value}")
                    break
                except:
                    continue
            
            if not trip_dropdown:
                self.logger.warning("Trip type dropdown not found")
                return False
                
            trip_dropdown.click()
            time.sleep(1)  # Wait for dropdown to open
            
            # Now select One Way option
            one_way_selectors = [
                (By.XPATH, "//span[normalize-space()='one way']"),
                (By.XPATH, "//*[contains(text(), 'One Way')]"),
                (By.CSS_SELECTOR, "[id*='headlessui-listbox-option-']"),
            ]
            
            for selector_type, selector_value in one_way_selectors:
                try:
                    one_way_option = self.waiter.wait_for_clickable((selector_type, selector_value), timeout=5)
                    option_text = one_way_option.text.lower()
                    if 'one way' in option_text or 'oneway' in option_text:
                        one_way_option.click()
                        self.logger.info("One Way trip type selected")
                        time.sleep(1)  # Wait for UI to update
                        return True
                except:
                    continue
            
            self.logger.warning("One Way option not found in dropdown")
            return False
            
        except Exception as e:
            self.logger.warning(f"Could not select One Way: {e}")
            return False

    def select_from_airport(self, airport_name="Heathrow"):
        """Select departure airport from dropdown"""
        self.logger.info(f"Selecting from airport: {airport_name}")

        # Click the "From" dropdown button
        from_dropdown = self.waiter.wait_for_clickable(
            (By.XPATH, "//button[contains(., 'From')]"),
            timeout=10,
        )
        from_dropdown.click()

        # Wait for search input and type airport name
        search_input = self.waiter.wait_for_present(
            (By.CSS_SELECTOR, "input"), timeout=5
        )
        search_input.clear()
        search_input.send_keys(airport_name)

        time.sleep(2)  # Wait for results to load

        # Try to find and click Heathrow specifically
        try:
            heathrow_option = self.waiter.wait_for_clickable(
                (By.XPATH, "//*[contains(text(), 'Heathrow') or contains(text(), 'LHR')]"),
                timeout=10,
            )
            heathrow_option.click()
            self.logger.info("Heathrow airport selected")
        except:
            # Fallback: click the first available result
            self.logger.warning("Could not find specific Heathrow option, clicking first result")
            first_result = self.waiter.wait_for_clickable(
                (By.CSS_SELECTOR, "li:first-child, div:first-child, [role='option']:first-child"),
                timeout=5,
            )
            first_result.click()

        time.sleep(1)

    def select_to_airport(self, airport_name="Schiphol"):
        """Select destination airport from dropdown"""
        self.logger.info(f"Selecting to airport: {airport_name}")

        # Click the "To" dropdown button
        to_dropdown = self.waiter.wait_for_clickable(
            (By.XPATH, "//button[contains(., 'To')]"),
            timeout=10,
        )
        to_dropdown.click()

        # Wait for search input and type airport name
        search_input = self.waiter.wait_for_present(
            (By.CSS_SELECTOR, "input"), timeout=5
        )
        search_input.clear()
        search_input.send_keys(airport_name)

        time.sleep(2)

        # Try to find and click Schiphol specifically
        try:
            schiphol_option = self.waiter.wait_for_clickable(
                (By.XPATH, "//*[contains(text(), 'Schiphol') or contains(text(), 'AMS')]"),
                timeout=10,
            )
            schiphol_option.click()
            self.logger.info("Schiphol airport selected")
        except:
            # Fallback: click the first available result
            self.logger.warning("Could not find specific Schiphol option, clicking first result")
            first_result = self.waiter.wait_for_clickable(
                (By.CSS_SELECTOR, "li:first-child, div:first-child, [role='option']:first-child"),
                timeout=5,
            )
            first_result.click()

        time.sleep(1)

    def select_departure_date(self):
        """Select departure date from calendar"""
        self.logger.info("Selecting departure date...")
        
        # Click departure date field
        departure_field = self.waiter.wait_for_clickable(
            (By.XPATH, "//div[contains(@class, 'cursor-pointer') and contains(., 'Departure Date')]"),
            timeout=10,
        )
        departure_field.click()

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
                    self.logger.info(f"Selected departure date: {date.text}")
                    break

        time.sleep(2)  # Wait for date selection to process

    def perform_basic_flight_search(self):
        """Perform complete flight search flow - optimized for One Way"""
        from_city = "Heathrow"
        to_city = "Schiphol"

        self.logger.info(f"Performing ONE WAY flight search: {from_city} → {to_city}")

        try:
            # Step 1: Select One Way trip type
            self.logger.step(1, "Selecting One Way trip type")
            one_way_selected = self.select_one_way_trip()
            if not one_way_selected:
                self.logger.warning("Could not select One Way, proceeding with default trip type")

            # Step 2: Select departure airport
            self.logger.step(2, f"Selecting departure airport: {from_city}")
            self.select_from_airport(from_city)

            # Step 3: Select destination airport
            self.logger.step(3, f"Selecting destination airport: {to_city}")
            self.select_to_airport(to_city)

            # Step 4: Select departure date only
            self.logger.step(4, "Selecting departure date")
            self.select_departure_date()

            # Verify form before search
            if not self.verify_search_form_filled():
                self.logger.error("Search form not properly filled!")
                raise Exception("Search form validation failed")

            # Step 5: Click search and wait for results
            self.logger.step(5, "Clicking search flights button")
            search_button = self.waiter.wait_for_clickable(
                (By.XPATH, "//button[contains(text(), 'Search flights')]"), timeout=10
            )

            # Capture before search
            self.screenshot.capture_screenshot("before_search_one_way")
            self.screenshot.capture_element_screenshot(search_button, "search_button")

            # Click search button
            search_button.click()
            self.screenshot.capture_screenshot("after_search_one_way")

            # Wait for search to process - give it reasonable time
            self.logger.info("Waiting for search results to load...")
            time.sleep(8)  # Increased wait for search processing

            # Additional wait for any loading indicators to disappear
            try:
                self.waiter.wait_for_invisible(
                    (By.XPATH, "//*[contains(text(), 'Loading') or contains(text(), 'Searching')]"),
                    timeout=10
                )
            except:
                self.logger.info("No loading indicators found or they timed out")

            self.logger.info("Search completed - checking for results")

        except Exception as e:
            self.logger.error(f"One Way flight search failed: {e}")
            self.screenshot.capture_screenshot("one_way_search_error")
            raise

    def verify_search_form_filled(self):
        """Verify that the search form has been properly filled for One Way"""
        try:
            # Check if from airport is selected (not showing "Select")
            from_field = self.driver.find_element(By.XPATH, "//button[contains(., 'From')]")
            from_text = from_field.text
            has_from = "Select" not in from_text and "------" not in from_text
            
            # Check if to airport is selected
            to_field = self.driver.find_element(By.XPATH, "//button[contains(., 'To')]")
            to_text = to_field.text
            has_to = "Select" not in to_text and "------" not in to_text
            
            # For One Way, we don't check return date
            self.logger.info(f"From field filled: {has_from} (text: {from_text})")
            self.logger.info(f"To field filled: {has_to} (text: {to_text})")
            
            return has_from and has_to
        except Exception as e:
            self.logger.error(f"Error verifying search form: {e}")
            return False

    def is_search_session_initialized(self, search_term="searchId=", timeout=30):
        """Check if search session is properly initialized with configurable search term"""
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
        """Check if flight search results are displayed - dynamic version"""
        try:
            self.logger.info("Checking for search results dynamically...")

            # Assertion 1: Verify search session is initialized
            if not self.is_search_session_initialized():
                self.logger.warning("No active search session found (missing searchId)")
                return False

            # Get the searchId for logging
            current_url = self.driver.current_url
            search_id = current_url.split("searchId=")[-1] if "searchId=" in current_url else "unknown"
            self.logger.info(f"Checking results for search session: {search_id}")

            # Rest of your dynamic detection logic...
            # Method 1: Check for any result container patterns
            result_containers = self.driver.find_elements(By.XPATH, 
                "//*[contains(@class, 'result') or contains(@class, 'card') or contains(@class, 'item') or contains(@class, 'grid') or contains(@class, 'list')]")

            # Filter containers that likely contain flight data
            flight_containers = []
            for container in result_containers:
                container_text = container.text.lower()
                if any(keyword in container_text for keyword in ['flight', 'airline', 'depart', 'arrive', 'price', '₦', 'select']):
                    flight_containers.append(container)

            if flight_containers:
                self.logger.info(f"Found {len(flight_containers)} potential flight containers for search {search_id}")
                return True

            # Method 2: Check for data attributes that indicate dynamic content
            data_components = self.driver.find_elements(By.CSS_SELECTOR, '[data-sentry-component]')
            if data_components:
                self.logger.info(f"Found {len(data_components)} dynamic components for search {search_id}")
                return True

            # Method 3: Check for any structured data that looks like flight results
            page_text = self.driver.page_source.lower()
            flight_patterns = [
                r'\d{1,2}:\d{2}\s*[ap]m',  # Time patterns
                r'₦\s*\d+[,.\d]*',  # Price patterns
                r'\d+h\s*\d+m',  # Duration patterns
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
        """Select a flight by clicking 'View flight details' button - RELIABLE VERSION"""
        try:
            self.logger.info(f"Selecting flight at index {flight_index}")

            # Wait for results to be available
            if not self.are_search_results_displayed():
                self.logger.error("No search results available to select from")
                return False

            # Find buttons using the most reliable locator
            view_buttons = self.driver.find_elements(By.XPATH, "//button[normalize-space()='View flight details']")

            self.logger.info(f"Found {len(view_buttons)} 'View flight details' buttons")

            if not view_buttons:
                self.logger.error("No 'View flight details' buttons found")
                return False

            if flight_index >= len(view_buttons):
                self.logger.warning(f"Requested index {flight_index} not available, selecting first flight")
                flight_index = 0

            target_button = view_buttons[flight_index]

            # **RELIABLE SCROLLING APPROACH**
            self.logger.info("Scrolling to button with reliable method...")

            # 1. First scroll to make element visible in DOM
            self.driver.execute_script("arguments[0].scrollIntoView(true);", target_button)

            # 2. Fine-tune scroll to account for headers/fixed elements
            self.driver.execute_script("window.scrollBy(0, -100);")  # Adjust for header

            # 3. Wait for scroll to complete
            import time
            time.sleep(2)  # Crucial wait for scroll completion

            # 4. Use Actions to move to element (most reliable for interaction)
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(self.driver)
            actions.move_to_element(target_button).perform()
            time.sleep(1)

            # **RELIABLE CLICKING APPROACH**
            self.waiter.wait_for_clickable(target_button, timeout=10)

            # Take screenshot before click
            self.screenshot.capture_element_screenshot(target_button, f"before_click_flight_{flight_index}")

            # Try multiple click methods in order of reliability:
            try:
                # Method 1: JavaScript click (most reliable)
                self.driver.execute_script("arguments[0].click();", target_button)
                self.logger.info("Clicked using JavaScript - most reliable method")

            except Exception as js_error:
                self.logger.warning(f"JavaScript click failed: {js_error}, trying standard click")

                # Method 2: Standard Selenium click
                try:
                    target_button.click()
                    self.logger.info("Clicked using standard Selenium click")
                except Exception as std_error:
                    self.logger.error(f"All click methods failed: {std_error}")
                    return False

            # Wait for page transition
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
            full_name_input = self.waiter.wait_for_clickable(
                (By.XPATH, "//input[@placeholder='Enter your full name']"), timeout=10
            )
            full_name_input.clear()
            full_name_input.send_keys("Smoke Test")

            # Title selection
            title_dropdown = self.waiter.wait_for_clickable(
                (By.XPATH, "//div[contains(., 'Select title')]"), timeout=10
            )
            title_dropdown.click()

            mr_option = self.waiter.wait_for_clickable(
                (By.XPATH, "//span[normalize-space()='mr.']"), timeout=10
            )
            mr_option.click()

            # Gender selection
            gender_dropdown = self.waiter.wait_for_clickable(
                (By.XPATH, "//div[contains(., 'Select gender')]"), timeout=10
            )
            gender_dropdown.click()

            male_option = self.waiter.wait_for_clickable(
                (By.XPATH, "//span[normalize-space()='male']"), timeout=10
            )
            male_option.click()

            # Date of Birth
            dob_field = self.waiter.wait_for_clickable(
                (By.XPATH, "//div[contains(@id, 'headlessui-popover-button')]//div"), timeout=10
            )
            dob_field.click()

            # Select year
            year_select = self.waiter.wait_for_clickable(
                (By.XPATH, "//select[contains(@aria-label,'Choose the Year')]"), timeout=10
            )
            Select(year_select).select_by_visible_text("2002")

            # Select month
            month_select = self.waiter.wait_for_clickable(
                (By.XPATH, "//select[@aria-label='Choose the Month']"), timeout=10
            )
            Select(month_select).select_by_visible_text("June")

            # Phone number
            phone_input = self.waiter.wait_for_clickable(
                (By.XPATH, "//input[@placeholder='Phone number']"), timeout=10
            )
            phone_input.clear()
            phone_input.send_keys("7080702920")

            # Email
            email_input = self.waiter.wait_for_clickable(
                (By.XPATH, "//input[@placeholder='Enter your email address']"), timeout=10
            )
            email_input.clear()
            email_input.send_keys("elonmusk@yopmail.com")

            # Passport number
            passport_input = self.waiter.wait_for_clickable(
                (By.XPATH, "//input[@placeholder='Enter your passport number']"), timeout=10
            )
            passport_input.clear()
            passport_input.send_keys("1234567890123")

            # Country of origin
            country_origin_dropdown = self.waiter.wait_for_clickable(
                (By.XPATH, "//div[contains(., 'Select country of origin')]"), timeout=10
            )
            country_origin_dropdown.click()

            nigeria_option = self.waiter.wait_for_clickable(
                (By.XPATH, "//span[normalize-space()='nigeria']"), timeout=10
            )
            nigeria_option.click()

            # Issuing country
            issuing_country_dropdown = self.waiter.wait_for_clickable(
                (By.XPATH, "//div[contains(., 'Select issuing country')]"), timeout=10
            )
            issuing_country_dropdown.click()

            nigeria_issuing_option = self.waiter.wait_for_clickable(
                (By.XPATH, "//span[contains(text(),'nigeria')]"), timeout=10
            )
            nigeria_issuing_option.click()

            # Passport expiry date
            expiry_date_field = self.waiter.wait_for_clickable(
                (By.XPATH, "//div[contains(@id, 'headlessui-popover-button')]//div"), timeout=10
            )
            expiry_date_field.click()

            # Select expiry year
            expiry_year_select = self.waiter.wait_for_clickable(
                (By.XPATH, "//select[contains(@aria-label,'Choose the Year')]"), timeout=10
            )
            Select(expiry_year_select).select_by_visible_text("2011")

            return True
        except Exception as e:
            self.logger.error(f"Error filling passenger information: {e}")
            return False

    def save_passenger_info_and_continue(self):
        """Save passenger information and continue to next step"""
        try:
            save_button = self.waiter.wait_for_clickable(
                (By.XPATH, "//button[normalize-space()='Save changes & Continue']"), timeout=10
            )
            self.javascript.execute_script("arguments[0].scrollIntoView();", save_button)
            time.sleep(1)
            save_button.click()
            return True
        except:
            return False

    def is_payment_page_accessible(self):
        """Check if payment page is accessible"""
        try:
            payment_section = self.waiter.wait_for_visible(
                (By.XPATH, "//section[contains(., 'payment') or contains(., 'Payment')]"), timeout=10
            )
            return payment_section.is_displayed()
        except:
            return False

    def select_payment_method(self):
        """Select payment method from available options"""
        try:
            flutterwave_option = self.waiter.wait_for_clickable(
                (By.XPATH, "//li[contains(., 'Flutterwave')]"), timeout=10
            )
            flutterwave_option.click()
            return True
        except:
            return False

    def proceed_to_payment(self):
        """Proceed to payment final step"""
        try:
            proceed_button = self.waiter.wait_for_clickable(
                (By.XPATH, "//button[normalize-space()='Proceed to payment']"), timeout=10
            )
            proceed_button.click()
            return True
        except:
            return False

    def is_error_message_displayed(self):
        """Check if any error message is displayed on the page"""
        try:
            error_elements = self.driver.find_elements(
                By.XPATH, "//div[contains(@class, 'error') or contains(@class, 'Error')]"
            )
            return len(error_elements) > 0
        except:
            return False

    def get_error_message_text(self):
        """Get error message text if present"""
        try:
            error_elements = self.driver.find_elements(
                By.XPATH, "//div[contains(@class, 'error') or contains(@class, 'Error')]"
            )
            if error_elements:
                return error_elements[0].text
            return None
        except:
            return None

    def is_page_loaded(self, timeout=15):
        """Check if flight booking page is fully loaded and ready for interaction"""
        try:
            # Wait for document to be completely loaded
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

            # Confirm key element is visible
            element = self.pageinfo.find_element(self.page_indicator, timeout)
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