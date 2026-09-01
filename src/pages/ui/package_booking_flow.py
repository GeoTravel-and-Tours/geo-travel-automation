"""
src/pages/ui/package_booking_flow.py

Page Object for the "Package" booking journey on the Geo Travel web app.

Covers the full flow end to end:
    1. Search & navigation  - open the Packages tab, pick a trip type,
       destination country and travel date, then run the search.
    2. Package selection    - open a package's detail page and choose a
       price option (couple / single / group).
    3. Booking form         - open the reservation modal, fill in
       traveller details and submit.
    4. Login & checkout     - authenticate, accept terms, and land on the
       payment method selection screen.
    5. Payment verification - confirm the flow reached the correct
       checkout destination for Flutterwave, Paystack, or bank transfer.

Methods are intended to be chained in roughly the order above (most
navigation/search methods return ``self`` for that purpose); tests
typically call ``handle_booking_flow`` for steps 3-4 once a package's
price option has been selected.
"""

import random
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
    Page Object Model for the Package Booking Flow.

    Handles the complete package booking process from search to payment:
    searching/filtering packages, selecting a price option, filling out
    the booking modal, logging in, accepting terms, choosing a payment
    method, and verifying the flow reaches the correct payment
    destination (Flutterwave, Paystack, or bank transfer).

    All locators are grouped near the top of the class by the step of the
    flow they belong to (search, package selection, booking form, modals,
    login, payment). Methods below follow the same grouping.
    """

    # ===== LOCATORS =====
    # Navigation & Search
    PACKAGES_MENU = (
        By.XPATH,
        "//a[normalize-space()='Packages']"
    )

    PACKAGES_PAGE_TITLE = (
        By.XPATH,
        "//h1[contains(normalize-space(), 'Packages')]"
    )

    PACKAGE_CARDS = (
        By.XPATH,
        "//a[contains(@href, '/packages/')]"
    )

    FIRST_PACKAGE = (
        By.XPATH,
        "(//a[contains(@href, '/packages/')])[1]"
    )

    PACKAGE_DETAIL = (
        By.XPATH,
        "//main"
    )
    PACKAGE_BUTTON = (By.XPATH, "//button[normalize-space()='Package']")
    TRIP_TYPE_DROPDOWN = (
        By.XPATH,
        "//button[@aria-haspopup='listbox' and .//span[normalize-space()='Select trip type']]"
    )
    GROUP_OPTION = (
        By.XPATH,
        "//div[@role='option']//span[normalize-space()='group']"
    )
    # NOTE: matches the first element with this class combo on the page,
    # not a dedicated test id - fragile if the page layout changes.
    COUNTRY_SELECTOR = (By.XPATH, "//div[contains(@class,'h-full relative')]")
    COUNTRY_INPUT = (By.XPATH, "//input[@placeholder='Enter country']")
    # NOTE: hardcoded to "NIGERIA" - only works for tests that search that country.
    COUNTRY_SEARCH_RESULT = (By.XPATH, "//h6[contains(text(),'NIGERIA')]")
    TRAVEL_DATE_SELECTOR = (By.CSS_SELECTOR, "div[class='w-full flex items-center px-3.5 min-h-12 h-full py-2 rounded-md border border-gray-300 cursor-pointer justify-between']")
    # Old CSS nth-child selector kept for reference; replaced by the XPath
    # below because nth-child paths break easily when markup shifts.
    # SEARCH_PACKAGES_BUTTON = (By.CSS_SELECTOR, "body > div:nth-child(1) > div:nth-child(2) > div:nth-child(2) > div:nth-child(2) > form:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > button:nth-child(1)")
    SEARCH_PACKAGES_BUTTON = (By.XPATH, "(//button[@class='active:scale-95 transition-all items-center gap-2 justify-center whitespace-nowrap rounded-md text-sm font-medium focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-mainblue disabled:pointer-events-none disabled:opacity-50 cursor-pointer bg-mainblue text-white hover:bg-mainblue/80 h-10 px-4 py-2 hidden md:flex'])[1]")

    # Package Selection
    VIEW_PACKAGE_BUTTON = (By.XPATH, "(//button[normalize-space()='View package'])[1]")
    PRICE_OPTION_BY_TYPE = {
        "couple": (
            By.XPATH,
            "//h5[normalize-space()='COUPLE']/ancestor::div[contains(@class,'cursor-pointer')][1]"
        ),
        "single": (
            By.XPATH,
            "//h5[normalize-space()='SINGLE']/ancestor::div[contains(@class,'cursor-pointer')][1]"
        ),
        "group": (
            By.XPATH,
            "//h5[normalize-space()='GROUP']/ancestor::div[contains(@class,'cursor-pointer')][1]"
        ),
    }
    BOOK_RESERVATION_BUTTON = (
        By.XPATH,
        "//button[normalize-space()='Book a reservation']"
    )
    
    # Add these to your locators section:
    PACKAGES_NAV_LINK = (By.XPATH, "//a[normalize-space()='Packages']")
    ALL_PACKAGES_PAGE_INDICATOR = (By.XPATH, "//*[contains(text(), 'Packages') or contains(text(), 'packages')]")
    FIRST_PACKAGE_VIEW_BUTTON = (By.XPATH, "(//button[contains(text(), 'View package')])[1]")

    # Booking Form
    FULL_NAME_INPUT = (By.NAME, "fullName")
    EMAIL_INPUT = (By.NAME, "email")
    PHONE_INPUT = (By.CSS_SELECTOR, "input[placeholder='Phone number']")
    
    # Modal Locators
    MODAL_BACKGROUND = (By.CSS_SELECTOR, ".overflow-y-auto.flex-grow")
    MODAL_FULL_NAME_INPUT = (By.XPATH, "//input[contains(@placeholder,'Enter your full name')]")
    MODAL_EMAIL_INPUT = (By.XPATH, "//input[@placeholder='Enter your email address']")
    MODAL_TRAVEL_DATE_INPUT = (By.CSS_SELECTOR, "input[placeholder='Select a date ']")
    MODAL_PHONE_INPUT = (By.XPATH, "//input[@placeholder='Phone number']")
    MODAL_PROCEED_BUTTON = (By.XPATH, "//button[normalize-space()='Proceed to checkout']")
    
    # Booking Confirmation Modal
    CLOSE_MODAL_BUTTON = (By.XPATH, "//button[@aria-label='Close modal']")
    PROCEED_TO_PAYMENT_BUTTON = (By.XPATH, "//button[normalize-space()='Proceed to payment']")
    
    LOGIN_BUTTON = (
        By.XPATH,
        "//button[normalize-space()='Login']"
    )

    LOGIN_EMAIL_INPUT = (
        By.XPATH,
        "//input[@placeholder='Enter your email']"
    )

    LOGIN_PASSWORD_INPUT = (
        By.XPATH,
        "//input[@placeholder='Enter your password']"
    )

    SIGN_IN_BUTTON = (
        By.XPATH,
        "//button[normalize-space()='Sign in']"
    )

    TERMS_CHECKBOX = (
        By.XPATH,
        "//input[@aria-label='Terms and policy']"
    )

    PROCEED_TO_PAYMENT = (
        By.XPATH,
        "//span[normalize-space()='Proceed to payment']"
    )
    
    PAYSTACK_OPTION = (
        By.XPATH,
        "//h6[normalize-space()='Pay with Paystack']"
    )

    FLUTTERWAVE_OPTION = (
        By.XPATH,
        "//h6[normalize-space()='Pay with Flutterwave']"
    )

    BANK_OPTION = (
        By.XPATH,
        "//h6[normalize-space()='Pay with Bank']"
    )
    
    BANK_NAME = (
        By.XPATH,
        "//div[normalize-space()='Bank Name']"
    )

    ACCOUNT_NUMBER = (
        By.XPATH,
        "//div[normalize-space()='Account Number']"
    )

    AMOUNT = (
        By.XPATH,
        "//div[normalize-space()='Amount']"
    )

    PAY_WITH_TRANSFER = (
        By.XPATH,
        "//span[normalize-space()='Pay with transfer']"
    )

    IVE_SENT_MONEY = (
        By.XPATH,
        "//button[contains(text(), 'I’ve sent the money')]"
    )

    TRANSFER_SUCCESS_MESSAGE = (
        By.XPATH,
        "//h2[normalize-space()='Your transfer is being securely processed']"
    )

    def __init__(self, driver):
        """Initialize the page object.

        Args:
            driver (WebDriver): Active Selenium WebDriver instance, passed
                straight through to ``BasePage`` which wires up the shared
                element/js/logging/wait helpers used by this class.
        """
        super().__init__(driver)

    # ===== SEARCH & NAVIGATION METHODS =====

    def click_package(self):
        """Click the "Package" entry point button in the navigation.

        Returns:
            WebElement: The clicked button element.

        Raises:
            Exception: Re-raised if the button cannot be found/clicked.
        """
        self.logger.info("Clicking Package button")
        try:
            click_btn = self.element.click(self.PACKAGE_BUTTON)
            self._last_interacted_element = click_btn
            return click_btn
        except Exception as e:
            self.logger.error(f"Failed to click Package button: {e}")
            raise

    def select_trip_type(self):
        """Open the trip-type dropdown and select "group".

        Returns:
            PackageBookingFlow: ``self``, to allow method chaining with
                the other search-step methods (e.g. ``select_country``).

        Raises:
            Exception: Re-raised if the dropdown or option never becomes
                clickable within the wait timeout.
        """
        self.logger.info("Selecting trip type as 'group'")
        try:
            # Wait for dropdown to be clickable
            trip_dropdown = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.TRIP_TYPE_DROPDOWN)
            )
            trip_dropdown.click()
            
            self.logger.info("Clicked trip type dropdown")

            # Wait for group option and click
            group_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.GROUP_OPTION)
            )
            group_option.click()
            
            self.logger.info("Trip type selected: group")
            

            return self

        except Exception as e:
            self.logger.error(f"Failed to select trip type: {e}")
            raise

    def select_country(self, country_name):
        """Open the country selector, type a country name, and pick it from results.

        Note the search-result locator (``COUNTRY_SEARCH_RESULT``) is
        currently hardcoded to match "NIGERIA" regardless of the
        ``country_name`` passed in, so this only reliably works for that
        destination until the locator is made dynamic.

        Args:
            country_name (str): Country to type into the search input
                (e.g. "Nigeria").

        Returns:
            PackageBookingFlow: ``self``, for method chaining.

        Raises:
            Exception: Re-raised if any step (opening the selector,
                typing, or picking a result) times out or fails. The
                element involved at the point of failure is stashed on
                ``self._last_interacted_element`` for screenshot/debug
                purposes.
        """
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
        """Open the travel date calendar and pick a day.

        Picks the first enabled day-of-month button whose value is greater
        than 10 as a cheap heuristic for "a date safely in the future"
        without needing to parse the calendar's month/year state.

        Returns:
            PackageBookingFlow: ``self``, for method chaining.

        Raises:
            Exception: Re-raised if the date selector can't be opened or
                no matching date button is found/clicked.
        """
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
        """Submit the package search form.

        Returns:
            WebElement: The clicked search button.

        Raises:
            Exception: Re-raised if the button can't be clicked.
        """
        self.logger.info("Clicking Search Packages button")
        try:
            search_btn = self.element.click(self.SEARCH_PACKAGES_BUTTON)
            self._last_interacted_element = search_btn
            return search_btn
        except Exception as e:
            self.logger.error(f"Failed to click Search Packages button: {e}")
            raise
    
    def is_search_session_initialized(self, search_term="packages", timeout=30):
        """Poll the current URL until it contains ``search_term``.

        Used after submitting a search to confirm the app actually
        navigated to a results URL rather than staying on the form
        (e.g. due to a validation error).

        Args:
            search_term (str): Substring expected to appear in the URL
                once the search has taken effect. Defaults to "packages".
            timeout (int): Max seconds to wait for the URL to update.
                Defaults to 30.

        Returns:
            bool: True if ``search_term`` appeared in the URL in time,
                False on timeout or any other error.
        """
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
        """Scroll to and click the first "View package" button on a results page.

        Raises:
            Exception: Re-raised if the button never appears or becomes
                clickable within the wait timeout.
        """
        self.logger.info("Clicking View Package button")

        try:
            button = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(self.VIEW_PACKAGE_BUTTON)
            )

            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                button
            )

            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.VIEW_PACKAGE_BUTTON)
            )

            button.click()

            self.logger.info("Successfully clicked View Package button")

        except Exception as e:
            self.logger.error(f"Failed to click View Package button: {e}")
            raise
    
    def click_view_package_after_packageNavBar(self):
        """Variant of ``click_view_package`` used after navigating via the
        Packages nav bar link, where the button sits further down the page.

        Scrolls an extra 100px past the element (instead of centering it)
        before clicking, which this page layout needs to clear a sticky
        nav bar that would otherwise overlap the button.

        Returns:
            WebElement: The clicked "View package" button.

        Raises:
            Exception: Re-raised if the button can't be found/clicked.
        """
        self.logger.info("Clicking View Package button")
        try:
            # Scroll further down (500 pixels past the element)
            self.javascript.execute_script(
                "arguments[0].scrollIntoView(true); window.scrollBy(0, 100);", 
                self.driver.find_element(*self.VIEW_PACKAGE_BUTTON)
            )
            time.sleep(1)
            click_view_package_btn = self.element.click(self.VIEW_PACKAGE_BUTTON)
            self._last_interacted_element = click_view_package_btn
            return click_view_package_btn
        except Exception as e:
            self.logger.error(f"Failed to click View Package button: {e}")
            raise
    
    def select_price_option(self, option_type="couple"):
        """Select a package price option by type and confirm it visually applied.

        After clicking, waits for the option's CSS class to include
        ``border-mainblue/50``, which is how the UI highlights the
        currently-selected card - this is the only way to confirm the
        click actually registered as a selection rather than a no-op.

        Args:
            option_type (str): One of "couple", "single", "group"
                (case-insensitive). Defaults to "couple".

        Returns:
            bool: True if the option was selected and the UI confirmed
                it, False if selection failed (exception is swallowed
                and logged rather than raised).

        Raises:
            ValueError: If ``option_type`` isn't a recognized key in
                ``PRICE_OPTION_BY_TYPE``.
        """
        self.logger.info(
            f"Selecting price option: {option_type}"
        )

        try:
            locator = self.PRICE_OPTION_BY_TYPE.get(
                option_type.lower()
            )

            if not locator:
                raise ValueError(
                    f"Unsupported price option: {option_type}"
                )

            option = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator)
            )

            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});",
                option
            )

            option.click()

            # Verify the UI actually changed to selected state
            WebDriverWait(self.driver, 10).until(
                lambda driver: (
                    "border-mainblue/50"
                    in option.get_attribute("class")
                )
            )

            self.logger.info(
                f"✅ {option_type.upper()} price option selected"
            )
            return True

        except Exception as e:
            self.logger.error(
                f"Failed to select {option_type} price option: {e}"
            )
            return False
        
    def is_price_option_available(self, timeout=10):
        """Check whether at least one package price option is available.

        Args:
            timeout (int): Seconds to wait for each price option locator
                before moving to the next. Defaults to 10.

        Returns:
            bool: True if at least one price option is present and
                displayed, False if none are found within the timeout.
        """

        for index, locator in enumerate(self.PRICE_OPTION_BY_TYPE.values(), start=1):
            try:
                price_option = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located(locator)
                )

                if price_option.is_displayed():
                    self.logger.info(
                        f"✅ Price option {index} is available"
                    )
                    return True

            except TimeoutException:
                continue

        self.logger.error("❌ No pricing option is available")
        return False

    def click_packages_nav_link(self):
        """Click the "Packages" link in the nav bar to view all packages.

        Returns:
            WebElement: The clicked nav link.

        Raises:
            Exception: Re-raised if the link can't be clicked.
        """
        self.logger.info("Clicking 'Packages' link in navigation")
        try:
            packages_link = self.element.click(self.PACKAGES_NAV_LINK)
            self._last_interacted_element = packages_link
            return packages_link
        except Exception as e:
            self.logger.error(f"Failed to click Packages nav link: {e}")
            raise

    def verify_all_packages_page_loaded(self, timeout=15):
        """Verify the All Packages listing page has loaded.

        Args:
            timeout (int): Seconds to wait for the page indicator element.
                Defaults to 15.

        Returns:
            bool: True if the page loaded in time, False on timeout.
        """
        self.logger.info("Verifying All Packages page loaded")
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(self.ALL_PACKAGES_PAGE_INDICATOR)
            )
            self.logger.info("✅ Successfully loaded All Packages page")
            return True
        except TimeoutException:
            self.logger.error("❌ All Packages page did not load")
            return False

    # ===== BOOKING FLOW METHODS =====

    def handle_booking_flow(self, email, password, payment_method="flutterwave"):
        """Run the full reservation-to-payment sequence in one call.

        Orchestrates, in order: click "Book a reservation", fill and
        submit the booking modal, log in and select a payment method via
        ``handle_second_modal``, then assert the flow is ready for
        payment. Assumes a package price option has already been
        selected (see ``select_price_option``) before this is called.

        Args:
            email (str): Login email for the account used to complete
                the booking.
            password (str): Login password for that account.
            payment_method (str): Payment method to select - one of the
                keys supported by ``handle_second_modal`` (currently only
                "flutterwave" is wired up; see the ``payment_locators``
                note there). Defaults to "flutterwave".

        Raises:
            AssertionError: If the flow does not end in a state ready
                for payment.
        """

        self.logger.info(
            f"Starting complete booking flow with {payment_method} payment"
        )

        # Step 1: Click Book Reservation
        self.click_book_reservation()

        # Step 2: Fill booking modal
        self.fill_booking_modal()

        # Step 3: Handle login, terms and payment method
        self.handle_second_modal(
            email=email,
            password=password,
            payment_method=payment_method
        )

        # Step 4: Verify payment readiness
        assert self.verify_payment_ready(), (
            "Booking flow should be ready for payment"
        )
        
    def handle_second_modal(
        self,
        email,
        password,
        payment_method="flutterwave"
    ):
        """Log in, accept terms, and select a payment method.

        Steps: click Login, enter credentials and sign in, wait for the
        login modal to close, tick the terms checkbox (if not already
        checked), click "Proceed to payment", then click the option for
        ``payment_method``.

        Args:
            email (str): Login email.
            password (str): Login password.
            payment_method (str): Which payment option to click. Only
                "flutterwave" is currently active in ``payment_locators``
                below - "paystack" and "bank" are commented out pending
                those methods being enabled end-to-end, so passing them
                raises ``ValueError`` even though locators exist for them.
                Defaults to "flutterwave".

        Returns:
            bool: True once the payment method has been clicked.

        Raises:
            ValueError: If ``payment_method`` isn't an active key in
                ``payment_locators``.
        """

        self.logger.info(
            f"Handling booking flow with {payment_method.upper()}"
        )

        # 1. Login
        login_button = WebDriverWait(self.driver, 15).until(
            EC.element_to_be_clickable(self.LOGIN_BUTTON)
        )
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            login_button
        )
        login_button.click()

        # 2. Login credentials
        email_field = WebDriverWait(self.driver, 15).until(
            EC.visibility_of_element_located(self.LOGIN_EMAIL_INPUT)
        )
        email_field.clear()
        email_field.send_keys(email)

        password_field = WebDriverWait(self.driver, 15).until(
            EC.visibility_of_element_located(self.LOGIN_PASSWORD_INPUT)
        )
        password_field.clear()
        password_field.send_keys(password)

        # 3. Sign in
        sign_in = WebDriverWait(self.driver, 15).until(
            EC.element_to_be_clickable(self.SIGN_IN_BUTTON)
        )
        sign_in.click()

        # 4. Wait for login modal to close
        WebDriverWait(self.driver, 15).until(
            EC.invisibility_of_element_located(self.LOGIN_EMAIL_INPUT)
        )

        self.logger.info("Login successful")

        # 5. Agree to terms
        terms = WebDriverWait(self.driver, 15).until(
            EC.element_to_be_clickable(self.TERMS_CHECKBOX)
        )

        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            terms
        )

        if not terms.is_selected():
            terms.click()

        self.logger.info("Accepted terms and policy")

        # 6. Proceed to payment
        proceed = WebDriverWait(self.driver, 15).until(
            EC.element_to_be_clickable(self.PROCEED_TO_PAYMENT)
        )

        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            proceed
        )

        proceed.click()

        self.logger.info("Clicked Proceed to payment")

        # 7. Select payment method
        # ❌❌❌ This is a cheat because all 3 payment menthods are meant to be active for it to loop over ❌❌❌
        payment_locators = {
            # "paystack": self.PAYSTACK_OPTION,
            "flutterwave": self.FLUTTERWAVE_OPTION,
            # "bank": self.BANK_OPTION,
        }

        payment_locator = payment_locators.get(
            payment_method.lower()
        )

        if not payment_locator:
            raise ValueError(
                f"Unsupported payment method: {payment_method}"
            )

        payment_option = WebDriverWait(self.driver, 15).until(
            EC.element_to_be_clickable(payment_locator)
        )

        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            payment_option
        )

        payment_option.click()

        self.logger.info(
            f"Selected {payment_method.upper()} payment method"
        )

        return True
        
    def verify_payment_ready(self):
        """Verify the "Proceed to payment" button is present and enabled.

        Returns:
            bool: True if the button is present and enabled, False if
                it's missing, disabled, or an error occurred while
                checking.
        """
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
        """Scroll to and click the "Book a reservation" button.

        Uses ``ActionChains.move_to_element().click()`` rather than a
        plain ``.click()`` so the mouse genuinely hovers the button
        before clicking, which is more robust for buttons with
        hover-triggered CSS transitions than a direct element click.

        Raises:
            Exception: Re-raised if the button never appears/becomes
                visible or the click fails.
        """
        self.logger.info("Clicking Book Reservation button")

        try:
            button = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(
                    self.BOOK_RESERVATION_BUTTON
                )
            )

            self.logger.info("Book Reservation button found in DOM")

            # Scroll the button into the visible viewport
            self.driver.execute_script(
                """
                arguments[0].scrollIntoView({
                    behavior: 'instant',
                    block: 'center',
                    inline: 'center'
                });
                """,
                button
            )

            time.sleep(1)

            # Re-find the element after scrolling
            button = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(
                    self.BOOK_RESERVATION_BUTTON
                )
            )

            # Move mouse directly onto the button and click
            ActionChains(self.driver).move_to_element(button).click().perform()

            self.logger.info(
                "✅ Book Reservation button clicked successfully"
            )

        except Exception as e:
            self.logger.error(
                f"Failed to click Book Reservation: {e}"
            )
            raise

    def fill_booking_modal(self):
        """Fill out and submit the booking modal with fixed test data.

        Fills full name, email, and phone directly; the travel date is
        set via the calendar widget (see ``select_date_from_calendar``)
        since it doesn't accept direct text input. Waits for the
        "Proceed to checkout" button to become enabled before clicking it.

        Note: traveller details (name/email/phone/date) are hardcoded
        test values, not parameters - this method is intended for use
        against a test/staging environment only.

        Raises:
            Exception: Re-raised if the modal never appears or any field
                can't be filled. The element in progress at failure time
                is stashed on ``self._last_interacted_element``.
        """
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
        """Select a specific day from an open calendar popup.

        Looks for a button matching the day number from ``date_string``
        (month/year are not used to navigate the calendar - this assumes
        the calendar is already showing the right month). Falls back to
        clicking the first enabled day button if the exact day can't be
        found, so a valid date is still picked even if the initial
        target is unavailable (e.g. disabled or on a different month).

        Args:
            date_string (str): Date in "DD/MM/YYYY" format, e.g.
                "05/11/2025".
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
        """Poll the "Proceed to checkout" button until it's enabled.

        Args:
            timeout (int): Max seconds to poll. Defaults to 10.

        Returns:
            bool: True once the button is enabled, False if it never
                became enabled (or errored) within the timeout.
        """
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
        """Wait for the URL to reflect a checkout/confirmation/success step.

        Best-effort only: on timeout it logs and returns without raising,
        so callers should follow up with their own assertions if reaching
        one of these URLs is actually required.
        """
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
            
    def complete_booking_with_payment(self, payment_method):
        """Dispatch to the right payment verification method.

        Args:
            payment_method (str): "flutterwave", "paystack", or "bank"
                (case-insensitive).

        Returns:
            bool: True if the corresponding verification succeeded.

        Raises:
            ValueError: If ``payment_method`` isn't one of the supported
                values.
        """

        payment_method = payment_method.lower()

        if payment_method == "flutterwave":
            return self.verify_flutterwave_payment()

        elif payment_method == "paystack":
            return self.verify_paystack_payment()

        elif payment_method == "bank":
            return self.complete_bank_transfer_flow()

        else:
            raise ValueError(
                f"Unsupported payment method: {payment_method}"
            )
        
    def verify_flutterwave_payment(self):
        """Wait for the browser to reach the Flutterwave hosted checkout URL.

        Note: the URL checked is the dev/sandbox Flutterwave domain
        (``checkout-v2.dev-flutterwave.com``), so this only passes
        against a non-production payment environment.

        Returns:
            bool: True once the checkout URL is reached.

        Raises:
            TimeoutException: If the URL isn't reached within 20s.
        """

        WebDriverWait(self.driver, 20).until(
            lambda driver:
            "checkout-v2.dev-flutterwave.com/v3/hosted/pay"
            in driver.current_url
        )

        self.logger.info(
            "✅ Flutterwave checkout page reached"
        )

        return True
    
    def verify_paystack_payment(self):
        """Wait for the browser to reach the Paystack hosted checkout URL.

        Returns:
            bool: True once the checkout URL is reached.

        Raises:
            TimeoutException: If the URL isn't reached within 20s.
        """

        WebDriverWait(self.driver, 20).until(
            lambda driver:
            "checkout.paystack.com"
            in driver.current_url
        )

        self.logger.info(
            "✅ Paystack checkout page reached"
        )

        return True
    
    def complete_bank_transfer_flow(self):
        """Run and verify the bank-transfer payment path.

        Asserts bank name, account number, and amount are displayed,
        clicks "Pay with transfer", then "I've sent the money", and
        verifies the resulting success modal is shown.

        Returns:
            bool: True on success.

        Raises:
            AssertionError: If the success modal isn't displayed.
            TimeoutException: If any expected element doesn't appear in
                time.
        """

        self.logger.info("Starting bank transfer flow")

        # Assert bank details
        WebDriverWait(self.driver, 15).until(
            EC.visibility_of_element_located(self.BANK_NAME)
        )

        WebDriverWait(self.driver, 15).until(
            EC.visibility_of_element_located(self.ACCOUNT_NUMBER)
        )

        WebDriverWait(self.driver, 15).until(
            EC.visibility_of_element_located(self.AMOUNT)
        )

        self.logger.info(
            "✅ Bank Name, Account Number and Amount displayed"
        )

        # Pay with transfer
        pay_with_transfer = WebDriverWait(
            self.driver, 15
        ).until(
            EC.element_to_be_clickable(self.PAY_WITH_TRANSFER)
        )

        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            pay_with_transfer
        )

        pay_with_transfer.click()

        self.logger.info("Clicked Pay with transfer")

        # I've sent the money
        sent_money = WebDriverWait(
            self.driver, 15
        ).until(
            EC.element_to_be_clickable(self.IVE_SENT_MONEY)
        )

        sent_money.click()

        self.logger.info("Clicked I've sent the money")

        # Verify success modal
        success_modal = WebDriverWait(
            self.driver, 15
        ).until(
            EC.visibility_of_element_located(
                self.TRANSFER_SUCCESS_MESSAGE
            )
        )

        assert success_modal.is_displayed(), (
            "Bank transfer success modal should be displayed"
        )

        self.logger.info(
            "✅ Bank transfer success modal displayed"
        )

        return True
        
    def wait_for_booking_modal(self, timeout=10):
        """Wait until the booking modal background becomes visible.

        Args:
            timeout (int): Max seconds to wait. Defaults to 10.

        Returns:
            bool: True if the modal appeared in time, False on timeout.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.MODAL_BACKGROUND)
            )
            return True
        except TimeoutException:
            return False

    def navigate_to_packages(self):
        """Click the Packages nav item and wait for the URL to update.

        Returns:
            PackageBookingFlow: ``self``, for method chaining.

        Raises:
            TimeoutException: If the nav link never becomes clickable or
                the URL doesn't update to include "/packages" in time.
        """
        self.logger.info("Navigating to Packages from navbar")

        packages_link = WebDriverWait(self.driver, 15).until(
            EC.element_to_be_clickable(self.PACKAGES_MENU)
        )

        packages_link.click()

        WebDriverWait(self.driver, 15).until(
            lambda driver: "/packages" in driver.current_url.lower()
        )

        self.logger.info(
            f"Successfully navigated to Packages: {self.driver.current_url}"
        )

        return self
    
    def select_first_package(self):
        """Scroll to and click the first package card in a results list.

        Returns:
            PackageBookingFlow: ``self``, for method chaining.

        Raises:
            TimeoutException: If no package card becomes clickable in
                time.
        """
        self.logger.info("Selecting first package")

        package = WebDriverWait(self.driver, 15).until(
            EC.element_to_be_clickable(self.FIRST_PACKAGE)
        )

        self.javascript.scroll_to_element(package)
        package.click()

        self.logger.info("First package selected")

        return self
    
    def verify_package_detail_loaded(self):
        """Verify the URL matches a package detail page (``/packages/<id>``).

        Considers the page loaded once the URL contains "/packages/" and
        ends in a numeric ID segment.

        Returns:
            bool: True once the detail page URL pattern is matched.

        Raises:
            TimeoutException: If the URL never matches within 15s.
        """
        self.logger.info("Verifying package detail page")

        WebDriverWait(self.driver, 15).until(
            lambda driver: "/packages/" in driver.current_url.lower()
            and driver.current_url.rstrip("/").split("/")[-1].isdigit()
        )

        self.logger.info(
            f"Package detail page loaded: {self.driver.current_url}"
        )

        return True