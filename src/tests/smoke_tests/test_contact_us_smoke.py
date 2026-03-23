# src/tests/smoke_tests/test_contact_us_smoke.py

import pytest
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.utils.screenshot import ScreenshotUtils
from src.core.test_base import TestBase
from src.pages.ui.contact_flow import ContactPage
from src.pages.ui.home_page import HomePage
from src.tests.test_data import get_contact_test_data


class TestContact(TestBase):
    """Test suite for Contact Support functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self, driver, request):
        """Setup before each test"""
        self.driver = driver
        
        # Initialize page objects
        self.contact_page = ContactPage(driver)
        self.home_page = HomePage(driver)
        self.screenshot = ScreenshotUtils(driver)
        
        # Test metadata
        self.test_name = request.node.name
        self.browser = driver.capabilities['browserName']
        
        # Test data
        self.contact_data = get_contact_test_data()
        
        yield
    
    # ========== SMOKE TEST 1: NAVIGATION ==========
    @pytest.mark.smoke
    def test_contact_page_navigation(self):
        """Smoke Test 1: Verify Contact page navigation"""
        self.contact_page.logger.info("=== Test: Contact Page Navigation ===")
        
        try:
            # Step 1: Open homepage
            self.contact_page.logger.step(1, "Opening homepage")
            self.home_page.open()
            self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
            
            # Step 2: Navigate to Contact
            self.contact_page.logger.step(2, "Navigating to Contact")
            self.contact_page.navigate_to_contact()
            
            # Step 3: Verify page loaded
            self.contact_page.logger.step(3, "Verifying Contact page")
            assert "contact" in self.driver.current_url, "URL should contain contact"
            
            self.contact_page.logger.success("✅ Contact page navigation verified")
            
        except Exception as e:
            self.contact_page.logger.error(f"❌ Test failed: {str(e)}")
            self.screenshot.capture_screenshot_on_failure("contact_navigation_failure")
            raise
    
    # ========== SMOKE TEST 2: SUBMIT CONTACT FORM ==========
    @pytest.mark.smoke
    def test_submit_contact_form(self):
        """Smoke Test 2: Verify contact form submission"""
        self.contact_page.logger.info("=== Test: Submit Contact Form ===")
        
        try:
            # Step 1: Navigate to Contact
            self.contact_page.logger.step(1, "Navigating to Contact")
            self.home_page.open()
            self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
            self.contact_page.navigate_to_contact()
            
            # Step 2: Fill form
            self.contact_page.logger.step(2, "Filling contact form")
            self.contact_page.fill_contact_form(
                name=self.contact_data["name"],
                email=self.contact_data["email"],
                phone=self.contact_data["phone"],
                message=self.contact_data["message"],
                support_type="technical support"
            )
            
            # Step 3: Submit form
            self.contact_page.logger.step(3, "Submitting form")
            self.contact_page.submit_form()
            
            # Step 4: Verify success
            self.contact_page.logger.step(4, "Verifying success message")
            assert self.contact_page.is_success_displayed(), "Success message should appear"
            
            self.contact_page.logger.success("✅ Contact form submission verified")
            
        except Exception as e:
            self.contact_page.logger.error(f"❌ Test failed: {str(e)}")
            self.screenshot.capture_screenshot_on_failure("contact_submit_failure")
            raise
    
    # ========== SMOKE TEST 3: READ FAQS ==========
    @pytest.mark.smoke
    def test_read_faqs(self):
        """Smoke Test 3: Verify Read FAQs navigation"""
        self.contact_page.logger.info("=== Test: Read FAQs ===")
        
        try:
            # Step 1: Navigate to Contact
            self.contact_page.logger.step(1, "Navigating to Contact")
            self.home_page.open()
            self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
            self.contact_page.navigate_to_contact()
            
            # Step 2: Click Read FAQs
            self.contact_page.logger.step(2, "Clicking Read FAQs")
            self.contact_page.click_read_faqs()
            
            # Step 3: Verify FAQ page
            self.contact_page.logger.step(3, "Verifying FAQ page")
            assert self.contact_page.verify_faq_page_loaded(), "FAQ page should load"
            assert "faq" in self.driver.current_url.lower(), "URL should contain faq"
            
            self.contact_page.logger.success("✅ Read FAQs verified")
            
        except Exception as e:
            self.contact_page.logger.error(f"❌ Test failed: {str(e)}")
            self.screenshot.capture_screenshot_on_failure("contact_faqs_failure")
            raise
    
    # ========== SMOKE TEST 4: PRIVACY STATEMENT ==========
    @pytest.mark.smoke
    def test_privacy_statement_link(self):
        """Smoke Test 4: Verify Privacy Statement link"""
        self.contact_page.logger.info("=== Test: Privacy Statement ===")
        
        try:
            # Step 1: Navigate to Contact
            self.contact_page.logger.step(1, "Navigating to Contact")
            self.home_page.open()
            self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
            self.contact_page.navigate_to_contact()
            
            # Get current window handle
            original_window = self.driver.current_window_handle
            
            # Step 2: Click Privacy Statement
            self.contact_page.logger.step(2, "Clicking Privacy Statement")
            self.contact_page.click_privacy_statement()
            
            # Step 3: Switch to new tab
            self.contact_page.logger.step(3, "Switching to new tab")
            WebDriverWait(self.driver, 10).until(
                EC.number_of_windows_to_be(2)
            )
            
            for window_handle in self.driver.window_handles:
                if window_handle != original_window:
                    self.driver.switch_to.window(window_handle)
                    break
            
            # Step 4: Verify privacy page URL
            self.contact_page.logger.step(4, "Verifying privacy page")
            assert "privacy" in self.driver.current_url.lower(), "URL should contain privacy"
            
            # Step 5: Close new tab and switch back
            self.driver.close()
            self.driver.switch_to.window(original_window)
            
            self.contact_page.logger.success("✅ Privacy Statement verified")
            
        except Exception as e:
            self.contact_page.logger.error(f"❌ Test failed: {str(e)}")
            self.screenshot.capture_screenshot_on_failure("contact_privacy_failure")
            raise
    
    # ========== COMPREHENSIVE TEST: FULL FLOW ==========
    @pytest.mark.smoke
    def test_complete_contact_flow(self):
        """Comprehensive Test: Complete contact support flow"""
        self.contact_page.logger.info("=== Comprehensive Test: Complete Contact Flow ===")
        
        try:
            # Step 1: Navigate to Contact
            self.contact_page.logger.step(1, "Navigating to Contact")
            self.home_page.open()
            self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
            self.contact_page.navigate_to_contact()
            
            # Step 2: Fill and submit form
            self.contact_page.logger.step(2, "Filling and submitting form")
            self.contact_page.fill_contact_form(
                name=self.contact_data["name"],
                email=self.contact_data["email"],
                phone=self.contact_data["phone"],
                message=self.contact_data["message"]
            )
            self.contact_page.submit_form()
            
            # Step 3: Verify success
            self.contact_page.logger.step(3, "Verifying success")
            assert self.contact_page.is_success_displayed(), "Success message should appear"
            
            # Step 4: Navigate back and test FAQs
            self.contact_page.logger.step(4, "Testing FAQs section")
            self.driver.back()
            self.contact_page.navigate_to_contact()
            time.sleep(2)
            
            self.contact_page.click_read_faqs()
            assert self.contact_page.verify_faq_page_loaded(), "FAQ page should load"
            
            self.contact_page.logger.success("✅ Complete contact flow verified")
            
        except Exception as e:
            self.contact_page.logger.error(f"❌ Test failed: {str(e)}")
            self.screenshot.capture_screenshot_on_failure("complete_contact_flow_failure")
            raise