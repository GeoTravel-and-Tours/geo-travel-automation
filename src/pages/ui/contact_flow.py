# src/pages/ui/contact_flow.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from src.core.base_page import BasePage
import time


class ContactPage(BasePage):
    """Page Object for Contact Support functionality"""
    
    def __init__(self, driver):
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
    SUPPORT_TYPE_OPTIONS = (By.XPATH, "//div[@data-sentry-element='Listbox']//span")
    SUPPORT_TYPE_OPTION_BY_TEXT = (By.XPATH, "//div[@data-sentry-element='Listbox']//span[normalize-space()='{}']")

    # Available support types
    SUPPORT_TYPES = [
        "general inquiry",
        "account & login issues",
        "booking & reservations",
        "technical support",
        "payments & billing",
        "refunds & cancellations",
        "others"
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
        """Open the application homepage"""
        self.logger.info("Opening application homepage")
        self.driver.get(base_url)
        return self
    
    def navigate_to_contact(self):
        """Navigate to Contact page from homepage"""
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
        """Fill contact form with dynamic data"""
        self.logger.info(f"Filling contact form with name: {name}")
        
        try:
            # Fill name
            name_field = self.waiter.wait_for_clickable(self.NAME_INPUT, timeout=10)
            name_field.clear()
            name_field.send_keys(name)
            
            # Fill email
            email_field = self.waiter.wait_for_clickable(self.EMAIL_INPUT, timeout=10)
            email_field.clear()
            email_field.send_keys(email)
            
            # Fill phone
            phone_field = self.waiter.wait_for_clickable(self.PHONE_INPUT, timeout=10)
            phone_field.clear()
            phone_field.send_keys(phone)
            
            # Select support type (random if not specified)
            if support_type is None:
                import random
                support_type = random.choice(self.SUPPORT_TYPES)
            
            self.logger.info(f"Selecting support type: {support_type}")
            
            # Click dropdown button
            dropdown = self.waiter.wait_for_clickable(self.SUPPORT_TYPE_DROPDOWN, timeout=10)
            dropdown.click()
            time.sleep(1)
            
            # Select option by text
            option_locator = (self.SUPPORT_TYPE_OPTION_BY_TEXT[0], 
                            self.SUPPORT_TYPE_OPTION_BY_TEXT[1].format(support_type))
            option = self.waiter.wait_for_clickable(option_locator, timeout=10)
            option.click()
            time.sleep(1)
            
            self.logger.info(f"Selected support type: {support_type}")
            
            # Fill message
            message_field = self.waiter.wait_for_clickable(self.MESSAGE_TEXTAREA, timeout=10)
            message_field.clear()
            message_field.send_keys(message)
            
            # Scroll to privacy checkbox
            self.logger.info("Scrolling to privacy checkbox")
            privacy = self.waiter.wait_for_present(self.PRIVACY_CHECKBOX, timeout=10)
            self.javascript.scroll_to_element(privacy)
            time.sleep(1)
            
            # Check privacy checkbox
            if not privacy.is_selected():
                privacy.click()
                self.logger.info("Privacy checkbox checked")
            
            self.logger.info("Contact form filled successfully")
            return self
            
        except Exception as e:
            self.logger.error(f"Failed to fill contact form: {e}")
            raise
    
    def submit_form(self):
        """Submit contact form"""
        self.logger.info("Submitting contact form")
        
        try:
            submit_btn = self.waiter.wait_for_clickable(self.SUBMIT_BUTTON, timeout=10)
            self.javascript.scroll_to_element(submit_btn)
            submit_btn.click()
            time.sleep(2)
            
            self.logger.info("Contact form submitted")
            return self
            
        except Exception as e:
            self.logger.error(f"Failed to submit form: {e}")
            raise
    
    def is_success_displayed(self, timeout=10):
        """Check if success message is displayed"""
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
        """Get success message text"""
        try:
            title = self.driver.find_element(*self.SUCCESS_TITLE).text
            message = self.driver.find_element(*self.SUCCESS_MESSAGE).text
            return f"{title} - {message}"
        except:
            return ""
    
    def click_read_faqs(self):
        """Click Read FAQs button"""
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
        """Verify FAQ page loaded"""
        self.logger.info("Verifying FAQ page loaded")
        
        try:
            title = self.waiter.wait_for_visible(self.FAQ_PAGE_TITLE, timeout=10)
            return title.is_displayed()
        except:
            return False
    
    def click_privacy_statement(self):
        """Click Privacy Statement link"""
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
        """Get all available support types from dropdown"""
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