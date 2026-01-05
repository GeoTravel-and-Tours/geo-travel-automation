# src/core/partners_base_api.py

import requests
import time
import json
from datetime import datetime
from src.utils.logger import GeoLogger
from src.utils.token_extractor import TokenExtractor
from configs.environment import EnvironmentConfig

class PartnersBaseAPI:
    """
    Base API class specifically for Partners API endpoints
    Uses different base URL than main API
    """
    def __init__(self):
        self.base_url = EnvironmentConfig.get_partners_api_base_url()
        self.session = requests.Session()
        self.auth_token = None
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Client-Type': 'corporate'
        }
        self.logger = GeoLogger(self.__class__.__name__)
        self.token_extractor = TokenExtractor()
        # ✅ INCREASED TIMEOUT: 30 → 60 seconds
        self.timeout = 60
    
    def set_auth_token(self, token):
        """Set authentication token for Partners API requests"""
        if not token or not isinstance(token, str):
            self.logger.warning("⚠️ Invalid token provided to set_auth_token()")
            return
        
        self.auth_token = token
        self.headers['Authorization'] = f'Bearer {token}'
        self.logger.info(f"✅ Auth token set (length: {len(token)})")
    
    def _request_with_retry(self, method, endpoint, max_retries=3, **kwargs):
        """✅ ADDED: Request with retry logic for timeouts"""
        url = f"{self.base_url}{endpoint}"
        
        # Merge headers
        headers = self.headers.copy()
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))
        
        # Set timeout using EnvironmentConfig
        kwargs.setdefault('timeout', (EnvironmentConfig.API_CONNECT_TIMEOUT, EnvironmentConfig.API_READ_TIMEOUT))
        
        self.logger.info(f"Partners API Request: {method} {url}")
        
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                response = self.session.request(
                    method, 
                    url, 
                    headers=headers, 
                    **kwargs
                )
                
                self.logger.info(f"Partners API Response: {response.status_code}")
                
                # Log response for debugging
                if response.status_code >= 400:
                    # Save response dump for troubleshooting
                    try:
                        from pathlib import Path
                        dump_dir = Path("reports/failed_responses")
                        dump_dir.mkdir(parents=True, exist_ok=True)
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        safe_endpoint = endpoint.strip('/').replace('/', '_') or 'root'
                        dump_file = dump_dir / f"{ts}_{response.status_code}_{safe_endpoint}.txt"
                        with open(dump_file, 'w', encoding='utf-8') as df:
                            df.write(response.text or response.content.decode('utf-8', errors='replace'))
                        self.logger.warning(f"Partners API Error: {response.status_code} - saved dump: {dump_file}")
                    except Exception:
                        self.logger.warning(f"Partners API Error: {response.status_code} - {response.text}")
                
                return response
                
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout) as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    self.logger.warning(
                        f"⏳ Timeout on attempt {attempt + 1}/{max_retries} for {endpoint}, "
                        f"retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"❌ All {max_retries} attempts failed for {endpoint}")
                    raise last_exception
                    
            except (requests.exceptions.ConnectionError, 
        requests.exceptions.ChunkedEncodingError,
        requests.exceptions.ReadTimeout) as e:
                wait_time = 5 * (attempt + 1)  # 5s, 10s, 15s
                self.logger.warning(f"Server connection issue, retry in {wait_time}s...")
                time.sleep(wait_time)
                self.logger.error(f"Partners API Request failed: {str(e)}")
    
    def _request(self, method, endpoint, **kwargs):
        """Base request method with logging and error handling"""
        # ✅ UPDATED: Use retry logic
        response = self._request_with_retry(method, endpoint, max_retries=3, **kwargs)
        if response is None:
            self.logger.error("Response is None. Check the request or server.")
            raise ValueError("API response is None")
        return response
    
    def get(self, endpoint, **kwargs):
        return self._request('GET', endpoint, **kwargs)
    
    def post(self, endpoint, **kwargs):
        return self._request('POST', endpoint, **kwargs)
    
    def put(self, endpoint, **kwargs):
        return self._request('PUT', endpoint, **kwargs)
    
    def patch(self, endpoint, **kwargs):
        return self._request('PATCH', endpoint, **kwargs)
    
    def delete(self, endpoint, **kwargs):
        return self._request('DELETE', endpoint, **kwargs)