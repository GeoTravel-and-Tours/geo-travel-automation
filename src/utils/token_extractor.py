# src/utils/token_extractor.py

from typing import Optional, Dict, Any, Tuple
import re
from src.utils.logger import GeoLogger
from configs.environment import EnvironmentConfig


class TokenExtractor:
    """
    Dynamic token extraction utility that handles multiple sources and strategies.
    Supports response body, cookies, and headers with environment-specific configuration.
    """
    
    # Default field names to check in response body (in order of priority)
    DEFAULT_RESPONSE_FIELDS = [
        'access_token',
        'accessToken',
        'token',
        'auth_token',
        'authToken',
    ]
    
    # Default cookie names to check
    DEFAULT_COOKIE_NAMES = [
        'retail_access_token',      # Retail API cookie
        'partners_access_token',    # Partners API cookie
        'auth_token',
        'access_token',
        'accessToken',
        'session',
        'session_id',
        'jwt',
    ]
    
    # Environment-specific configurations
    ENVIRONMENT_CONFIGS = {
        'dev': {
            'response_fields': ['access_token', 'accessToken', 'token'],
            'cookie_names': ['retail_access_token', 'partners_access_token', 'auth_token', 'access_token'],
            'try_cookies_first': False,
            'nested_path': 'data',
        },
        'qa': {
            'response_fields': ['access_token', 'accessToken', 'token'],
            'cookie_names': ['retail_access_token', 'partners_access_token', 'auth_token', 'access_token'],
            'try_cookies_first': False,
            'nested_path': 'data',
        },
        'staging': {
            'response_fields': ['access_token', 'accessToken', 'token'],
            'cookie_names': ['retail_access_token', 'partners_access_token', 'auth_token', 'access_token'],
            'try_cookies_first': False,
            'nested_path': 'data',
        },
        'production': {
            'response_fields': ['access_token', 'accessToken', 'token'],
            'cookie_names': ['retail_access_token', 'partners_access_token', 'auth_token', 'access_token', 'session', 'jwt'],
            'try_cookies_first': False,
            'nested_path': 'data',
        }
    }
    
    def __init__(self, environment: Optional[str] = None):
        """
        Initialize TokenExtractor with optional environment config.
        
        Args:
            environment: Environment name (dev, qa, staging, production).
                        If None, uses EnvironmentConfig.TEST_ENV.
        """
        self.logger = GeoLogger("TokenExtractor")
        self.environment = environment or EnvironmentConfig.TEST_ENV
        self.config = self._get_environment_config(self.environment)
        self.logger.debug(f"TokenExtractor initialized for environment: {self.environment}")
    
    def _get_environment_config(self, environment: str) -> Dict[str, Any]:
        """Get configuration for specified environment."""
        try:
            config = EnvironmentConfig.get_token_extraction_config(environment)
            if config:
                self.logger.debug(f"Token extraction config loaded for environment: {environment}")
                return config
        except Exception as e:
            self.logger.debug(f"Could not load config from EnvironmentConfig: {e}")
        
        # Fallback to hardcoded config
        config = self.ENVIRONMENT_CONFIGS.get(environment, {})
        if not config:
            self.logger.debug(f"No specific config for {environment}, using defaults")
            return {
                'response_fields': self.DEFAULT_RESPONSE_FIELDS,
                'cookie_names': self.DEFAULT_COOKIE_NAMES,
                'try_cookies_first': False,
                'nested_path': 'data',
            }
        return config
    
    def extract_token(
        self, 
        response: Any,
        nested_path: Optional[str] = None,
        response_fields: Optional[list] = None,
        cookie_names: Optional[list] = None
    ) -> Tuple[Optional[str], str]:
        """
        Extract token from response using multiple strategies.
        
        Extraction priority:
        1. Response body (nested path or top-level fields)
        2. Cookies (by configured names)
        3. Authorization header
        
        Args:
            response: requests.Response object
            nested_path: Path to nested data (e.g., 'data' for response['data']['token'])
            response_fields: List of field names to check in response body
            cookie_names: List of cookie names to check
        
        Returns:
            Tuple of (token, extraction_method) where extraction_method is one of:
            'response_body', 'cookies', 'header', or None
        """
        nested_path = nested_path or self.config.get('nested_path')
        response_fields = response_fields or self.config.get('response_fields', self.DEFAULT_RESPONSE_FIELDS)
        cookie_names = cookie_names or self.config.get('cookie_names', self.DEFAULT_COOKIE_NAMES)
        
        # Strategy 1: Response body
        token = self._extract_from_response_body(response, nested_path, response_fields)
        if token:
            self.logger.debug("Token extracted from response body")
            return token, 'response_body'
        
        # Strategy 2: Cookies
        token = self._extract_from_cookies(response, cookie_names)
        if token:
            self.logger.debug("Token extracted from cookies")
            return token, 'cookies'
        
        # Strategy 3: Authorization header
        token = self._extract_from_header(response)
        if token:
            self.logger.debug("Token extracted from authorization header")
            return token, 'header'
        
        self.logger.debug("No token found in response body, cookies, or headers")
        return None, None
    
    def _extract_from_response_body(
        self,
        response: Any,
        nested_path: Optional[str],
        response_fields: list
    ) -> Optional[str]:
        """Extract token from response JSON body."""
        try:
            response_data = response.json()
        except Exception as e:
            self.logger.debug(f"Cannot parse response JSON: {e}")
            return None
        
        # Check if token is in nested path first
        if nested_path:
            nested_data = response_data.get(nested_path, {})
            for field in response_fields:
                if field in nested_data:
                    token = nested_data[field]
                    if token and isinstance(token, str) and len(token) > 0:
                        self.logger.debug(f"Found token in response['{nested_path}']['{field}']")
                        return token
        
        # Check top-level fields
        for field in response_fields:
            if field in response_data:
                token = response_data[field]
                if token and isinstance(token, str) and len(token) > 0:
                    self.logger.debug(f"Found token in response['{field}']")
                    return token
        
        return None
    
    def _extract_from_cookies(
        self,
        response: Any,
        cookie_names: list
    ) -> Optional[str]:
        """Extract token from response cookies."""
        try:
            cookies = response.cookies
            if not cookies:
                self.logger.debug("No cookies in response")
                return None
            
            for cookie_name in cookie_names:
                if cookie_name in cookies:
                    token = cookies.get(cookie_name)
                    if token and len(token) > 0:
                        self.logger.debug(f"Found token in cookie: {cookie_name}")
                        return token
            
            self.logger.debug(f"No matching cookies found. Available: {list(cookies.keys())}")
            return None
        except Exception as e:
            self.logger.debug(f"Error extracting from cookies: {e}")
            return None
    
    def _extract_from_header(self, response: Any) -> Optional[str]:
        """Extract token from Authorization header in response."""
        try:
            # Sometimes the response includes auth headers
            auth_header = response.headers.get('Authorization', '')
            
            if not auth_header:
                return None
            
            # Extract Bearer token
            match = re.search(r'Bearer\s+([^\s]+)', auth_header, re.IGNORECASE)
            if match:
                token = match.group(1)
                self.logger.debug(f"Found token in Authorization header")
                return token
            
            return None
        except Exception as e:
            self.logger.debug(f"Error extracting from header: {e}")
            return None
    
    def extract_token_from_response_data(
        self,
        response_data: Dict[str, Any],
        nested_path: Optional[str] = None,
        response_fields: Optional[list] = None
    ) -> Tuple[Optional[str], str]:
        """
        Extract token directly from parsed response data dict (for testing/special cases).
        
        Args:
            response_data: Parsed JSON response dict
            nested_path: Path to nested data
            response_fields: List of field names to check
        
        Returns:
            Tuple of (token, extraction_method)
        """
        nested_path = nested_path or self.config.get('nested_path')
        response_fields = response_fields or self.config.get('response_fields', self.DEFAULT_RESPONSE_FIELDS)
        
        # Check nested path first
        if nested_path and nested_path in response_data:
            nested_data = response_data[nested_path]
            if isinstance(nested_data, dict):
                for field in response_fields:
                    token = nested_data.get(field)
                    if token and isinstance(token, str) and len(token) > 0:
                        self.logger.debug(f"Found token in data['{nested_path}']['{field}']")
                        return token, 'response_body'
        
        # Check top-level fields
        for field in response_fields:
            token = response_data.get(field)
            if token and isinstance(token, str) and len(token) > 0:
                self.logger.debug(f"Found token in data['{field}']")
                return token, 'response_body'
        
        self.logger.debug("No token found in response data")
        return None, None
    
    def validate_token(self, token: Optional[str]) -> bool:
        """
        Validate that token looks like a valid JWT or auth token.
        
        Args:
            token: Token string to validate
        
        Returns:
            True if token appears valid, False otherwise
        """
        if not token or not isinstance(token, str):
            return False
        
        # Check for JWT format (three parts separated by dots)
        if token.count('.') == 2:
            return True
        
        # Check for other token formats (reasonable length, alphanumeric)
        if len(token) >= 20 and re.match(r'^[a-zA-Z0-9_\-\.]+$', token):
            return True
        
        return False
    
    def log_extraction_attempt(
        self,
        token: Optional[str],
        extraction_method: Optional[str],
        is_valid: bool
    ) -> None:
        """Log token extraction attempt with details."""
        if token:
            if is_valid:
                self.logger.info(f"Token extracted via {extraction_method} (length: {len(token)}, valid)")
            else:
                self.logger.warning(f"Token extracted via {extraction_method} but validation failed")
        else:
            self.logger.warning("No token found - authentication will fail")
