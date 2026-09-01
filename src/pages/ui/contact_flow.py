"""
src/pages/ui/contact_flow.py

Page Object for the Geo Travel "Contact Support" flow.

Covers:
    1. Navigation    - click "Contact" in the nav menu and confirm the
                        contact page loaded.
    2. Contact form  - fill name/email/phone/message, pick a support type
                        from the dropdown (random by default, or a caller
                        supplied value), accept the privacy checkbox, and
                        submit.
    3. Confirmation  - verify the "Thank you for reaching out" success
                        message.
    4. Related links - navigate to the FAQ page and the Privacy Statement
                        footer link.

Tests typically chain ``navigate_to_contact()`` -> ``fill_contact_form(...)``
-> ``submit_form()`` -> ``is_success_displayed()``.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from src.core.base_page import BasePage
from selenium.common.exceptions import TimeoutException
import time


class ContactPage(BasePage):
    """Page Object for the Contact Support form, FAQ link, and privacy link.

    Locators are grouped by section: navigation, form fields, the support
    type dropdown (plus a template locator used to match an option by its
    lower-cased text), the privacy checkbox, and the success/FAQ/footer
    elements. Self-contained - no coupling to other page objects.
    """

    def __init__(self, driver):
        """Initialize the page object.

        Args:
            driver (WebDriver): Active Selenium WebDriver instance, passed
                through to ``BasePage``.
        """
        super().__init__(driver)
    
    # ========== LOCATORS ==========
    # Navigation
    CONTACT_MENU = (By.XPATH, "//a[normalize-space()='Contact']")
    CONTACT_PAGE_TITLE = (By.XPATH, "//h1[contains(text(), 'Contact')]")
    
    # Form Elements
    NAME_INPUT = (By.XPATH, "//input[@placeholder='Enter your full name']")
    EMAIL_INPUT = (By.XPATH, "//input[@placeholder='Enter your email address']")
    PHONE_INPUT = (By.XPATH, "//input[@placeholder='Phone number']")
    
    # Support Type Dropdown
    SUPPORT_TYPE_DROPDOWN = (By.XPATH, "//label[contains(text(), 'Type of support')]/following-sibling::div//button")
    SUPPORT_TYPE_OPTIONS = (
        By.XPATH,
        "//*[@role='option']"
    )

    SUPPORT_TYPE_OPTION_BY_TEXT = (
        By.XPATH,
        "//*[@role='option']["
        "translate(normalize-space(.), "
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
        "'abcdefghijklmnopqrstuvwxyz') = '{}'"
        "]"
    )

    # Available support types
    # NOTE: this list must exactly match the dropdown's live option text
    # (matched case-insensitively via SUPPORT_TYPE_OPTION_BY_TEXT) - recent
    # git history shows this list flip-flopping between "Other" and
    # "Others", so double check the live UI copy before changing it again.
    SUPPORT_TYPES = [
        "General Inquiry",
        "Account & Login Issues",
        "Booking & Reservations",
        "Technical Support",
        "Payments & Billing",
        "Refunds & Cancellations",
        "Other"
    ]
    
    MESSAGE_TEXTAREA = (By.XPATH, "//textarea[@placeholder='How can we help?']")
    
    # Privacy Checkbox
    PRIVACY_CHECKBOX = (By.ID, "privacy")
    PRIVACY_LABEL = (By.XPATH, "//label[@for='privacy']")
    
    SUBMIT_BUTTON = (By.XPATH, "//button[normalize-space()='Submit']")
    
    # Success Message
    SUCCESS_TITLE = (By.XPATH, "//h5[contains(text(), 'Thank you for reaching out')]")
    SUCCESS_MESSAGE = (By.XPATH, "//p[@class='text-sm text-gray-600 mt-1.5 max-w-xl mx-auto']")
    
    # FAQ Section
    READ_FAQS_BTN = (By.XPATH, "//h3[normalize-space()='Read FAQs']")
    FAQ_PAGE_TITLE = (By.XPATH, "//h1[contains(text(),'Frequently asked')]")
    STILL_HAVE_QUESTIONS = (By.XPATH, "//a[contains(@class, 'mt-10 flex items-center')]")
    
    # Footer Links
    PRIVACY_STATEMENT = (By.XPATH, "//a[normalize-space()='Privacy Statement']")
    
    # ========== PAGE METHODS ==========
    
    def open(self, base_url):
        """Open the application homepage directly via ``driver.get``.

        Args:
            base_url (str): Full URL of the homepage to load.

        Returns:
            ContactPage: ``self``, for method chaining.
        """
        self.logger.info("Opening application homepage")
        self.driver.get(base_url)
        return self

    def navigate_to_contact(self):
        """Click "Contact" in the nav menu and verify the contact page loaded.

        Returns:
            ContactPage: ``self``, for method chaining.

        Raises:
            AssertionError: If the URL doesn't contain "contact" after
                navigating.
            Exception: Re-raised for any other navigation failure.
        """
        self.logger.info("Navigating to Contact page")

        try:
            contact_menu = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable(self.CONTACT_MENU)
            )
            contact_menu.click()

            # Wait for page to load
            self.waiter.wait_for_present(self.CONTACT_PAGE_TITLE, timeout=15)

            assert "contact" in self.driver.current_url.lower(), "URL should contain 'contact'"

            self.logger.info("Successfully navigated to Contact page")
            return self

        except Exception as e:
            self.logger.error(f"Failed to navigate to Contact page: {e}")
            raise

    def fill_contact_form(self, name, email, phone, message, support_type=None):
        """Fill out the full contact form, including support type and privacy consent.

        If ``support_type`` isn't given, a random value from
        ``SUPPORT_TYPES`` is chosen and matched against the dropdown
        options case-insensitively (see ``SUPPORT_TYPE_OPTION_BY_TEXT``).
        Also checks the privacy checkbox if it isn't already checked.

        Args:
            name (str): Full name to enter.
            email (str): Email address to enter.
            phone (str): Phone number to enter.
            message (str): Message body to enter.
            support_type (str, optional): One of ``SUPPORT_TYPES`` to
                select. If None, a random type is chosen.

        Returns:
            ContactPage: ``self``, for method chaining.

        Raises:
            Exception: Re-raised if any field or dropdown interaction
                fails.
        """
        self.logger.info(f"Filling contact form with name: {name}")
        
        try:
            # Fill name
            name_field = self.waiter.wait_for_clickable(self.NAME_INPUT, timeout=10)
            name_field.clear()
            name_field.send_keys(name)
            self.logger.info("Filled name input")
            
            # Fill email
            email_field = self.waiter.wait_for_clickable(self.EMAIL_INPUT, timeout=10)
            email_field.clear()
            email_field.send_keys(email)
            self.logger.info("Filled email input")
            
            # Fill phone
            phone_field = self.waiter.wait_for_clickable(self.PHONE_INPUT, timeout=10)
            phone_field.clear()
            phone_field.send_keys(phone)
            self.logger.info("Filled phone input")
            
            # Select support type (random if not specified)
            if support_type is None:
                import random
                support_type = random.choice(self.SUPPORT_TYPES)
            
            self.logger.info(f"Selecting support type: {support_type}")
            
            # Click dropdown button
            dropdown = self.waiter.wait_for_clickable(
                self.SUPPORT_TYPE_DROPDOWN,
                timeout=10
            )
            dropdown.click()

            # Wait for dropdown options to become visible
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_any_elements_located(self.SUPPORT_TYPE_OPTIONS)
            )

            option_locator = (
                self.SUPPORT_TYPE_OPTION_BY_TEXT[0],
                self.SUPPORT_TYPE_OPTION_BY_TEXT[1].format(
                    support_type.lower()
                )
            )

            option = self.waiter.wait_for_clickable(
                option_locator,
                timeout=10
            )

            self.javascript.scroll_to_element(option)
            option.click()

            self.logger.info(
                f"Selected support type: {support_type}"
            )
            
            # Fill message
            message_field = self.waiter.wait_for_clickable(self.MESSAGE_TEXTAREA, timeout=10)
            message_field.clear()
            message_field.send_keys(message)
            self.logger.info("Filled message textarea")
            
            # Scroll to privacy checkbox
            self.logger.info("Scrolling to privacy checkbox")
            privacy = self.waiter.wait_for_present(self.PRIVACY_CHECKBOX, timeout=10)
            self.javascript.scroll_to_element(privacy)
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.PRIVACY_CHECKBOX)
            )
            
            # Check privacy checkbox
            if not privacy.is_selected():
                privacy.click()
                self.logger.info("Privacy checkbox checked")
            
            self.logger.info("Contact form filled successfully")
            return self
            
        except Exception as e:
            self.logger.error(f"Failed to fill contact form: {e}")
            raise
    
    def submit_form(self, max_retries=3):
        """Scroll to and click the Submit button.

        FIXME: ``max_retries`` is accepted but never used - there is no
        retry loop here, so passing anything other than the default has
        no effect. Likely a retry mechanism was planned but not finished.

        Args:
            max_retries (int): Currently unused. Defaults to 3.

        Raises:
            Exception: Re-raised (via ``wait_for_clickable``) if the
                button never becomes clickable.
        """
        self.logger.info("Submitting contact form")

        submit_btn = self.waiter.wait_for_clickable(self.SUBMIT_BUTTON, timeout=10)
        self.javascript.scroll_to_element(submit_btn)
        submit_btn.click()
        self.logger.debug("Submit button clicked")

    def is_success_displayed(self, timeout=10):
        """Check if the "Thank you for reaching out" success title is displayed.

        Args:
            timeout (int): Seconds to wait for the title. Defaults to 10.

        Returns:
            bool: True if visible in time, False on timeout or any other
                error.
        """
        self.logger.info("Checking success message")

        try:
            success = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.SUCCESS_TITLE)
            )
            self.javascript.scroll_to_element(success)
            return success.is_displayed()
        except:
            return False

    def get_success_message_text(self):
        """Get the combined success title and message text.

        Returns:
            str: ``"{title} - {message}"``, or "" if either element isn't
                found.
        """
        try:
            title = self.driver.find_element(*self.SUCCESS_TITLE).text
            message = self.driver.find_element(*self.SUCCESS_MESSAGE).text
            return f"{title} - {message}"
        except:
            return ""

    def click_read_faqs(self):
        """Scroll to and click the "Read FAQs" link.

        Returns:
            ContactPage: ``self``, for method chaining.

        Raises:
            Exception: Re-raised if the link can't be found/clicked.
        """
        self.logger.info("Clicking Read FAQs")

        try:
            faq_btn = self.waiter.wait_for_clickable(self.READ_FAQS_BTN, timeout=10)
            self.javascript.scroll_to_element(faq_btn)
            faq_btn.click()
            time.sleep(2)
            
            self.logger.info("Clicked Read FAQs")
            return self
            
        except Exception as e:
            self.logger.error(f"Failed to click Read FAQs: {e}")
            raise
    
    def verify_faq_page_loaded(self):
        """Verify the FAQ page (reached via "Read FAQs") has loaded.

        Returns:
            bool: True if the FAQ page title is visible, False on
                timeout or any other error.
        """
        self.logger.info("Verifying FAQ page loaded")

        try:
            title = self.waiter.wait_for_visible(self.FAQ_PAGE_TITLE, timeout=10)
            return title.is_displayed()
        except:
            return False

    def click_privacy_statement(self):
        """Scroll to and click the "Privacy Statement" footer link.

        Returns:
            ContactPage: ``self``, for method chaining.

        Raises:
            Exception: Re-raised if the link can't be found/clicked.
        """
        self.logger.info("Clicking Privacy Statement")

        try:
            privacy = self.waiter.wait_for_clickable(self.PRIVACY_STATEMENT, timeout=10)
            self.javascript.scroll_to_element(privacy)
            privacy.click()
            time.sleep(2)
            
            self.logger.info("Clicked Privacy Statement")
            return self
            
        except Exception as e:
            self.logger.error(f"Failed to click Privacy Statement: {e}")
            raise
        
    def get_support_types(self):
        """Open the support type dropdown and read the visible option labels.

        Closes the dropdown afterwards by clicking the page body.

        Returns:
            list[str]: The text of each option found, or an empty list on
                any failure.
        """
        self.logger.info("Getting available support types")
        
        try:
            dropdown = self.waiter.wait_for_clickable(self.SUPPORT_TYPE_DROPDOWN, timeout=10)
            dropdown.click()
            time.sleep(1)
            
            options = self.driver.find_elements(*self.SUPPORT_TYPE_OPTIONS)
            types = [opt.text for opt in options]
            
            # Close dropdown by clicking outside
            self.driver.find_element(By.TAG_NAME, 'body').click()
            time.sleep(1)
            
            self.logger.info(f"Found support types: {types}")
            return types
            
        except Exception as e:
            self.logger.error(f"Failed to get support types: {e}")
        return []