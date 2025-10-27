# src/utils/javascript.py

import time
class JavaScriptUtils:
    """Dedicated class for JavaScript operations"""

    def __init__(self, driver):
        self.driver = driver

    def execute_script(self, script, *args):
        """Execute JavaScript"""
        return self.driver.execute_script(script, *args)

    def scroll_to_element(self, element):
        """Scroll to element"""
        self.execute_script("arguments[0].scrollIntoView(true);", element)
    
    def scroll_down(self):
        """Scroll down the page"""
        self.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

    def scroll_up(self):
        """Scroll up the page"""
        self.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
    def highlight_element(self, element, duration=1):
        """Highlight element temporarily"""
        original_style = element.get_attribute("style")
        self.execute_script(
            "arguments[0].setAttribute('style', arguments[1]);",
            element,
            "border: 2px solid red; background: yellow;",
        )
        import time

        time.sleep(duration)
        self.execute_script(
            "arguments[0].setAttribute('style', arguments[1]);", element, original_style
        )

    def wait_for_page_load(self, timeout=30):
        """Wait for page to fully load"""
        import time
        from selenium.webdriver.support.ui import WebDriverWait

        WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
