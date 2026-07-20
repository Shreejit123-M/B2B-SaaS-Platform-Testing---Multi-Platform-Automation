"""HTTP API client for REST API testing.

Provides wrapper around requests library with retry logic, logging, and error handling.
"""

import requests
from typing import Dict, Any, Optional, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import logging

logger = logging.getLogger(__name__)


class APIClient:
    """HTTP client for API testing with retry logic and session management."""
    
    def __init__(self, base_url: str, timeout: int = 30, max_retries: int = 3):
        """Initialize API client.
        
        Args:
            base_url: Base URL for API.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries on failure.
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = self._create_session()
        self.headers: Dict[str, str] = {
            "Content-Type": "application/json",
        }
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry strategy.
        
        Returns:
            requests.Session: Configured session with retry logic.
        """
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def set_auth_header(self, token: str) -> None:
        """Set authorization header.
        
        Args:
            token: Bearer token for authentication.
        """
        self.headers["Authorization"] = f"Bearer {token}"
    
    def set_tenant_header(self, tenant_id: str) -> None:
        """Set tenant ID header for multi-tenant support.
        
        Args:
            tenant_id: Tenant identifier.
        """
        self.headers["X-Tenant-ID"] = tenant_id
    
    def set_header(self, key: str, value: str) -> None:
        """Set custom header.
        
        Args:
            key: Header key.
            value: Header value.
        """
        self.headers[key] = value
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None, **kwargs) -> requests.Response:
        """Make GET request.
        
        Args:
            endpoint: API endpoint (relative to base_url).
            params: Query parameters.
            headers: Additional headers.
            **kwargs: Additional arguments for requests.get.
            
        Returns:
            requests.Response: Response object.
        """
        url = self._build_url(endpoint)
        merged_headers = {**self.headers, **(headers or {})}
        
        logger.info(f"GET {url}")
        response = self.session.get(url, params=params, headers=merged_headers,
                                   timeout=self.timeout, **kwargs)
        self._log_response(response)
        return response
    
    def post(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None,
             headers: Optional[Dict[str, str]] = None, **kwargs) -> requests.Response:
        """Make POST request.
        
        Args:
            endpoint: API endpoint.
            json_data: JSON request body.
            headers: Additional headers.
            **kwargs: Additional arguments for requests.post.
            
        Returns:
            requests.Response: Response object.
        """
        url = self._build_url(endpoint)
        merged_headers = {**self.headers, **(headers or {})}
        
        logger.info(f"POST {url}")
        response = self.session.post(url, json=json_data, headers=merged_headers,
                                    timeout=self.timeout, **kwargs)
        self._log_response(response)
        return response
    
    def put(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None, **kwargs) -> requests.Response:
        """Make PUT request.
        
        Args:
            endpoint: API endpoint.
            json_data: JSON request body.
            headers: Additional headers.
            **kwargs: Additional arguments for requests.put.
            
        Returns:
            requests.Response: Response object.
        """
        url = self._build_url(endpoint)
        merged_headers = {**self.headers, **(headers or {})}
        
        logger.info(f"PUT {url}")
        response = self.session.put(url, json=json_data, headers=merged_headers,
                                   timeout=self.timeout, **kwargs)
        self._log_response(response)
        return response
    
    def patch(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None,
              headers: Optional[Dict[str, str]] = None, **kwargs) -> requests.Response:
        """Make PATCH request.
        
        Args:
            endpoint: API endpoint.
            json_data: JSON request body.
            headers: Additional headers.
            **kwargs: Additional arguments for requests.patch.
            
        Returns:
            requests.Response: Response object.
        """
        url = self._build_url(endpoint)
        merged_headers = {**self.headers, **(headers or {})}
        
        logger.info(f"PATCH {url}")
        response = self.session.patch(url, json=json_data, headers=merged_headers,
                                     timeout=self.timeout, **kwargs)
        self._log_response(response)
        return response
    
    def delete(self, endpoint: str, headers: Optional[Dict[str, str]] = None,
               **kwargs) -> requests.Response:
        """Make DELETE request.
        
        Args:
            endpoint: API endpoint.
            headers: Additional headers.
            **kwargs: Additional arguments for requests.delete.
            
        Returns:
            requests.Response: Response object.
        """
        url = self._build_url(endpoint)
        merged_headers = {**self.headers, **(headers or {})}
        
        logger.info(f"DELETE {url}")
        response = self.session.delete(url, headers=merged_headers,
                                      timeout=self.timeout, **kwargs)
        self._log_response(response)
        return response
    
    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint.
        
        Args:
            endpoint: Relative endpoint path.
            
        Returns:
            str: Full URL.
        """
        if endpoint.startswith("http"):
            return endpoint
        return f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    
    def _log_response(self, response: requests.Response) -> None:
        """Log response details.
        
        Args:
            response: Response object.
        """
        logger.info(f"Response: {response.status_code}")
        if not response.ok:
            logger.warning(f"Response body: {response.text}")
    
    def close(self) -> None:
        """Close session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
