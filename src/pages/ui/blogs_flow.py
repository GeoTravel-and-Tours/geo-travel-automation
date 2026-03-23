# src/pages/ui/blogs_flow.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from src.core.base_page import BasePage
import time


class BlogsPage(BasePage):
    """Page Object for Blogs functionality"""
    
    def __init__(self, driver):
        super().__init__(driver)
    
    # ========== LOCATORS ==========
    # Navigation
    BLOGS_MENU = (By.XPATH, "//a[@class='py-2 hover:bg-slate-100 transition-all truncate text-base'][normalize-space()='Blogs']")
    BLOGS_HEADER = (By.XPATH, "//h3[normalize-space()='Blogs']")
    BLOGS_CONTAINER = (By.XPATH, "//div[@class='bg-white p-3 rounded-lg border border-gray-100/70 shadow-sm']")
    
    # Blog Cards
    BLOG_TITLES = (By.XPATH, "//h2[contains(@class, 'text-lg')]")
    FIRST_BLOG_CARD = (By.XPATH, "(//main[@data-sentry-component='BlogPage']//a[contains(@href, '/blogs/')])[1]")
    READ_ARTICLE_BTN = (By.XPATH, "//a[normalize-space()='Read article']")
    
    # Blog Detail Page
    BLOG_DETAIL_CONTAINER = (By.XPATH, "//main[@data-sentry-component='BlogPage']")
    BLOG_TITLE = (By.CSS_SELECTOR, ".text-lg.font-medium.text-gray-700")
    BLOG_CONTENT = (By.CSS_SELECTOR, "section[class='mt-5 text-gray-600'] div p")
    
    # Comment Section
    COMMENT_SECTION = (By.XPATH, "//h4[normalize-space()='Leave a Comment']")
    NAME_INPUT = (By.XPATH, "//input[@placeholder='Enter your full name']")
    EMAIL_INPUT = (By.XPATH, "//input[@placeholder='Enter your email']")
    MESSAGE_TEXTAREA = (By.XPATH, "//textarea[@placeholder='Write your message here...']")
    SUBMIT_BUTTON = (By.XPATH, "//button[normalize-space()='Submit']")
    
    # Success Message (Toast)
    SUCCESS_MESSAGE = (By.XPATH, "//div[@class='message-text-container']")
    SUCCESS_TOAST = (By.XPATH, "//div[contains(@class, 'card')]//div[@class='message-text-container']")
    SUCCESS_TEXT = (By.XPATH, "//p[contains(text(), 'Your comment were successfully added')]")
    
    # Comments Display
    COMMENTS_HEADER = (By.XPATH, "//h4[contains(text(), 'Comments')]")
    COMMENT_ITEM = (By.XPATH, "//div[contains(@class, 'comment')] | //div[contains(@class, 'bg-gray-50')]")
    
    # More Like This
    MORE_LIKE_THIS = (By.XPATH, "//h4[normalize-space()='More like this']")
    RELATED_BLOGS = (By.XPATH, "//h4[normalize-space()='More like this']/following-sibling::div//a")
    
    # ========== PAGE METHODS ==========
    
    def open(self, base_url):
        """Open the application homepage"""
        self.logger.info("Opening application homepage")
        self.driver.get(base_url)
        return self
    
    def navigate_to_blogs(self):
        """Navigate to Blogs page from homepage"""
        self.logger.info("Navigating to Blogs page")
        
        try:
            # Click Blogs menu
            blogs_menu = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable(self.BLOGS_MENU)
            )
            blogs_menu.click()
            
            # Wait for page to load
            self.waiter.wait_for_present(self.BLOGS_HEADER, timeout=300)
            self.waiter.wait_for_present(self.BLOGS_CONTAINER, timeout=300)
            
            # Verify URL contains blogs
            assert "blogs" in self.driver.current_url.lower(), "URL should contain 'blogs'"
            self.logger.info("Successfully navigated to Blogs page")
            
            # Verify page source contains blogs
            assert "Blogs" in self.driver.page_source, "Page source should contain 'Blogs'"
            self.logger.info("Blogs page source verified")
            
            self.logger.info("Successfully navigated to Blogs page")
            return self
            
        except Exception as e:
            self.logger.error(f"Failed to navigate to Blogs page: {e}")
            raise
        except TimeoutError as te:
            self.logger.error(f"Timeout while navigating to Blogs page: {te}")
            raise
    
    def verify_blogs_page_loaded(self):
        """Verify Blogs page is fully loaded"""
        self.logger.info("Verifying Blogs page loaded")
        
        try:
            # Check header is visible
            header = self.waiter.wait_for_visible(self.BLOGS_HEADER, timeout=15)
            assert header.is_displayed(), "Blogs header should be visible"
            self.logger.info("Blogs header is visible")
            
            # Check blogs container is present
            self.waiter.wait_for_present(self.BLOGS_CONTAINER, timeout=15)
            self.logger.info("Blogs container is present")
            
            self.logger.info("Blogs page verified")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to verify blogs page: {e}")
            return False
    
    def click_first_blog(self):
        """Click on the first blog's Read article button"""
        self.logger.info("Clicking on first blog's Read article button")
        
        try:
            # Wait for Read article buttons to be present
            read_articles = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located(self.READ_ARTICLE_BTN)
            )
            
            # Click the first Read article button
            first_read_article = read_articles[0]
            self.javascript.scroll_to_element(first_read_article)
            first_read_article.click()
            time.sleep(5)
            
            self.logger.info("Successfully clicked on first blog's Read article button")
            return self
            
        except Exception as e:
            self.logger.error(f"Failed to click on first blog: {e}")
            raise
    
    def wait_for_blog_detail_load(self, timeout=15):
        """Wait for blog detail page to load"""
        self.logger.info("Waiting for blog detail to load")
        
        try:
            # Wait for blog detail container
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(self.BLOG_DETAIL_CONTAINER)
            )
            
            # Wait for blog title to be present
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(self.BLOG_TITLE)
            )
            
            # Wait for blog content to be present
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(self.BLOG_CONTENT)
            )
            
            self.logger.info("Blog detail loaded")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load blog detail: {e}")
            return False
    
    def fill_comment(self, name, email, message):
        """Fill comment form"""
        self.logger.info(f"Filling comment form with name: {name}")
        
        try:
            # Scroll to comment section
            comment_section = self.waiter.wait_for_present(self.COMMENT_SECTION, timeout=10)
            self.javascript.scroll_to_element(comment_section)
            time.sleep(1)
            
            # Fill name
            name_field = self.waiter.wait_for_clickable(self.NAME_INPUT, timeout=10)
            name_field.clear()
            name_field.send_keys(name)
            
            # Fill email
            email_field = self.waiter.wait_for_clickable(self.EMAIL_INPUT, timeout=10)
            email_field.clear()
            email_field.send_keys(email)
            
            # Fill message
            message_field = self.waiter.wait_for_clickable(self.MESSAGE_TEXTAREA, timeout=10)
            message_field.clear()
            message_field.send_keys(message)
            
            self.logger.info("Comment form filled successfully")
            return self
            
        except Exception as e:
            self.logger.error(f"Failed to fill comment form: {e}")
            raise
    
    def submit_comment(self):
        """Submit comment"""
        self.logger.info("Submitting comment")
        
        try:
            submit_btn = self.waiter.wait_for_clickable(self.SUBMIT_BUTTON, timeout=10)
            self.javascript.scroll_to_element(submit_btn)
            submit_btn.click()
            time.sleep(3)  # Wait for toast to appear
            
            self.logger.info("Comment submitted")
            return self
            
        except Exception as e:
            self.logger.error(f"Failed to submit comment: {e}")
            raise
    
    def is_success_message_displayed(self, timeout=10):
        """Check if success toast message is displayed"""
        self.logger.info("Checking success toast message")
        
        try:
            # Wait for toast to appear
            success = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.SUCCESS_TOAST)
            )
            return success.is_displayed()
        except:
            return False

    def get_success_message_text(self):
        """Get success toast message text"""
        try:
            success = self.driver.find_element(*self.SUCCESS_MESSAGE)
            return success.text
        except:
            return ""

    def wait_for_toast_disappear(self, timeout=10):
        """Wait for success toast to disappear"""
        self.logger.info("Waiting for toast to disappear")
        
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located(self.SUCCESS_TOAST)
            )
            self.logger.info("Toast disappeared")
            return True
        except:
            return False
    
    def get_comments_count(self):
        """Get number of comments displayed"""
        self.logger.info("Getting comments count")
        
        try:
            comments_header = self.driver.find_element(*self.COMMENTS_HEADER)
            header_text = comments_header.text
            
            # Extract number from "Comments (1)"
            import re
            match = re.search(r'\((\d+)\)', header_text)
            if match:
                return int(match.group(1))
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to get comments count: {e}")
            return 0
    
    def scroll_to_comments(self):
        """Scroll to comments section"""
        self.logger.info("Scrolling to comments section")
        
        try:
            comments = self.waiter.wait_for_present(self.COMMENTS_HEADER, timeout=10)
            self.javascript.scroll_to_element(comments)
            time.sleep(1)
            return self
            
        except Exception as e:
            self.logger.error(f"Failed to scroll to comments: {e}")
            raise
    
    def scroll_to_more_like_this(self):
        """Scroll to More like this section"""
        self.logger.info("Scrolling to More like this section")
        
        try:
            more_section = self.waiter.wait_for_present(self.MORE_LIKE_THIS, timeout=10)
            self.javascript.scroll_to_element(more_section)
            time.sleep(1)
            return self
            
        except Exception as e:
            self.logger.error(f"Failed to scroll to More like this: {e}")
            raise
    
    def click_more_like_this(self):
        """Click on More like this section"""
        self.logger.info("Clicking on More like this")
        
        try:
            more_section = self.waiter.wait_for_clickable(self.MORE_LIKE_THIS, timeout=10)
            self.javascript.scroll_to_element(more_section)
            more_section.click()
            time.sleep(1)
            
            self.logger.info("Clicked on More like this")
            return self
            
        except Exception as e:
            self.logger.error(f"Failed to click More like this: {e}")
            raise
    
    def verify_related_blogs_exist(self):
        """Verify related blogs exist in More like this section"""
        self.logger.info("Verifying related blogs exist")
        
        try:
            related = self.driver.find_elements(*self.READ_ARTICLE_BTN)
            count = len(related)
            self.logger.info(f"Found {count} related blogs")
            return count > 0
            
        except Exception as e:
            self.logger.error(f"Failed to verify related blogs: {e}")
            return False