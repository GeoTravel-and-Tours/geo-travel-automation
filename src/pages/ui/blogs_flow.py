"""
src/pages/ui/blogs_flow.py

Page Object for the Geo Travel Blogs section.

Covers the full flow end to end:
    1. Navigation      - click "Blogs" in the nav menu, wait for the
                          listing page to load, and verify it via URL and
                          page-source checks.
    2. Blog selection   - open the first blog's detail page and wait for
                          its title/content to render.
    3. Comments         - fill and submit the "Leave a Comment" form, then
                          verify the success toast, check the comment
                          count, and wait for the toast to disappear.
    4. Related content  - scroll to and verify the "More like this"
                          section links to other blog posts.

Tests typically chain ``navigate_to_blogs()`` -> ``click_first_blog()`` ->
``wait_for_blog_detail_load()`` -> ``fill_comment(...)`` ->
``submit_comment()`` -> assertion helpers like
``is_success_message_displayed()``.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from src.core.base_page import BasePage
import time


class BlogsPage(BasePage):
    """Page Object for the Blogs listing, detail, and comment functionality.

    Locators are grouped by section: nav/listing (``BLOGS_MENU`` etc.),
    blog cards on the listing page, the blog detail container, the
    comment form and its success toast, and the "More like this" related
    posts section. No cross-file page-object coupling (unlike
    package_booking_flow.py's use of PaymentPage) - this flow is
    self-contained.
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
    # NOTE: matches on an exact, full utility-class string rather than a
    # stable attribute/test id - fragile if the class list changes at all
    # (e.g. Tailwind class reordering or an added responsive variant).
    BLOGS_MENU = (By.XPATH, "//a[@class='py-2 hover:bg-slate-100 transition-all truncate text-base'][normalize-space()='Blogs']")
    BLOGS_HEADER = (By.XPATH, "//h3[normalize-space()='Blogs']")
    BLOGS_CONTAINER = (By.XPATH, "//div[@class='bg-white p-3 rounded-lg border border-gray-100/70 shadow-sm']")
    
    # Blog Cards
    BLOG_TITLES = (By.XPATH, "//h2[contains(@class, 'text-lg')]")
    FIRST_BLOG_CARD = (By.XPATH, "(//main[@data-sentry-component='BlogPage']//a[contains(@href, '/blogs/')])[1]")
    READ_ARTICLE_BTN = (By.XPATH, "//a[normalize-space()='Read article']")
    
    # Blog Detail Page
    BLOG_DETAIL_CONTAINER = (By.XPATH, "//main[@data-sentry-component='BlogPage']")
    FIRST_BLOG_LINK = (
        By.XPATH,
        "(//a[contains(@href, '/blogs/') and normalize-space()='Read article'])[1]"
    )
    BLOG_TITLE = (
        By.XPATH,
        "//main//h3 | //main//h2"
    )

    BLOG_CONTENT = (
        By.XPATH,
        "//main//section[contains(@class,'text-gray-600')]"
    )
    
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
    RELATED_BLOGS = (
        By.XPATH,
        "//h4[normalize-space()='More like this']"
        "/following-sibling::section//a[contains(@href, '/blogs/')]"
    )
    
    # ========== PAGE METHODS ==========
    
    def open(self, base_url):
        """Open the application homepage directly via ``driver.get``.

        Args:
            base_url (str): Full URL of the homepage to load.

        Returns:
            BlogsPage: ``self``, for method chaining.
        """
        self.logger.info("Opening application homepage")
        self.driver.get(base_url)
        return self

    def navigate_to_blogs(self):
        """Click "Blogs" in the nav menu and verify the listing page loaded.

        Verification checks both the URL (contains "blogs") and the page
        source (contains "Blogs") after the header/container locators
        become present.

        NOTE: the two ``wait_for_present`` calls use a 300s timeout - far
        longer than the 10-15s used elsewhere in this class - which looks
        like a leftover from debugging a slow-loading environment rather
        than an intentional wait budget.

        Returns:
            BlogsPage: ``self``, for method chaining.

        Raises:
            AssertionError: If the URL or page source doesn't confirm the
                Blogs page loaded.
            Exception: Re-raised for any other navigation failure.
        """
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

    def verify_blogs_page_loaded(self):
        """Verify the Blogs listing page has fully loaded.

        Returns:
            bool: True if the header is visible and the container is
                present, False on any failure (logged rather than raised).
        """
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
        """Click the "Read article" link of the first blog card and wait for navigation.

        Returns:
            BlogsPage: ``self``, for method chaining.

        Raises:
            TimeoutException: If the link never becomes clickable or the
                URL doesn't update to include "/blogs/" in time.
        """
        self.logger.info("Clicking first blog")

        first_blog = WebDriverWait(self.driver, 15).until(
            EC.element_to_be_clickable(self.FIRST_BLOG_LINK)
        )

        self.javascript.scroll_to_element(first_blog)
        first_blog.click()

        WebDriverWait(self.driver, 15).until(
            lambda driver: "/blogs/" in driver.current_url
        )

        self.logger.info(
            f"Opened blog: {self.driver.current_url}"
        )

        return self

    def wait_for_blog_detail_load(self, timeout=15):
        """Wait for the blog detail page's URL, title, and content to load.

        Args:
            timeout (int): Seconds to wait for each condition. Defaults
                to 15.

        Returns:
            bool: True once URL, title, and content are all confirmed.

        Raises:
            AssertionError: If any condition times out, wrapping the
                original ``TimeoutException``.
        """
        self.logger.info("Waiting for blog detail page")

        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: "/blogs/" in driver.current_url
            )
            self.logger.info(
                f"Blog detail URL confirmed: {self.driver.current_url}"
            )

            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.BLOG_TITLE)
            )
            self.logger.info("Blog title is visible")

            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.BLOG_CONTENT)
            )
            self.logger.info("Blog content is visible")

            return True

        except TimeoutException as e:
            raise AssertionError(
                f"Blog detail failed to load. "
                f"URL: {self.driver.current_url}"
            ) from e
    
    def fill_comment(self, name, email, message):
        """Scroll to the comment section and fill in name, email, and message.

        Args:
            name (str): Commenter's full name.
            email (str): Commenter's email address.
            message (str): Comment body text.

        Returns:
            BlogsPage: ``self``, for method chaining (e.g. with
                ``submit_comment``).

        Raises:
            Exception: Re-raised if the comment section or any field
                can't be located/filled in time.
        """
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
        """Click Submit and wait for the success toast to appear.

        Returns:
            BlogsPage: ``self``, for method chaining.

        Raises:
            Exception: Re-raised if the submit button can't be clicked or
                the success toast never appears in time.
        """
        self.logger.info("Submitting comment")
        
        try:
            submit_btn = self.waiter.wait_for_clickable(self.SUBMIT_BUTTON, timeout=10)
            self.javascript.scroll_to_element(submit_btn)
            submit_btn.click()
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(self.SUCCESS_TOAST)
            )
            
            self.logger.info("Comment submitted")
            return self
            
        except Exception as e:
            self.logger.error(f"Failed to submit comment: {e}")
            raise
    
    def is_success_message_displayed(self, timeout=10):
        """Check if the comment-submitted success toast is displayed.

        Args:
            timeout (int): Seconds to wait for the toast. Defaults to 10.

        Returns:
            bool: True if the toast became visible in time, False on
                timeout or any other error.
        """
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
        """Get the success toast's text content.

        Returns:
            str: The toast's text, or "" if it isn't present/found.
        """
        try:
            success = self.driver.find_element(*self.SUCCESS_MESSAGE)
            return success.text
        except:
            return ""

    def wait_for_toast_disappear(self, timeout=10):
        """Wait for the success toast to become invisible.

        Args:
            timeout (int): Seconds to wait. Defaults to 10.

        Returns:
            bool: True if the toast disappeared in time, False on
                timeout or any other error.
        """
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
        """Parse the comment count out of the "Comments (N)" header text.

        Returns:
            int: The parsed count, or 0 if the header isn't found or
                doesn't contain a parenthesized number.
        """
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
        """Scroll the comments header into view.

        Returns:
            BlogsPage: ``self``, for method chaining.

        Raises:
            Exception: Re-raised if the header can't be located.
        """
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
        """Scroll the "More like this" section into view.

        Returns:
            BlogsPage: ``self``, for method chaining.

        Raises:
            Exception: Re-raised if the section can't be located.
        """
        self.logger.info("Scrolling to More like this section")

        try:
            more_section = self.waiter.wait_for_present(self.MORE_LIKE_THIS, timeout=10)
            self.javascript.scroll_to_element(more_section)
            time.sleep(1)
            return self
            
        except Exception as e:
            self.logger.error(f"Failed to scroll to More like this: {e}")
            raise
    
    def verify_more_like_this(self):
        """Verify the "More like this" section is visible and has related blog links.

        Returns:
            BlogsPage: ``self``, for method chaining.

        Raises:
            AssertionError: If no related blog links are found.
            TimeoutException: If the section never becomes visible or the
                related links never appear.
        """
        self.logger.info("Verifying More like this section")

        section = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located(self.MORE_LIKE_THIS)
        )

        self.javascript.scroll_to_element(section)

        related_blogs = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located(self.RELATED_BLOGS)
        )

        assert related_blogs, "More like this should contain related blogs"

        self.logger.info(
            f"More like this verified: {len(related_blogs)} related blogs"
        )

        return self
    
    def verify_related_blogs_exist(self):
        """Count the related blog links in the "More like this" section.

        Returns:
            int: The number of related blog links found (0 means none).

        Raises:
            TimeoutException: If no related links appear within 10s.
        """
        self.logger.info("Verifying related blogs exist")

        related_blogs = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located(self.RELATED_BLOGS)
        )

        count = len(related_blogs)

        self.logger.info(
            f"Found {count} related blog links"
        )

        return count > 0