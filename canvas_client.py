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
