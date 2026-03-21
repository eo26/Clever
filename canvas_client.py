import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List, Dict, Any, Optional, Union

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
    def __init__(self, base_url: str, access_token: str, timeout: int = 10, retries: int = 3):
        """
        Initialize the CanvasClient.

        Args:
            base_url (str): The base URL of the Canvas instance.
            access_token (str): The developer access token for authentication.
            timeout (int, optional): Request timeout in seconds. Defaults to 10.
            retries (int, optional): Number of retries for 429 and 5xx errors. Defaults to 3.
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
        
        # Setup retry strategy for transient errors
        retry_strategy = Retry(
            total=retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _handle_error(self, response: requests.Response) -> None:
        """
        Map HTTP error codes to custom exceptions.

        Args:
            response (requests.Response): The response object from the request.

        Raises:
            CanvasAuthError: If 401 Unauthorized.
            CanvasForbiddenError: If 403 Forbidden.
            CanvasNotFoundError: If 404 Not Found.
            CanvasAPIError: For other HTTP errors.
        """
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

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Internal base GET method with error handling and timeout.

        Args:
            endpoint (str): The API endpoint relative to the base URL.
            params (dict, optional): Query parameters.

        Returns:
            Any: The parsed JSON response.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.get(url, params=params, timeout=self.timeout)
        self._handle_error(response)
        return response.json()

    def _get_all(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Fetch all pages of a paginated API endpoint.

        Args:
            endpoint (str): The API endpoint.
            params (dict, optional): Initial query parameters.

        Returns:
            List[Any]: Consolidated list of items from all pages.
        """
        all_items: List[Any] = []
        url: Optional[str] = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Current params for the first request
        current_params = params
        
        while url:
            # We use the session.get directly here because url might be absolute from Link header
            response = self.session.get(url, params=current_params, timeout=self.timeout)
            self._handle_error(response)
            
            items = response.json()
            if isinstance(items, list):
                all_items.extend(items)
            else:
                all_items.append(items)
                break

            # Extract next URL from Link header via requests' built-in parser
            url = response.links.get('next', {}).get('url')
            # Once we follow a 'next' link, params are already in the URL
            current_params = None 
            
        return all_items

    def get_user_self(self) -> Dict[str, Any]:
        """
        Retrieve information about the currently authenticated user.

        Returns:
            Dict[str, Any]: The user's profile information.
        """
        return self._get("api/v1/users/self")

    def get_courses(self, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve the list of courses for the authenticated user.

        Args:
            params (dict, optional): Query parameters for filtering courses.

        Returns:
            List[Dict[str, Any]]: The list of courses.
        """
        return self._get_all("api/v1/courses", params=params)

    def get_enrollments(self, course_id: Union[str, int], params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve the list of enrollments for a specific course.

        Args:
            course_id (str|int): The ID of the course.
            params (dict, optional): Query parameters.

        Returns:
            List[Dict[str, Any]]: The list of enrollments.
        """
        return self._get_all(f"api/v1/courses/{course_id}/enrollments", params=params)

    def get_assignments(self, course_id: Union[str, int], params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve the list of assignments for a specific course.

        Args:
            course_id (str|int): The ID of the course.
            params (dict, optional): Query parameters.

        Returns:
            List[Dict[str, Any]]: The list of assignments.
        """
        return self._get_all(f"api/v1/courses/{course_id}/assignments", params=params)

    def get_grading_periods(self, course_id: Union[str, int]) -> List[Dict[str, Any]]:
        """
        Retrieve grading periods for a specific course (e.g., Q1, Q2, Q3, Q4).

        Args:
            course_id (str|int): The ID of the course.

        Returns:
            List[Dict[str, Any]]: The list of grading periods, each containing
                id, title, start_date, end_date, and close_date.
        """
        data = self._get(f"api/v1/courses/{course_id}/grading_periods")
        return data.get("grading_periods", [])

    def get_user_enrollments(
        self,
        user_id: Union[str, int],
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all enrollments for a specific user, including grade data.

        Args:
            user_id (str|int): The Canvas user ID or 'self'.
            params (dict, optional): Query parameters (e.g., state[], type[]).

        Returns:
            List[Dict[str, Any]]: Enrollment records. Each record contains a
                ``grades`` sub-object with ``current_score``, ``final_score``,
                ``current_grade``, and ``final_grade`` fields (letter grades
                are only populated when the course has a grading scheme).
        """
        merged_params = {"include[]": "grades", "per_page": 100}
        if params:
            merged_params.update(params)
        return self._get_all(f"api/v1/users/{user_id}/enrollments", params=merged_params)
