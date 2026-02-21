import requests

class CanvasClient:
    """
    A robust client for interacting with the Canvas LMS API.
    """
    def __init__(self, base_url, access_token):
        """
        Initialize the CanvasClient.

        Args:
            base_url (str): The base URL of the Canvas instance (e.g., https://canvas.instructure.com).
            access_token (str): The developer access token for authentication.
        
        Raises:
            ValueError: If base_url or access_token is missing.
        """
        if not base_url:
            raise ValueError("base_url is required")
        if not access_token:
            raise ValueError("access_token is required")
        
        self.base_url = base_url.rstrip('/')
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})

    def _get(self, endpoint, params=None):
        """
        A base GET method for the Canvas API.

        Args:
            endpoint (str): The API endpoint (e.g., api/v1/users/self).
            params (dict, optional): Query parameters.

        Returns:
            dict: The JSON response from the API.
        
        Raises:
            requests.exceptions.HTTPError: If the request fails.
        """
        # Ensure endpoint starts correctly
        if not endpoint.startswith('api/v1/') and not endpoint.startswith('/api/v1/'):
             # If not starting with api/v1, we assume it's relative to the base
             # but Canvas API generally expects api/v1/...
             pass

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def _get_all(self, endpoint, params=None):
        """
        Fetch all pages of a paginated API endpoint.

        Args:
            endpoint (str): The API endpoint.
            params (dict, optional): Query parameters.

        Returns:
            list: Consolidated JSON response from all pages.
        """
        all_items = []
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        while url:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            items = response.json()
            if isinstance(items, list):
                all_items.extend(items)
            else:
                all_items.append(items)
                break

            # Use requests built-in link header parser
            url = response.links.get('next', {}).get('url')
            # After the first request, the 'next' URL includes existing params
            params = None 
            
        return all_items

    def get_user_self(self):
        """
        Retrieve information about the currently authenticated user.

        Returns:
            dict: The user's profile information.
        """
        return self._get("api/v1/users/self")

    def get_courses(self, params=None):
        """
        Retrieve the list of courses for the authenticated user.

        Args:
            params (dict, optional): Query parameters for filtering courses.

        Returns:
            list: The list of courses.
        """
        return self._get_all("api/v1/courses", params=params)
