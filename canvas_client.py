import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class CanvasAPIError(Exception):
    """Base exception for Canvas API errors."""
    pass

class CanvasAuthError(CanvasAPIError):
    """Raised when authentication fails."""
    pass

class CanvasForbiddenError(CanvasAPIError):
    """Raised when the user is not allowed to access the resource."""
    pass

class CanvasNotFoundError(CanvasAPIError):
    """Raised when the resource is not found."""
    pass

class CanvasClient:
    """
    A robust client for interacting with the Canvas LMS API.
    """
    def __init__(self, base_url, access_token, timeout=10, retries=3):
        """
        Initialize the CanvasClient.

        Args:
            base_url (str): The base URL of the Canvas instance.
            access_token (str): The developer access token for authentication.
            timeout (int, optional): Request timeout in seconds. Defaults to 10.
            retries (int, optional): Number of retries for 5xx errors. Defaults to 3.
        """
        if not base_url:
            raise ValueError("base_url is required")
        if not access_token:
            raise ValueError("access_token is required")
        
        self.base_url = base_url.rstrip('/')
        self.access_token = access_token
        self.timeout = timeout
        
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
        
        # Setup retry strategy
        retry_strategy = Retry(
            total=retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _handle_error(self, response):
        """Map HTTP error codes to custom exceptions."""
        if response.status_code == 401:
            raise CanvasAuthError("Authentication failed: Invalid access token.")
        elif response.status_code == 403:
            raise CanvasForbiddenError("Forbidden: You do not have permission to access this resource.")
        elif response.status_code == 404:
            raise CanvasNotFoundError(f"Not Found: {response.url}")
        elif response.status_code >= 400:
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                raise CanvasAPIError(f"API Error: {e}")

    def _get(self, endpoint, params=None):
        """Base GET method with error handling and timeout."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.get(url, params=params, timeout=self.timeout)
        self._handle_error(response)
        return response.json()

    def _get_all(self, endpoint, params=None):
        """Fetch all pages with error handling and timeout."""
        all_items = []
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        while url:
            response = self.session.get(url, params=params, timeout=self.timeout)
            self._handle_error(response)
            
            items = response.json()
            if isinstance(items, list):
                all_items.extend(items)
            else:
                all_items.append(items)
                break

            url = response.links.get('next', {}).get('url')
            params = None 
            
        return all_items

    def get_user_self(self):
        """Retrieve the current user."""
        return self._get("api/v1/users/self")

    def get_courses(self, params=None):
        """Retrieve the user's courses."""
        return self._get_all("api/v1/courses", params=params)

    def get_enrollments(self, course_id, params=None):
        """Retrieve enrollments for a course."""
        return self._get_all(f"api/v1/courses/{course_id}/enrollments", params=params)

    def get_assignments(self, course_id, params=None):
        """Retrieve assignments for a course."""
        return self._get_all(f"api/v1/courses/{course_id}/assignments", params=params)
