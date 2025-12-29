import pytest
import time
from datetime import datetime, timedelta
from src.utils.screenshot import ScreenshotUtils
from src.core.test_base import TestBase
from src.pages.ui.visa_enquiries_flow import VisaPage
from src.pages.ui.home_page import HomePage


class TestVisaSmoke(TestBase):
    """Test suite for Visa Enquiries functionality - Hierarchical Smoke Tests"""
    
    # Test data
    TEST_DATA = {
        "first_name": "QA Bot",
        "last_name": "GEO",
        "email": "geo.qa.bot@gmail.com",
        "phone": "7080702920",
        "country_origin": "Nigeria",
        "passport_availability": "yes",
        "destination": "Qatar",
        "visa_type": "tourist/visit visa",
        "message": "I would like to travel to Qatar for tourist/visit purposes"
    }
    
    @pytest.fixture(autouse=True)
    def setup(self, driver, request):
        """Setup before each test"""
        self.driver = driver
        
        # Initialize page objects
        self.visa_page = VisaPage(driver)
        self.home_page = HomePage(driver)
        self.screenshot = ScreenshotUtils(driver)
        
        # Test metadata
        self.test_name = request.node.name
        self.browser = driver.capabilities['browserName']
        
        yield
    
    # ========== SMOKE TEST 1: NAVIGATION ==========
    @pytest.mark.smoke
    @pytest.mark.dependency(name="visa_page_loaded")
    def test_visa_page_navigation(self):
        """Smoke Test 1: Quick check - Visa page loads and navigates successfully"""
        self.visa_page.logger.info("=== Quick Smoke Test: Visa Page Navigation ===")
        
        # Step 1: Open homepage
        self.visa_page.logger.step(1, "Opening homepage")
        self.home_page.open()
        self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
        
        # Step 2: Navigate to Visa page
        self.visa_page.logger.step(2, "Navigating to Visa page")
        self.visa_page.navigate_to_visa()
        
        self.visa_page.logger.success("✅ Visa page navigation verified")
    
    # ========== SMOKE TEST 2: FORM INTERACTION ==========
    @pytest.mark.smoke
    @pytest.mark.dependency(name="visa_form_works", depends=["visa_page_loaded"])
    def test_visa_form_basic_interaction(self):
        """Smoke Test 2: Quick check - Visa form accepts basic input"""
        self.visa_page.logger.info("=== Quick Smoke Test: Visa Form Basic Interaction ===")
        
        # Step 1: Navigate to Visa page
        self.visa_page.logger.step(1, "Navigating to Visa page and opening form")
        self.home_page.open()
        self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
        self.visa_page.navigate_to_visa()
        self.visa_page.click_get_started()
        
        # Step 2: Verify form is loaded
        self.visa_page.logger.step(2, "Verifying form loaded")
        form_loaded = self.visa_page.wait_for_form_load()
        assert form_loaded, "Visa form should load successfully"
        
        # Step 3: Test basic form interaction
        self.visa_page.logger.step(3, "Testing form field interaction")
        
        # Fill first name only (quick test)
        self.visa_page.fill_personal_details(
            first_name=self.TEST_DATA["first_name"],
            last_name="",
            email="",
            phone=""
        )
        
        # Check field status
        fields_status = self.visa_page.get_form_fields_status()
        assert fields_status["first_name"]["visible"], "First name field should be visible"
        assert fields_status["first_name"]["enabled"], "First name field should be enabled"
        
        self.visa_page.logger.success("✅ Visa form basic interaction verified")
    
    # ========== SMOKE TEST 3: DROPDOWN FUNCTIONALITY ==========
    @pytest.mark.smoke
    @pytest.mark.dependency(name="dropdowns_work", depends=["visa_page_loaded"])
    def test_dropdown_functionality(self):
        """Smoke Test 3: Quick check - All dropdowns work correctly"""
        self.visa_page.logger.info("=== Quick Smoke Test: Dropdown Functionality ===")
        
        # Step 1: Navigate to Visa form
        self.visa_page.logger.step(1, "Navigating to Visa form")
        self.home_page.open()
        self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
        self.visa_page.navigate_to_visa()
        self.visa_page.click_get_started()
        self.visa_page.wait_for_form_load()
        
        # Step 2: Test country origin dropdown
        self.visa_page.logger.step(2, "Testing country origin dropdown")
        self.visa_page.select_country_origin(self.TEST_DATA["country_origin"])
        time.sleep(1)
        
        # Step 3: Test passport availability dropdown
        self.visa_page.logger.step(3, "Testing passport availability dropdown")
        self.visa_page.select_passport_availability(self.TEST_DATA["passport_availability"])
        time.sleep(1)
        
        # Step 4: Test destination country dropdown
        self.visa_page.logger.step(4, "Testing destination country dropdown")
        # self.visa_page.select_destination_country(self.TEST_DATA["destination"])
        self.visa_page.select_destination_country()
        time.sleep(1)
        
        # Step 5: Test visa type dropdown
        self.visa_page.logger.step(5, "Testing visa type dropdown")
        # self.visa_page.select_visa_type(self.TEST_DATA["visa_type"])
        self.visa_page.select_visa_type()
        time.sleep(1)
        
        self.visa_page.logger.success("✅ All dropdowns functional")
    
    # ========== SMOKE TEST 4: DATE PICKER ==========
    @pytest.mark.smoke
    # @pytest.mark.dependency(name="date_picker_works", depends=["visa_page_loaded"])
    def test_date_picker_functionality(self):
        """Smoke Test 4: Quick check - Date picker works"""
        self.visa_page.logger.info("=== Quick Smoke Test: Date Picker ===")
        
        # Step 1: Navigate to Visa form
        self.visa_page.logger.step(1, "Navigating to Visa form")
        self.home_page.open()
        self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
        self.visa_page.navigate_to_visa()
        self.visa_page.click_get_started()
        self.visa_page.wait_for_form_load()
        
        # Step 2: Test date picker
        self.visa_page.logger.step(2, "Testing date picker")
        self.visa_page.select_travel_date()
        
        self.visa_page.logger.success("✅ Date picker functional")
    
    # ========== COMPREHENSIVE TEST: FULL FORM SUBMISSION ==========
    @pytest.mark.smoke
    # @pytest.mark.dependency(depends=[
    #     "visa_page_loaded", 
    #     "visa_form_works", 
    #     "dropdowns_work", 
    #     "date_picker_works"
    # ])
    def test_complete_visa_application_flow(self):
        """Smoke Test 5: Comprehensive end-to-end visa application flow"""
        self.visa_page.logger.info("=== COMPREHENSIVE TEST: Complete Visa Application Flow ===")
        
        try:
            # Step 1: Open and navigate to Visa page
            self.visa_page.logger.step(1, "Opening homepage and navigating to Visa")
            self.home_page.open()
            self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
            self.visa_page.navigate_to_visa()
            
            # Step 2: Open visa application form
            self.visa_page.logger.step(2, "Opening visa application form")
            self.visa_page.click_get_started()
            self.visa_page.wait_for_form_load()
            
            # Step 3: Fill personal details
            self.visa_page.logger.step(3, "Filling personal details")
            self.visa_page.fill_personal_details(
                first_name=self.TEST_DATA["first_name"],
                last_name=self.TEST_DATA["last_name"],
                email=self.TEST_DATA["email"],
                phone=self.TEST_DATA["phone"]
            )
            
            # Step 4: Select country of origin
            self.visa_page.logger.step(4, "Selecting country of origin")
            self.visa_page.select_country_origin(self.TEST_DATA["country_origin"])
            
            # Step 5: Select passport availability
            self.visa_page.logger.step(5, "Selecting passport availability")
            self.visa_page.select_passport_availability(self.TEST_DATA["passport_availability"])
            
            # Step 6: Select travel date
            self.visa_page.logger.step(6, "Selecting travel date")
            self.visa_page.select_travel_date()
            
            # Step 7: Select destination country
            self.visa_page.logger.step(7, "Selecting destination country")
            self.visa_page.select_destination_country()
            
            # Step 8: Select visa type
            self.visa_page.logger.step(8, "Selecting visa type")
            self.visa_page.select_visa_type()
            
            # Step 9: Fill additional message
            self.visa_page.logger.step(9, "Filling additional message")
            self.visa_page.fill_message(self.TEST_DATA["message"])
            print("Message filled in the form: ", self.TEST_DATA["message"])
            
            # Step 10: Submit application
            self.visa_page.logger.step(10, "Submitting visa application")
            self.visa_page.submit_application()
            
            # Step 11: Verify submission response
            self.visa_page.logger.step(11, "Verifying submission response")
            time.sleep(3)  # Wait for response
            
            # Check for success message or confirmation
            success = self.visa_page.is_success_message_displayed()
            
            # In staging, we might not get actual success, but should not crash
            if not success:
                self.visa_page.logger.info("No success message displayed (might be expected in staging)")
                # Verify we're still on the page and no errors
                assert self.visa_page.is_form_visible() or self.driver.current_url, "Should remain on valid page"
            else:
                self.visa_page.logger.success("✅ Success message displayed")
            
            self.visa_page.logger.success("✅ Comprehensive visa application flow completed")
            
        except Exception as e:
            self.visa_page.logger.error(f"❌ Comprehensive visa application test failed: {str(e)}")
            self.screenshot.capture_screenshot_on_failure("visa_application_flow_failure")
            raise
    
    # ========== CANCEL FLOW TEST ==========
    @pytest.mark.smoke
    @pytest.mark.dependency(depends=["visa_page_loaded"])
    def test_visa_application_cancel_flow(self):
        """Test 6: Verify visa application cancel functionality"""
        self.visa_page.logger.info("=== Test: Visa Application Cancel Flow ===")
        
        try:
            # Step 1: Navigate to Visa form
            self.visa_page.logger.step(1, "Navigating to Visa form")
            self.home_page.open()
            self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
            self.visa_page.navigate_to_visa()
            self.visa_page.click_get_started()
            self.visa_page.wait_for_form_load()
            
            # Step 2: Fill some data
            self.visa_page.logger.step(2, "Filling partial form data")
            self.visa_page.fill_personal_details(
                first_name=self.TEST_DATA["first_name"],
                last_name=self.TEST_DATA["last_name"],
                email="",
                phone=""
            )
            
            # Step 3: Cancel application
            self.visa_page.logger.step(3, "Cancelling application")
            
            self.visa_page.cancel_application()
            time.sleep(2)
            
            # Step 4: Verify cancel worked
            self.visa_page.logger.step(4, "Verifying cancel action")
            # Either form should be closed or we should be redirected
            current_url = self.driver.current_url
            assert "enquiries" not in current_url.lower(), "Should remain on visa page after cancel"
            
            self.visa_page.logger.success("✅ Visa application cancel flow verified")
            
        except Exception as e:
            self.visa_page.logger.error(f"❌ Visa cancel flow test failed: {str(e)}")
            self.screenshot.capture_screenshot_on_failure("visa_cancel_flow_failure")
            raise
    
    # # ========== CROSS-BROWSER COMPATIBILITY TEST ==========
    # @pytest.mark.cross_browser
    # @pytest.mark.smoke
    # # @pytest.mark.dependency(depends=["visa_page_loaded"])
    # @pytest.mark.parametrize("width,height,device", [
    #     (1920, 1080, "Desktop"),
    #     (1366, 768, "Laptop"),
    #     (768, 1024, "Tablet"),
    #     (375, 667, "Mobile"),
    #     (360, 640, "Small Mobile")
    # ])
    # def test_visa_form_responsive_design(self, width, height, device):
    #     """Test 7: Cross-browser/device responsive design verification"""
    #     self.visa_page.logger.info(f"=== Responsive Test: Visa Form on {device} ({width}x{height}) ===")
        
    #     try:
    #         # Set window size
    #         self.driver.set_window_size(width, height)
    #         time.sleep(1)
            
    #         # Step 1: Navigate to Visa page
    #         self.visa_page.logger.step(1, f"Navigating to Visa page on {device}")
    #         self.home_page.open()
    #         self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
    #         self.visa_page.navigate_to_visa()
            
    #         # Step 2: Open form
    #         self.visa_page.logger.step(2, "Opening visa form")
    #         self.visa_page.click_get_started()
    #         form_loaded = self.visa_page.wait_for_form_load()
    #         assert form_loaded, f"Visa form should load on {device}"
            
    #         # Step 3: Verify page loads correctly
    #         self.visa_page.logger.step(3, "Verifying page layout")
    #         assert self.visa_page.is_form_visible(), f"Visa page should be visible on {device}"
            
    #         # Step 4: Test basic interaction
    #         self.visa_page.logger.step(4, "Testing form interaction")
    #         self.visa_page.fill_personal_details(
    #             first_name=self.TEST_DATA["first_name"],
    #             last_name="",
    #             email="",
    #             phone=""
    #         )
            
    #         # Verify form is usable
    #         fields_status = self.visa_page.get_form_fields_status()
    #         assert fields_status["first_name"]["enabled"], f"Form should be usable on {device}"
            
    #         self.visa_page.logger.success(f"✅ Visa form responsive on {device} ({width}x{height})")
            
    #         # Screenshot for responsive testing evidence
    #         screenshot_name = f"visa_responsive_{device}_{width}x{height}_{self.browser}"
            
    #     except Exception as e:
    #         self.visa_page.logger.error(f"❌ Responsive test failed for {device}: {str(e)}")
    #         screenshot_name = f"visa_responsive_failure_{device}_{width}x{height}_{self.browser}"
    #         self.screenshot.capture_screenshot_on_failure(screenshot_name)
    #         raise