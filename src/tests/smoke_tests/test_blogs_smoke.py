import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.utils.screenshot import ScreenshotUtils
from src.core.test_base import TestBase
from src.pages.ui.blogs_flow import BlogsPage
from src.pages.ui.home_page import HomePage
from src.tests.test_data import get_blog_test_data


class TestBlogs(TestBase):
    """Test suite for Blogs functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self, driver, request):
        """Setup before each test"""
        self.driver = driver
        
        # Initialize page objects
        self.blogs_page = BlogsPage(driver)
        self.home_page = HomePage(driver)
        self.screenshot = ScreenshotUtils(driver)
        
        # Test metadata
        self.test_name = request.node.name
        self.browser = driver.capabilities['browserName']
        
        # Test data
        self.blog_test_data = get_blog_test_data()
        self.comment_data = self.blog_test_data["comment"]
        
        yield
    
    # ========== SMOKE TEST 1: NAVIGATION ==========
    @pytest.mark.smoke
    def test_blogs_page_navigation(self):
        """Smoke Test 1: Verify Blogs page navigation"""
        self.blogs_page.logger.info("=== Test: Blogs Page Navigation ===")
        
        try:
            # Step 1: Open homepage
            self.blogs_page.logger.step(1, "Opening homepage")
            self.home_page.open()
            self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
            
            # Step 2: Navigate to Blogs
            self.blogs_page.logger.step(2, "Navigating to Blogs")
            self.blogs_page.navigate_to_blogs()
            
            # Step 3: Verify page loaded
            self.blogs_page.logger.step(3, "Verifying Blogs page")
            assert self.blogs_page.verify_blogs_page_loaded(), "Blogs page should load"
            
            self.blogs_page.logger.success("✅ Blogs page navigation verified")
            
        except Exception as e:
            self.blogs_page.logger.error(f"❌ Test failed: {str(e)}")
            self.screenshot.capture_screenshot_on_failure("blogs_navigation_failure")
            raise
    
    # ========== SMOKE TEST 2: READ BLOG ==========
    @pytest.mark.smoke
    def test_read_blog(self):
        """Smoke Test 2: Verify clicking blog opens detail page"""
        self.blogs_page.logger.info("=== Test: Read Blog ===")
        
        try:
            # Step 1: Navigate to Blogs
            self.blogs_page.logger.step(1, "Navigating to Blogs")
            self.home_page.open()
            self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
            self.blogs_page.navigate_to_blogs()
            
            # Step 2: Click first blog
            self.blogs_page.logger.step(2, "Clicking on first blog")
            self.blogs_page.click_first_blog()
            
            # Step 3: Wait for blog detail
            self.blogs_page.logger.step(3, "Waiting for blog detail")
            assert self.blogs_page.wait_for_blog_detail_load(), "Blog detail should load"
            
            # Step 4: Verify URL contains blog ID
            self.blogs_page.logger.step(4, "Verifying URL")
            assert "blogs" in self.driver.current_url, "URL should contain 'blogs'"
            
            self.blogs_page.logger.success("✅ Read blog verified")
            
        except Exception as e:
            self.blogs_page.logger.error(f"❌ Test failed: {str(e)}")
            self.screenshot.capture_screenshot_on_failure("read_blog_failure")
            raise
    
    # ========== SMOKE TEST 3: COMMENT FLOW ==========
    @pytest.mark.smoke
    def test_comment_flow(self):
        """Smoke Test 3: Verify comment submission flow"""
        self.blogs_page.logger.info("=== Test: Comment Flow ===")
        
        try:
            # Step 1: Navigate to blog detail
            self.blogs_page.logger.step(1, "Navigating to blog detail")
            self.home_page.open()
            self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
            self.blogs_page.navigate_to_blogs()
            self.blogs_page.click_first_blog()
            assert self.blogs_page.wait_for_blog_detail_load(), "Blog detail should load"
            
            # Step 2: Fill comment form
            self.blogs_page.logger.step(2, "Filling comment form")
            self.blogs_page.fill_comment(
                name=self.comment_data["name"],
                email=self.comment_data["email"],
                message=self.comment_data["message"]
            )
            
            # Step 3: Submit comment
            self.blogs_page.logger.step(3, "Submitting comment")
            self.blogs_page.submit_comment()
            
            # Step 4: Verify success message
            self.blogs_page.logger.step(4, "Verifying success message")
            assert self.blogs_page.is_success_message_displayed(), "Success message should appear"
            
            self.blogs_page.logger.success("✅ Comment flow verified")
            
        except Exception as e:
            self.blogs_page.logger.error(f"❌ Test failed: {str(e)}")
            self.screenshot.capture_screenshot_on_failure("comment_flow_failure")
            raise
    
    # ========== SMOKE TEST 4: SCROLL FUNCTIONALITY ==========
    @pytest.mark.smoke
    def test_scroll_functionality(self):
        """Smoke Test 4: Verify scroll functionality on blog detail"""
        self.blogs_page.logger.info("=== Test: Scroll Functionality ===")
        
        try:
            # Step 1: Navigate to blog detail
            self.blogs_page.logger.step(1, "Navigating to blog detail")
            self.home_page.open()
            self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
            self.blogs_page.navigate_to_blogs()
            self.blogs_page.click_first_blog()
            assert self.blogs_page.wait_for_blog_detail_load(), "Blog detail should load"
            
            # Get initial scroll position
            initial_scroll = self.driver.execute_script("return window.pageYOffset;")
            self.blogs_page.logger.info(f"Initial scroll position: {initial_scroll}")
            
            # Step 2: Scroll down
            self.blogs_page.logger.step(2, "Scrolling down")
            self.blogs_page.javascript.scroll_down()
            
            after_down_scroll = self.driver.execute_script("return window.pageYOffset;")
            self.blogs_page.logger.info(f"After scroll down position: {after_down_scroll}")
            assert after_down_scroll > initial_scroll, "Page should scroll down"
            
            # Step 3: Scroll up
            self.blogs_page.logger.step(3, "Scrolling up")
            self.blogs_page.javascript.scroll_up()
            
            after_up_scroll = self.driver.execute_script("return window.pageYOffset;")
            self.blogs_page.logger.info(f"After scroll up position: {after_up_scroll}")
            assert after_up_scroll < after_down_scroll, "Page should scroll up"
            
            self.blogs_page.logger.success("✅ Scroll functionality verified")
            
        except Exception as e:
            self.blogs_page.logger.error(f"❌ Test failed: {str(e)}")
            self.screenshot.capture_screenshot_on_failure("blogs_scroll_failure")
            raise
    
    # ========== SMOKE TEST 5: MORE LIKE THIS ==========
    @pytest.mark.smoke
    def test_more_like_this(self):
        """Smoke Test 5: Verify More like this section"""
        self.blogs_page.logger.info("=== Test: More Like This ===")
        
        try:
            # Step 1: Navigate to blog detail
            self.blogs_page.logger.step(1, "Navigating to blog detail")
            self.home_page.open()
            self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
            self.blogs_page.navigate_to_blogs()
            self.blogs_page.click_first_blog()
            assert self.blogs_page.wait_for_blog_detail_load(), "Blog detail should load"
            
            # Step 2: Scroll to More like this
            self.blogs_page.logger.step(2, "Scrolling to More like this")
            self.blogs_page.scroll_to_more_like_this()
            
            # Step 3: Verify related blogs exist
            self.blogs_page.logger.step(3, "Verifying related blogs")
            assert self.blogs_page.verify_related_blogs_exist(), "Related blogs should exist"
            
            self.blogs_page.logger.success("✅ More like this verified")
            
        except Exception as e:
            self.blogs_page.logger.error(f"❌ Test failed: {str(e)}")
            self.screenshot.capture_screenshot_on_failure("more_like_this_failure")
            raise
    
    # ========== COMPREHENSIVE TEST: FULL FLOW ==========
    @pytest.mark.smoke
    def test_complete_blog_flow(self):
        """Comprehensive Test: Complete blog reading and commenting flow"""
        self.blogs_page.logger.info("=== Comprehensive Test: Complete Blog Flow ===")
        
        try:
            # Step 1: Navigate to Blogs
            self.blogs_page.logger.step(1, "Navigating to Blogs")
            self.home_page.open()
            self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
            self.blogs_page.navigate_to_blogs()
            
            # Step 2: Click first blog
            self.blogs_page.logger.step(3, "Clicking first blog")
            self.blogs_page.click_first_blog()
            assert self.blogs_page.wait_for_blog_detail_load(), "Blog detail should load"
            
            # Step 3: Scroll to comments
            self.blogs_page.logger.step(4, "Scrolling to comments")
            self.blogs_page.scroll_to_comments()
            
            # Step 4: Fill and submit comment
            self.blogs_page.logger.step(5, "Filling and submitting comment")
            self.blogs_page.fill_comment(
                name=self.comment_data["name"],
                email=self.comment_data["email"],
                message=self.comment_data["message"]
            )
            self.blogs_page.submit_comment()
            
            # Step 5: Verify success
            self.blogs_page.logger.step(6, "Verifying comment submission")
            assert self.blogs_page.is_success_message_displayed(), "Success message should appear"
            
            # Step 6: Scroll to More like this
            self.blogs_page.logger.step(7, "Scrolling to More like this")
            self.blogs_page.scroll_to_more_like_this()
            
            # Step 7: Verify related blogs
            self.blogs_page.logger.step(8, "Verifying related blogs")
            assert self.blogs_page.verify_related_blogs_exist(), "Related blogs should exist"
            
            self.blogs_page.logger.success("✅ Complete blog flow verified")
            
        except Exception as e:
            self.blogs_page.logger.error(f"❌ Test failed: {str(e)}")
            self.screenshot.capture_screenshot_on_failure("complete_blog_flow_failure")
            raise
    
    # # ========== RESPONSIVE TEST ==========
    # @pytest.mark.cross_browser
    # @pytest.mark.parametrize("width,height,device", [
    #     (1920, 1080, "Desktop"),
    #     (1366, 768, "Laptop"),
    #     (768, 1024, "Tablet"),
    #     (375, 667, "Mobile")
    # ])
    # def test_blogs_responsive(self, width, height, device):
    #     """Test: Blogs responsive design verification"""
    #     self.blogs_page.logger.info(f"=== Responsive Test: Blogs on {device} ({width}x{height}) ===")
        
    #     try:
    #         # Set window size
    #         self.driver.set_window_size(width, height)
    #         time.sleep(1)
            
    #         # Step 1: Navigate to Blogs
    #         self.blogs_page.logger.step(1, f"Navigating to Blogs on {device}")
    #         self.home_page.open()
    #         self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
            
    #         # Check if hamburger menu needed
    #         try:
    #             hamburger = WebDriverWait(self.driver, 3).until(
    #                 EC.element_to_be_clickable((By.CSS_SELECTOR, ".lucide.lucide-menu.text-navblue.cursor-pointer.text-2xl"))
    #             )
    #             hamburger.click()
    #             time.sleep(1)
    #         except:
    #             pass
            
    #         self.blogs_page.navigate_to_blogs()
            
    #         # Step 2: Verify page loads
    #         assert self.blogs_page.verify_blogs_page_loaded(), f"Blogs should load on {device}"
            
    #         # Step 3: Verify blogs are visible
    #         blog_count = self.blogs_page.verify_blog_has_tours()
    #         assert blog_count > 0, f"Blogs should be visible on {device}"
            
    #         # Step 4: Click and read blog
    #         self.blogs_page.click_first_blog()
    #         assert self.blogs_page.wait_for_blog_detail_load(), f"Blog detail should load on {device}"
            
    #         # Step 5: Go back
    #         self.driver.back()
    #         time.sleep(2)
            
    #         self.blogs_page.logger.success(f"✅ Blogs responsive on {device}")
            
    #     except Exception as e:
    #         self.blogs_page.logger.error(f"❌ Responsive test failed for {device}: {str(e)}")
    #         self.screenshot.capture_screenshot_on_failure(f"blogs_responsive_{device}_failure")
    #         raise