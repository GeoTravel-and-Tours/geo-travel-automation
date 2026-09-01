"""Central environment/configuration hub for the whole framework.

Loads ``.env`` via ``python-dotenv`` and exposes a single class,
``EnvironmentConfig``, that every other module in this list (and most
page objects/API clients) reads from: which environment to target
(dev/qa/staging/production), the resulting base URLs, which browser to
drive and how to configure it, API timeouts/retry settings, and
per-environment token-extraction rules. It also provides health-check
helpers (``is_api_accessible``, ``is_environment_accessible``, etc.)
used by fixtures to skip tests against an environment that's down.

Nothing here is instantiated - all state lives on class attributes and
all methods are ``@classmethod``s, so callers use ``EnvironmentConfig``
directly (e.g. ``EnvironmentConfig.get_base_url()``) rather than
creating an instance.
"""

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
    """Class-attribute-based configuration for UI and API testing.

    State (all class-level, no instances are created):

    - ``ENVIRONMENTS``: base/API/partners-API URLs per named
      environment (dev/qa/staging/production).
    - ``BROWSERS``: Selenium driver/options classes and
      webdriver-manager classes per supported browser.
    - ``TEST_ENV``, ``BROWSER``, ``HEADLESS``, ``WINDOW_SIZE``,
      ``TIMEOUT``: read once from environment variables at import time
      (via ``os.getenv``), controlling which environment/browser a
      test run targets.
    - ``API_BASE_URL``, ``API_TIMEOUT``, ``API_MAX_RETRIES``,
      ``API_CONNECT_TIMEOUT``, ``API_READ_TIMEOUT``: API-specific
      timing/retry knobs, also read from environment variables.
    - ``API_HEALTH_ENDPOINTS``: named endpoints used by the
      comprehensive health check.
    - ``TOKEN_EXTRACTION_CONFIG``: per-environment rules (response
      field names, cookie names, JSON nesting path) that
      ``TokenExtractor`` uses to pull an auth token out of a login
      response.
    - ``PARTNERS_VERIFIED_EMAIL`` / ``PARTNERS_VERIFIED_PASSWORD``:
      credentials for a known-verified Partners test account, read
      from environment variables.

    Callers across ``src/core`` (``BaseAPI``, ``PartnersBaseAPI``,
    ``BasePage``, ``DriverFactory``) and the page objects/tests rely on
    this class as the single source of truth for environment-dependent
    values, rather than reading ``os.environ`` themselves.
    """


    # Environment URLs
    ENVIRONMENTS = {
        "dev": {
            "base_url": "https://retail.dev.gowithgeo.com",
            "api_base_url": "https://api.dev.gowithgeo.com",
            "partners_api_base_url": "https://sandbox.api.gowithgeo.com"
        },
        "qa": {
            "base_url": "https://retail.qa.gowithgeo.com", 
            "api_base_url": "https://api.qa.gowithgeo.com",
            "partners_api_base_url": "https://sandbox.api.gowithgeo.com"
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
    
    # API Timeout Configuration
    API_CONNECT_TIMEOUT = int(os.getenv("API_CONNECT_TIMEOUT", "10"))
    API_READ_TIMEOUT = int(os.getenv("API_READ_TIMEOUT", "60"))
    
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
        """Look up the app's UI base URL for an environment.

        Args:
            environment (str, optional): Environment name (dev, qa,
                staging, production). Defaults to ``cls.TEST_ENV``.

        Returns:
            str | None: The base URL, or None if ``environment`` isn't
            a recognized key in ``ENVIRONMENTS``.
        """
        env = environment or cls.TEST_ENV
        return cls.ENVIRONMENTS.get(env, {}).get("base_url")

    @classmethod
    def get_browser_config(cls, browser=None):
        """Look up the Selenium driver/options/manager classes for a browser.

        Args:
            browser (str, optional): Browser name ("chrome", "firefox",
                "edge"). Defaults to ``cls.BROWSER``.

        Returns:
            dict: The matching entry from ``BROWSERS``, or the
            "chrome" entry if ``browser`` isn't recognized.
        """
        browser = browser or cls.BROWSER
        return cls.BROWSERS.get(browser, cls.BROWSERS["chrome"])

    @classmethod
    def get_browser_capabilities(cls, browser=None):
        """Get extra WebDriver capabilities needed for a given browser.

        Currently only Edge needs anything special (accepting insecure
        certs, auto-accepting unexpected prompts, and normal page-load
        strategy) - other browsers get an empty dict.

        Args:
            browser (str, optional): Browser name. Defaults to
                ``cls.BROWSER``.

        Returns:
            dict: Capability overrides for the browser (possibly empty).
        """
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
        """Build a fully-configured Options object for the given browser.

        Applies common flags (headless mode, window size) and then
        browser-specific hardening/compatibility flags - notably a
        large block of Edge-only flags to work around Edge-specific
        issues (certificate errors, extensions/background throttling
        interfering with test timing, etc.), and Firefox preferences to
        disable the automation-detection flag and HTTP/disk/memory
        caching (so tests see fresh content instead of cached pages).

        Args:
            browser (str, optional): Browser name. Defaults to
                ``cls.BROWSER``.

        Returns:
            selenium.webdriver.*.Options: A populated options instance
            ready to pass into the corresponding WebDriver constructor.
        """
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
        """Collect a snapshot of the current run's environment settings.

        Returns:
            dict: Environment name, browser, headless flag, window
            size, timeout, and resolved base/API URLs - intended for
            inclusion in test reports.
        """
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
        """Resolve the main API base URL, honoring an explicit override.

        Args:
            environment (str, optional): Environment name. Defaults to
                ``cls.TEST_ENV``. Ignored if ``API_BASE_URL`` is set.

        Returns:
            str | None: ``cls.API_BASE_URL`` if the ``API_BASE_URL``
            env var is set (lets a run point at an arbitrary API host
            regardless of ``environment``); otherwise the
            environment's configured ``api_base_url``.
        """
        env = environment or cls.TEST_ENV

        # If API_BASE_URL is explicitly set in environment, use it
        if cls.API_BASE_URL:
            return cls.API_BASE_URL

        # Otherwise use the environment-specific API URL
        return cls.ENVIRONMENTS.get(env, {}).get("api_base_url")

    @classmethod
    def get_partners_api_base_url(cls, environment=None):
        """Resolve the Partners API base URL, honoring an explicit override.

        Args:
            environment (str, optional): Environment name. Defaults to
                ``cls.TEST_ENV``. Ignored if ``PARTNERS_API_BASE_URL``
                is set.

        Returns:
            str | None: The ``PARTNERS_API_BASE_URL`` env var if set
            (read fresh on every call, unlike ``API_BASE_URL`` which is
            cached as a class attribute); otherwise the environment's
            configured ``partners_api_base_url``.
        """
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

        Returns:
            None. NOTE: if ``environment`` isn't already a key in
            ``TOKEN_EXTRACTION_CONFIG``, this silently does nothing -
            no error is raised and ``config_updates`` is dropped.
        """
        if environment in cls.TOKEN_EXTRACTION_CONFIG:
            cls.TOKEN_EXTRACTION_CONFIG[environment].update(config_updates)

    # Partners API Verified Test Account
    PARTNERS_VERIFIED_EMAIL = os.getenv("PARTNERS_VERIFIED_EMAIL")
    PARTNERS_VERIFIED_PASSWORD = os.getenv("PARTNERS_VERIFIED_PASSWORD")

    @classmethod
    def get_verified_partners_account(cls):
        """Return a known-verified Partners test account's credentials.

        Returns:
            dict: ``{"email": ..., "password": ...}`` built from
            ``PARTNERS_VERIFIED_EMAIL`` / ``PARTNERS_VERIFIED_PASSWORD``.

        Raises:
            ValueError: If either environment variable is unset/empty.
        """
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
        """Sanity-check that the verified Partners credentials look valid.

        Only checks presence and a basic "@" substring in the email -
        not a full email format validation.

        Returns:
            bool: True if both fields are non-empty and the email
            contains "@", False otherwise.

        Raises:
            ValueError: Propagated from ``get_verified_partners_account``
                if the credentials aren't set at all.
        """
        credentials = cls.get_verified_partners_account()

        if not credentials["email"] or not credentials["password"]:
            return False

        # Basic validation - email format
        if "@" not in credentials["email"]:
            return False

        return True

    @classmethod
    def get_api_credentials(cls):
        """Return generic API test credentials.

        FIXME: references ``cls.API_TEST_EMAIL`` / ``cls.API_TEST_PASSWORD``,
        which are never defined as class attributes on
        ``EnvironmentConfig`` (they only exist as ``os.getenv()`` reads
        inside ``src/pages/api/auth_api.py``). Calling this method as
        written raises ``AttributeError`` rather than returning
        credentials - it needs its own
        ``os.getenv("API_TEST_EMAIL")``/``os.getenv("API_TEST_PASSWORD")``
        class attributes (or reuse of whatever ``auth_api.py`` reads)
        before it can work.

        Returns:
            dict: Intended to be ``{"email": ..., "password": ...}``.

        Raises:
            AttributeError: Always, currently, per the FIXME above.
        """
        return {
            "email": cls.API_TEST_EMAIL,
            "password": cls.API_TEST_PASSWORD
        }

    @classmethod
    def is_api_accessible(cls, endpoint=None, environment=None, max_attempts=3, timeout=10):
        """Check whether an API endpoint responds with a non-5xx status.

        Uses a ``requests.Session`` with its own urllib3-level retry
        policy (3 retries on 500/502/503/504) layered underneath this
        method's own attempt loop, so a single call here can trigger
        up to ``max_attempts`` * (that policy's retries) actual HTTP
        attempts in the worst case. TLS verification is disabled
        (``verify=False``) since lower environments may use
        self-signed/staging certificates.

        Args:
            endpoint (str, optional): Path to check, e.g.
                "/api/auth/login". Defaults to "/api/auth/login".
            environment (str, optional): Environment to check against.
                Defaults to ``cls.TEST_ENV``.
            max_attempts (int): Number of check attempts before giving
                up. Defaults to 3.
            timeout (int): Per-request timeout in seconds. Defaults to 10.

        Returns:
            bool: True as soon as a response with status < 500 is
            received; False if no API base URL is configured, or if
            every attempt errors out or returns a 5xx status.
        """
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

                # For GET endpoints, use GET; for others, use HEAD to check availability.
                # NOTE: this allowlist is hardcoded and separate from
                # API_HEALTH_ENDPOINTS - a new health-checked endpoint that
                # doesn't support HEAD would need to be added here too.
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
        """Poll ``is_api_accessible`` until the API responds or time runs out.

        Args:
            environment (str, optional): Environment to wait for.
                Defaults to ``cls.TEST_ENV``.
            timeout (int): Overall time budget in seconds. Defaults to 60.
            check_interval (int): Unused directly (wait time between
                polls is instead computed as ``3 * attempt``, growing
                each iteration) - kept as a parameter for API
                compatibility/callers that pass it explicitly.

        Returns:
            bool: True once ``is_api_accessible`` succeeds; False if
            ``timeout`` seconds elapse without success.
        """
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
        """Check accessibility of every endpoint in ``API_HEALTH_ENDPOINTS``.

        Args:
            environment (str, optional): Environment to check.
                Defaults to ``cls.TEST_ENV``.

        Returns:
            dict: Maps each service name (e.g. "auth", "flights") to a
            dict of ``{"healthy": bool, "endpoint": full URL}``.
        """
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
        """Decide whether API tests should be skipped for this environment.

        Uses only the auth endpoint as a minimal health signal (not the
        full ``check_api_health_comprehensive`` sweep), on the
        assumption that if login is reachable the API is usable enough
        to test against.

        Args:
            environment (str, optional): Environment to check.
                Defaults to ``cls.TEST_ENV``.

        Returns:
            bool: True if tests should be skipped (auth endpoint
            unreachable, or the health check itself raised), False if
            the environment looks healthy enough to proceed.
        """
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
            environment: Environment name to check. Defaults to ``cls.TEST_ENV``.
            max_attempts: Max check attempts to pass through to the
                underlying UI/API check(s).
            timeout: Per-attempt timeout in seconds to pass through.
            check_type: "ui" for frontend, "api" for backend, "both" for both

        Returns:
            bool: Result of the requested check(s). For "both", True
            only if both the UI and API checks succeed. False (and a
            logged error) if ``check_type`` isn't one of the three
            recognized values.
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
        """Check whether the UI base URL responds with a non-5xx status.

        Same shape as ``is_api_accessible``: a session-level urllib3
        retry policy plus its own attempt loop with linear backoff
        (``5 * attempt`` seconds), and TLS verification disabled for
        lower environments.

        Args:
            environment (str): Environment name to resolve a base URL for.
            max_attempts (int): Number of check attempts before giving up.
            timeout (int): Per-request timeout in seconds.

        Returns:
            bool: True once a response with status < 500 is received;
            False if no base URL is configured for ``environment``, or
            every attempt errors out or returns a 5xx status.
        """
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