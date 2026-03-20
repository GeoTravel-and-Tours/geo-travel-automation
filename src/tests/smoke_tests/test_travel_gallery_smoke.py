import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.utils.screenshot import ScreenshotUtils
from src.core.test_base import TestBase
from src.pages.ui.travel_gallery_flow import TravelGalleryPage
from src.pages.ui.home_page import HomePage


class TestTravelGallery(TestBase):
    """Test suite for Travel Gallery functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self, driver, request):
        """Setup before each test"""
        self.driver = driver
        
        # Initialize page objects
        self.travel_gallery = TravelGalleryPage(driver)
        self.home_page = HomePage(driver)
        self.screenshot = ScreenshotUtils(driver)
        
        # Test metadata
        self.test_name = request.node.name
        self.browser = driver.capabilities['browserName']
        
        yield
    
    # ========== SMOKE TEST 1: NAVIGATION ==========
    @pytest.mark.smoke
    def test_travel_gallery_navigation(self):
        """Smoke Test 1: Verify Travel Gallery page navigation"""
        self.travel_gallery.logger.info("=== Test: Travel Gallery Navigation ===")
        
        try:
            # Step 1: Open homepage
            self.travel_gallery.logger.step(1, "Opening homepage")
            self.home_page.open()
            self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
            
            # Step 2: Navigate to Travel Gallery
            self.travel_gallery.logger.step(2, "Navigating to Travel Gallery")
            self.travel_gallery.navigate_to_travel_gallery()
            
            # Step 3: Verify page loaded
            self.travel_gallery.logger.step(3, "Verifying Travel Gallery page")
            assert self.travel_gallery.verify_gallery_page_loaded(), "Travel Gallery page should load"
            
            self.travel_gallery.logger.success("✅ Travel Gallery navigation verified")
            
        except Exception as e:
            self.travel_gallery.logger.error(f"❌ Test failed: {str(e)}")
            self.screenshot.capture_screenshot_on_failure("travel_gallery_navigation_failure")
            raise
    
    # ========== SMOKE TEST 2: TOUR CARD CLICK ==========
    @pytest.mark.smoke
    def test_tour_card_click_and_close(self):
        """Smoke Test 2: Verify tour card opens modal and can be closed"""
        self.travel_gallery.logger.info("=== Test: Tour Card Click and Close ===")
        
        try:
            # Step 1: Navigate to Travel Gallery
            self.travel_gallery.logger.step(1, "Navigating to Travel Gallery")
            self.home_page.open()
            self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
            self.travel_gallery.navigate_to_travel_gallery()
            
            # Step 2: Click on first tour card
            self.travel_gallery.logger.step(2, "Clicking on first tour card")
            self.travel_gallery.click_first_tour()
            
            # Step 3: Wait for tour detail page to load
            self.travel_gallery.logger.step(3, "Waiting for tour detail page")
            assert self.travel_gallery.wait_for_tour_detail_load(), "Tour detail page should load"
            
            # Step 4: Click view button on image
            self.travel_gallery.logger.step(4, "Clicking view button on image")
            self.travel_gallery.click_tour_image()
            
            # Step 5: Close image viewer
            self.travel_gallery.logger.step(5, "Closing image viewer")
            self.travel_gallery.close_image_viewer()
            
            # Step 6: Go back to gallery
            self.travel_gallery.logger.step(6, "Going back to gallery")
            self.driver.back()
            time.sleep(2)
            
            # Step 7: Verify back on gallery page
            self.travel_gallery.logger.step(7, "Verifying back on gallery page")
            assert "gallery" in self.driver.current_url, "Should be back on gallery page"
            
            self.travel_gallery.logger.success("✅ Tour card click, image view, and back navigation verified")
            
        except Exception as e:
            self.travel_gallery.logger.error(f"❌ Test failed: {str(e)}")
            self.screenshot.capture_screenshot_on_failure("tour_card_click_failure")
            raise
    
    # ========== SMOKE TEST 3: SCROLL FUNCTIONALITY ==========
    @pytest.mark.smoke
    def test_scroll_functionality(self):
        """Smoke Test 3: Verify scroll functionality works"""
        self.travel_gallery.logger.info("=== Test: Scroll Functionality ===")
        
        try:
            # Step 1: Navigate to Travel Gallery
            self.travel_gallery.logger.step(1, "Navigating to Travel Gallery")
            self.home_page.open()
            self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
            self.travel_gallery.navigate_to_travel_gallery()
            
            # Get initial scroll position
            initial_scroll = self.driver.execute_script("return window.pageYOffset;")
            self.travel_gallery.logger.info(f"Initial scroll position: {initial_scroll}")
            
            # Step 2: Scroll down using JavaScriptUtils
            self.travel_gallery.logger.step(2, "Scrolling down")
            self.travel_gallery.javascript.scroll_down()
            
            after_down_scroll = self.driver.execute_script("return window.pageYOffset;")
            self.travel_gallery.logger.info(f"After scroll down position: {after_down_scroll}")
            assert after_down_scroll > initial_scroll, "Page should scroll down"
            
            # Step 3: Scroll up using JavaScriptUtils
            self.travel_gallery.logger.step(3, "Scrolling up")
            self.travel_gallery.javascript.scroll_up()
            
            after_up_scroll = self.driver.execute_script("return window.pageYOffset;")
            self.travel_gallery.logger.info(f"After scroll up position: {after_up_scroll}")
            assert after_up_scroll < after_down_scroll, "Page should scroll up"
            
            self.travel_gallery.logger.success("✅ Scroll functionality verified")
            
        except Exception as e:
            self.travel_gallery.logger.error(f"❌ Test failed: {str(e)}")
            self.screenshot.capture_screenshot_on_failure("scroll_functionality_failure")
            raise
    
    # ========== COMPREHENSIVE TEST: FULL FLOW ==========
    @pytest.mark.smoke
    def test_complete_travel_gallery_flow(self):
        """Comprehensive Test: Complete Travel Gallery user flow"""
        self.travel_gallery.logger.info("=== Comprehensive Test: Complete Travel Gallery Flow ===")
        
        try:
            # Step 1: Open homepage
            self.travel_gallery.logger.step(1, "Opening homepage")
            self.home_page.open()
            self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
            
            # Step 2: Click Travel Gallery from menu
            self.travel_gallery.logger.step(2, "Clicking Travel Gallery menu")
            self.travel_gallery.navigate_to_travel_gallery()
            
            # Step 3: Verify gallery page loads with tours
            self.travel_gallery.logger.step(3, "Verifying gallery page")
            assert self.travel_gallery.verify_gallery_page_loaded(), "Gallery page should load"
            tour_count = self.travel_gallery.verify_gallery_has_tours()
            assert tour_count > 0, "Should have at least one tour"
            self.travel_gallery.logger.info(f"Found {tour_count} tours")
            
            # Step 4: Scroll down using JavaScriptUtils
            self.travel_gallery.logger.step(4, "Scrolling down")
            self.travel_gallery.javascript.scroll_down()
            time.sleep(1)
            
            # Step 5: Scroll back up using JavaScriptUtils
            self.travel_gallery.logger.step(5, "Scrolling up")
            self.travel_gallery.javascript.scroll_up()
            time.sleep(1)
            
            # Step 6: Click on first tour
            self.travel_gallery.logger.step(6, "Clicking on first tour")
            self.travel_gallery.click_first_tour()
            
            # Step 7: Wait for tour detail page to load
            self.travel_gallery.logger.step(7, "Waiting for tour detail page")
            assert self.travel_gallery.wait_for_tour_detail_load(), "Tour detail page should load"
            
            # Step 8: Click view button on image
            self.travel_gallery.logger.step(8, "Clicking view button on image")
            self.travel_gallery.click_tour_image()
            
            # Step 9: Close image viewer
            self.travel_gallery.logger.step(9, "Closing image viewer")
            self.travel_gallery.close_image_viewer()
            
            # Step 10: Go back to gallery
            self.travel_gallery.logger.step(10, "Going back to gallery")
            self.driver.back()
            time.sleep(2)
            
            # Step 11: Verify back on gallery page
            self.travel_gallery.logger.step(11, "Verifying back on gallery page")
            assert "gallery" in self.driver.current_url, "Should be back on gallery page"
            assert self.travel_gallery.verify_gallery_page_loaded(), "Should return to gallery page"
            
            self.travel_gallery.logger.success("✅ Complete travel gallery flow verified")
            
        except Exception as e:
            self.travel_gallery.logger.error(f"❌ Test failed: {str(e)}")
            self.screenshot.capture_screenshot_on_failure("complete_travel_gallery_flow_failure")
            raise
    
    # ========== MULTIPLE TOUR CLICKS TEST ==========
    @pytest.mark.smoke
    def test_multiple_tour_clicks(self):
        """Test: Click multiple tours and verify each opens correctly"""
        self.travel_gallery.logger.info("=== Test: Multiple Tour Clicks ===")
        
        try:
            # Step 1: Navigate to Travel Gallery
            self.travel_gallery.logger.step(1, "Navigating to Travel Gallery")
            self.home_page.open()
            self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
            self.travel_gallery.navigate_to_travel_gallery()
            
            # Get all tour cards
            tour_cards = self.driver.find_elements(*self.travel_gallery.TOUR_CARDS)
            tours_to_test = min(3, len(tour_cards))
            
            self.travel_gallery.logger.info(f"Testing {tours_to_test} tours")
            
            for i in range(tours_to_test):
                self.travel_gallery.logger.step(i + 2, f"Testing tour {i + 1}")
                
                # Click tour
                self.travel_gallery.click_on_any_tour(i)
                
                # Verify tour detail page loads
                assert self.travel_gallery.wait_for_tour_detail_load(), f"Tour {i + 1} detail page should load"
                
                # Click view button on image
                self.travel_gallery.click_tour_image()
                
                # Close image viewer
                self.travel_gallery.close_image_viewer()
                
                # Go back to gallery
                self.driver.back()
                time.sleep(2)
                
                # Verify back on gallery page
                assert "gallery" in self.driver.current_url, f"Should be back on gallery after tour {i + 1}"
                assert self.travel_gallery.verify_gallery_page_loaded(), f"Should return to gallery after tour {i + 1}"
            
            self.travel_gallery.logger.success("✅ Multiple tour clicks verified")
            
        except Exception as e:
            self.travel_gallery.logger.error(f"❌ Test failed: {str(e)}")
            self.screenshot.capture_screenshot_on_failure("multiple_tour_clicks_failure")
            raise
    
#     # ========== RESPONSIVE DESIGN TEST ==========
#     @pytest.mark.cross_browser
#     @pytest.mark.parametrize("width,height,device", [
#     (1920, 1080, "Desktop"),
#     (1366, 768, "Laptop"),
#     (768, 1024, "Tablet"),
#     (375, 667, "Mobile")
# ])
#     def test_travel_gallery_responsive(self, width, height, device):
#         """Test: Travel Gallery responsive design verification"""
#         self.travel_gallery.logger.info(f"=== Responsive Test: Travel Gallery on {device} ({width}x{height}) ===")
        
#         try:
#             # Set window size
#             self.driver.set_window_size(width, height)
#             time.sleep(1)
            
#             # Step 1: Navigate to homepage
#             self.travel_gallery.logger.step(1, f"Opening homepage on {device}")
#             self.home_page.open()
#             self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
            
#             # Step 2: Check if hamburger menu is visible (for tablet and mobile)
#             try:
#                 hamburger_menu = WebDriverWait(self.driver, 3).until(
#                     EC.element_to_be_clickable((By.CSS_SELECTOR, ".lucide.lucide-menu.text-navblue.cursor-pointer.text-2xl"))
#                 )
#                 self.travel_gallery.logger.step(2, f"Opening mobile/tablet menu on {device}")
#                 hamburger_menu.click()
#                 time.sleep(1)
#             except:
#                 self.travel_gallery.logger.info(f"No hamburger menu needed for {device}")
            
#             # Step 3: Navigate to Travel Gallery
#             self.travel_gallery.logger.step(3, f"Navigating to Travel Gallery on {device}")
#             self.travel_gallery.navigate_to_travel_gallery()
            
#             # Step 4: Verify page loads
#             assert self.travel_gallery.verify_gallery_page_loaded(), f"Gallery should load on {device}"
            
#             # Step 5: Verify tours are visible
#             tour_count = self.travel_gallery.verify_gallery_has_tours()
#             assert tour_count > 0, f"Tours should be visible on {device}"
            
#             # Step 6: Test click on tour
#             self.travel_gallery.logger.step(6, f"Clicking on first tour on {device}")
#             self.travel_gallery.click_first_tour()
#             assert self.travel_gallery.wait_for_tour_detail_load(), f"Tour detail page should load on {device}"
            
#             # Step 7: Click view button on image
#             self.travel_gallery.logger.step(7, f"Clicking view button on image on {device}")
#             self.travel_gallery.click_tour_image()
            
#             # Step 8: Close image viewer
#             self.travel_gallery.logger.step(8, f"Closing image viewer on {device}")
#             self.travel_gallery.close_image_viewer()
            
#             # Step 9: Go back to gallery
#             self.travel_gallery.logger.step(9, f"Going back to gallery on {device}")
#             self.driver.back()
#             time.sleep(2)
            
#             # Step 10: Verify back on gallery page
#             self.travel_gallery.logger.step(10, f"Verifying back on gallery page on {device}")
#             assert "gallery" in self.driver.current_url, f"Should be back on gallery page on {device}"
            
#             self.travel_gallery.logger.success(f"✅ Travel Gallery responsive on {device}")
            
#         except Exception as e:
#             self.travel_gallery.logger.error(f"❌ Responsive test failed for {device}: {str(e)}")
#             self.screenshot.capture_screenshot_on_failure(f"travel_gallery_responsive_{device}_failure")
#             raise