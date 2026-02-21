import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Ensure root directory is in path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from canvas_client import CanvasClient
except ImportError:
    CanvasClient = None

class TestCanvasClient(unittest.TestCase):
    def setUp(self):
        self.base_url = "https://example.com"
        self.access_token = "test_token"
        if CanvasClient:
            self.client = CanvasClient(self.base_url, self.access_token)

    def test_initialization_missing_base_url(self):
        """Test that missing base_url raises ValueError."""
        if CanvasClient is None:
            self.fail("CanvasClient not implemented")
        with self.assertRaises(ValueError):
            CanvasClient(None, self.access_token)

    def test_initialization_missing_access_token(self):
        """Test that missing access_token raises ValueError."""
        if CanvasClient is None:
            self.fail("CanvasClient not implemented")
        with self.assertRaises(ValueError):
            CanvasClient(self.base_url, None)

    @patch('requests.Session.get')
    def test_get_success(self, mock_get):
        """Test a successful GET request."""
        if CanvasClient is None:
            self.fail("CanvasClient not implemented")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}
        mock_get.return_value = mock_response

        result = self.client._get("api/v1/test")
        self.assertEqual(result, {"key": "value"})
        mock_get.assert_called_once()

    @patch('requests.Session.get')
    def test_get_error(self, mock_get):
        """Test a failed GET request."""
        if CanvasClient is None:
            self.fail("CanvasClient not implemented")
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_response

        with self.assertRaises(Exception):
            self.client._get("api/v1/test")

if __name__ == '__main__':
    unittest.main()
