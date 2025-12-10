# configs/environment.py

import os
import requests
import time
from dotenv import load_dotenv
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from urllib3.util.retry import Retry
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from requests.adapters import HTTPAdapter
from src.utils.logger import GeoLogger

load_dotenv()


class EnvironmentConfig:
    """Configuration for cross-browser testing and API testing"""
    
    
    # Environment URLs
    ENVIRONMENTS = {
        "dev": {
            "base_url": "https://retail.dev.gowithgeo.com",
            "api_base_url": "https://api.dev.gowithgeo.com",
            "partners_api_base_url": "https://sandbox.api.developers.gowithgeo.com"
        },
        "qa": {
            "base_url": "https://retail.qa.gowithgeo.com", 
            "api_base_url": "https://api.qa.gowithgeo.com",
            "partners_api_base_url": "https://sandbox.api.developers.gowithgeo.com"
        },
        "staging": {
            "base_url": "https://retail.stg.gowithgeo.com",
            "api_base_url": "https://api.stg.gowithgeo.com",
            "partners_api_base_url": "https://sandbox.api.developers.gowithgeo.com"
        },
        'production': {
            'base_url': 'https://www.gowithgeo.com',
            'api_base_url': 'https://api.gowithgeo.com',
            'partners_api_base_url': 'https://api.developers.gowithgeo.com'
        }
    }

    # Browser configurations
    BROWSERS = {
        "chrome": {
            "driver_class": webdriver.Chrome,
            "options_class": webdriver.ChromeOptions,
            "manager": ChromeDriverManager,
        },
        "firefox": {
            "driver_class": webdriver.Firefox,
            "options_class": webdriver.FirefoxOptions,
            "manager": GeckoDriverManager,
        },
        "edge": {
            "driver_class": webdriver.Edge,
            "options_class": webdriver.EdgeOptions,
            "manager": EdgeChromiumDriverManager,
        },
    }

    # Environment variables
    TEST_ENV = os.getenv("TEST_ENV", "qa").lower()
    BROWSER = os.getenv("BROWSER", "chrome").lower()
    HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
    WINDOW_SIZE = os.getenv("WINDOW_SIZE", "1920x1080")
    TIMEOUT = int(os.getenv("TIMEOUT", "10"))
    
    
    # API-specific environment variables
    API_BASE_URL = os.getenv("API_BASE_URL")
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
    API_MAX_RETRIES = int(os.getenv("API_MAX_RETRIES", "3"))
    
    # API Test Credentials (should be in .env file)
    API_TEST_EMAIL = os.getenv("API_TEST_EMAIL", "test@example.com")
    API_TEST_PASSWORD = os.getenv("API_TEST_PASSWORD", "testpass123")
    
    # API Endpoints availability check
    API_HEALTH_ENDPOINTS = {
        "auth": "/api/auth/login",
        "flights": "/api/flight/search-request", 
        "packages": "/api/package/all",
        "visa": "/api/visa/create"
    }

    # Token Extraction Configuration - Customizable per environment
    # Controls how tokens are extracted from auth responses
    TOKEN_EXTRACTION_CONFIG = {
        'dev': {
            'response_fields': ['access_token', 'accessToken', 'token'],
            'cookie_names': ['retail_access_token', 'partners_access_token', 'auth_token', 'access_token', 'session'],
            'nested_path': 'data',
            'try_cookies_first': False,
            'validate_token': True,
        },
        'qa': {
            'response_fields': ['access_token', 'accessToken', 'token'],
            'cookie_names': ['retail_access_token', 'partners_access_token', 'auth_token', 'access_token', 'session'],
            'nested_path': 'data',
            'try_cookies_first': False,
            'validate_token': True,
        },
        'staging': {
            'response_fields': ['access_token', 'accessToken', 'token'],
            'cookie_names': ['retail_access_token', 'partners_access_token', 'auth_token', 'access_token', 'session'],
            'nested_path': 'data',
            'try_cookies_first': False,
            'validate_token': True,
        },
        'production': {
            'response_fields': ['access_token', 'accessToken', 'token'],
            'cookie_names': ['retail_access_token', 'partners_access_token', 'auth_token', 'access_token', 'session', 'jwt'],
            'nested_path': 'data',
            'try_cookies_first': False,
            'validate_token': True,
        }
    }

    
    @classmethod
    def get_base_url(cls, environment=None):
        env = environment or cls.TEST_ENV
        return cls.ENVIRONMENTS.get(env, {}).get("base_url")

    @classmethod
    def get_browser_config(cls, browser=None):
        browser = browser or cls.BROWSER
        return cls.BROWSERS.get(browser, cls.BROWSERS["chrome"])
    
    @classmethod
    def get_browser_capabilities(cls, browser=None):
        browser = browser or cls.BROWSER
        capabilities = {}

        if browser == "edge":
            capabilities = {
                "acceptInsecureCerts": True,
                "unhandledPromptBehavior": "accept",
                "pageLoadStrategy": "normal"
            }

        return capabilities

    @classmethod
    def get_browser_options(cls, browser=None):
        browser_config = cls.get_browser_config(browser)
        options = browser_config["options_class"]()

        # Common options for all browsers
        if cls.HEADLESS:
            if hasattr(options, "add_argument"):  # Chrome/Edge
                options.add_argument("--headless")
            elif hasattr(options, "headless"):  # Firefox
                options.headless = True

        if cls.WINDOW_SIZE and hasattr(options, "add_argument"):
            options.add_argument(f"--window-size={cls.WINDOW_SIZE}")

        # Browser-specific options
        if browser == "chrome" or browser == "edge":
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            
            # EDGE-SPECIFIC FIXES:
            if browser == "edge":
                options.add_argument("--ignore-certificate-errors")
                options.add_argument("--ignore-ssl-errors")
                options.add_argument("--disable-web-security")
                options.add_argument("--allow-running-insecure-content")
                options.add_argument("--disable-features=VizDisplayCompositor")
                options.add_argument("--disable-extensions")
                options.add_argument("--disable-plugins")
                options.add_argument("--disable-default-apps")
                options.add_argument("--disable-component-extensions-with-background-pages")
                options.add_argument("--disable-background-timer-throttling")
                options.add_argument("--disable-renderer-backgrounding")
                options.add_argument("--disable-backgrounding-occluded-windows")
                
        elif browser == "firefox":
            options.set_preference("dom.webdriver.enabled", False)
            options.set_preference("useAutomationExtension", False)
            # Firefox specific connection fixes
            options.set_preference("network.http.use-cache", False)
            options.set_preference("browser.cache.disk.enable", False)
            options.set_preference("browser.cache.memory.enable", False)

        return options
    
    @classmethod
    def get_environment_metadata(cls):
        """Get comprehensive environment metadata for reporting"""
        return {
            "environment": cls.TEST_ENV.upper(),
            "browser": cls.BROWSER.upper(),
            "headless": cls.HEADLESS,
            "window_size": cls.WINDOW_SIZE,
            "timeout": cls.TIMEOUT,
            "base_url": cls.get_base_url(),
            "api_base_url": cls.get_api_base_url()
        }

    # ========== API-SPECIFIC METHODS ==========
    @classmethod
    def get_api_base_url(cls, environment=None):
        """Get API base URL for the specified environment"""
        env = environment or cls.TEST_ENV
        
        # If API_BASE_URL is explicitly set in environment, use it
        if cls.API_BASE_URL:
            return cls.API_BASE_URL
            
        # Otherwise use the environment-specific API URL
        return cls.ENVIRONMENTS.get(env, {}).get("api_base_url")
    
    @classmethod
    def get_partners_api_base_url(cls, environment=None):
        """Get Partners API base URL for the specified environment"""
        env = environment or cls.TEST_ENV
        
        # If PARTNERS_API_BASE_URL is explicitly set in environment, use it
        partners_api_url = os.getenv("PARTNERS_API_BASE_URL")
        if partners_api_url:
            return partners_api_url
            
        # Otherwise use the environment-specific Partners API URL
        return cls.ENVIRONMENTS.get(env, {}).get("partners_api_base_url")
    
    @classmethod
    def get_token_extraction_config(cls, environment=None):
        """
        Get token extraction configuration for the specified environment.
        
        This configuration controls how authentication tokens are extracted from API responses.
        Supports:
        - Multiple response field names (access_token, accessToken, token, etc.)
        - Cookie-based token extraction
        - Configurable nesting paths
        - Token validation
        
        Args:
            environment: Environment name (dev, qa, staging, production)
                        If None, uses TEST_ENV
        
        Returns:
            Dictionary with token extraction configuration
        """
        env = environment or cls.TEST_ENV
        config = cls.TOKEN_EXTRACTION_CONFIG.get(env)
        
        if not config:
            # Return default config if environment not found
            logger = GeoLogger("EnvironmentConfig")
            logger.warning(f"⚠️ No token extraction config for {env}, using defaults")
            return cls.TOKEN_EXTRACTION_CONFIG.get('qa', {})
        
        return config
    
    @classmethod
    def override_token_extraction_config(cls, environment, config_updates):
        """
        Override token extraction configuration for an environment.
        Useful for environment-specific customizations.
        
        Args:
            environment: Environment name
            config_updates: Dictionary of config updates to merge
        """
        if environment in cls.TOKEN_EXTRACTION_CONFIG:
            cls.TOKEN_EXTRACTION_CONFIG[environment].update(config_updates)
    
    # Partners API Verified Test Account
    PARTNERS_VERIFIED_EMAIL = os.getenv("PARTNERS_VERIFIED_EMAIL")
    PARTNERS_VERIFIED_PASSWORD = os.getenv("PARTNERS_VERIFIED_PASSWORD")
    
    @classmethod
    def get_verified_partners_account(cls):
        """Get verified partners account from environment variables"""
        if not cls.PARTNERS_VERIFIED_EMAIL or not cls.PARTNERS_VERIFIED_PASSWORD:
            raise ValueError(
                "Partners verified account credentials not found in environment variables. "
                "Please set PARTNERS_VERIFIED_EMAIL and PARTNERS_VERIFIED_PASSWORD in .env file"
            )
        
        return {
            "email": cls.PARTNERS_VERIFIED_EMAIL,
            "password": cls.PARTNERS_VERIFIED_PASSWORD,
        }
    
    @classmethod
    def validate_partners_credentials(cls):
        """Validate that partners credentials are properly set"""
        credentials = cls.get_verified_partners_account()
        
        if not credentials["email"] or not credentials["password"]:
            return False
            
        # Basic validation - email format
        if "@" not in credentials["email"]:
            return False
            
        return True

    @classmethod
    def get_api_credentials(cls):
        """Get API test credentials"""
        return {
            "email": cls.API_TEST_EMAIL,
            "password": cls.API_TEST_PASSWORD
        }

    @classmethod
    def is_api_accessible(cls, endpoint=None, environment=None, max_attempts=3, timeout=10):
        """Check if API endpoint is accessible with retry logic"""
        logger = GeoLogger("APICheck")

        api_base_url = cls.get_api_base_url(environment)
        if not api_base_url:
            logger.error("No API base URL configured")
            return False

        # Use a simple health check endpoint or the provided one
        check_endpoint = endpoint or "/api/auth/login"

        # FIX: Properly construct the full URL
        full_url = f"{api_base_url}{check_endpoint}"

        # Debug logging to see what URL is being checked
        logger.debug(f"Checking API accessibility at: {full_url}")

        session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))

        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"API health check attempt {attempt}/{max_attempts} for {full_url}")

                # For GET endpoints, use GET; for others, use HEAD to check availability
                if endpoint in ["/api/auth/login", "/api/package/all", ]:
                    response = session.get(full_url, timeout=timeout, verify=False)
                else:
                    response = session.head(full_url, timeout=timeout, verify=False)

                # Consider any non-5xx status as accessible
                if response.status_code < 500:
                    logger.success(f"API endpoint {check_endpoint} is accessible (Status: {response.status_code})")
                    return True
                else:
                    logger.warning(f"API endpoint responded with status {response.status_code}")

            except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
                logger.error(f"API check attempt {attempt} failed: {e}")

            # Wait before retry
            if attempt < max_attempts:
                wait_time = 2 * attempt  # Shorter wait for API checks
                logger.info(f"Waiting {wait_time}s before next API check...")
                time.sleep(wait_time)

        logger.error(f"API endpoint {check_endpoint} is not accessible after {max_attempts} attempts")
        return False

    @classmethod
    def wait_for_api_environment(cls, environment=None, timeout=60, check_interval=5):
        """Wait for API environment to become available"""
        logger = GeoLogger("APICheck")
        
        env = environment or cls.TEST_ENV
        api_base_url = cls.get_api_base_url(env)
        start_time = time.time()
        attempt = 1
        
        logger.info(f"Waiting for API environment: {api_base_url}")
        
        while time.time() - start_time < timeout:
            if cls.is_api_accessible(environment=env, max_attempts=1):
                logger.success(f"API environment {env} is now accessible")
                return True
            
            wait_time = 3 * attempt  # Shorter intervals for API
            logger.info(f"Waiting for API environment... (attempt {attempt}, waiting {wait_time}s)")
            time.sleep(wait_time)
            attempt += 1
        
        logger.error(f"API environment {env} did not become accessible within {timeout} seconds")
        return False

    @classmethod
    def check_api_health_comprehensive(cls, environment=None):
        """Comprehensive API health check across multiple endpoints"""
        logger = GeoLogger("APICheck")
        env = environment or cls.TEST_ENV
        
        logger.info(f"Running comprehensive API health check for {env}")
        
        health_status = {}
        api_base_url = cls.get_api_base_url(env)
        
        for service, endpoint in cls.API_HEALTH_ENDPOINTS.items():
            is_healthy = cls.is_api_accessible(endpoint, env, max_attempts=2)
            health_status[service] = {
                "healthy": is_healthy,
                "endpoint": f"{api_base_url}{endpoint}"
            }
            
            if is_healthy:
                logger.success(f"{service.upper()} API is healthy")
            else:
                logger.error(f"{service.upper()} API is not accessible")
        
        # Overall health status
        all_healthy = all(status["healthy"] for status in health_status.values())
        
        if all_healthy:
            logger.success("All API services are healthy! 🎉")
        else:
            unhealthy_services = [service for service, status in health_status.items() if not status["healthy"]]
            logger.warning(f"Unhealthy API services: {', '.join(unhealthy_services)}")
        
        return health_status

    @classmethod
    def should_skip_api_tests(cls, environment=None):
        """Determine if API tests should be skipped based on environment health"""
        logger = GeoLogger("APICheck")
        env = environment or cls.TEST_ENV
        
        try:
            # Minimum health check: authentication endpoint
            is_auth_accessible = cls.is_api_accessible("/api/auth/login", env)
        except Exception as e:
            logger.error(f"API health check failed: {e}")
            return True     # skip tests if health check fails
        
        if not is_auth_accessible:
            logger.warning(f"API tests will be skipped - authentication endpoint not accessible in {env}")
            return True
            
        logger.info(f"API environment healthy - proceeding with tests in {env}")
        return False

    # ========== ENVIRONMENTS CHECK ==========
    @classmethod
    def is_environment_accessible(cls, environment=None, max_attempts=3, timeout=10, check_type="ui"):
        """
        Enhanced environment check that supports both UI and API
        
        Args:
            check_type: "ui" for frontend, "api" for backend, "both" for both
        """
        logger = GeoLogger("EnvironmentCheck")
        
        env = environment or cls.TEST_ENV
        
        if check_type == "ui":
            return cls._is_ui_accessible(env, max_attempts, timeout)
        elif check_type == "api":
            return cls.is_api_accessible(environment=env, max_attempts=max_attempts, timeout=timeout)
        elif check_type == "both":
            ui_accessible = cls._is_ui_accessible(env, max_attempts, timeout)
            api_accessible = cls.is_api_accessible(environment=env, max_attempts=max_attempts, timeout=timeout)
            return ui_accessible and api_accessible
        else:
            logger.error(f"Unknown check type: {check_type}")
            return False

    @classmethod
    def _is_ui_accessible(cls, environment, max_attempts, timeout):
        """Original UI accessibility check (moved from existing method)"""
        logger = GeoLogger("EnvironmentCheck")
        base_url = cls.get_base_url(environment)
        
        if not base_url:
            logger.error(f"No base URL found for environment: {environment}")
            return False
            
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"UI environment check attempt {attempt}/{max_attempts} for {base_url}")
                response = session.get(base_url, timeout=timeout, verify=False)
                
                if response.status_code < 500:
                    logger.success(f"UI environment {environment} is accessible (Status: {response.status_code})")
                    return True
                else:
                    logger.warning(f"UI environment responded with status {response.status_code}")
                    
            except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
                logger.error(f"UI check attempt {attempt} failed: {e}")
            
            if attempt < max_attempts:
                wait_time = 5 * attempt
                logger.info(f"Waiting {wait_time}s before next UI check...")
                time.sleep(wait_time)
        
        logger.error(f"UI environment {environment} is not accessible after {max_attempts} attempts")
        return False