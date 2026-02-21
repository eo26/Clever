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

    @patch('requests.Session.get')
    def test_get_all_pagination(self, mock_get):
        """Test the _get_all method with pagination."""
        if CanvasClient is None:
            self.fail("CanvasClient not implemented")
        
        # Setup mock responses for two pages
        mock_response_1 = MagicMock()
        mock_response_1.status_code = 200
        mock_response_1.json.return_value = [{"id": 1}, {"id": 2}]
        mock_response_1.links = {'next': {'url': 'https://example.com/api/v1/test?page=2'}}

        mock_response_2 = MagicMock()
        mock_response_2.status_code = 200
        mock_response_2.json.return_value = [{"id": 3}]
        mock_response_2.links = {}

        mock_get.side_effect = [mock_response_1, mock_response_2]

        result = self.client._get_all("api/v1/test")
        self.assertEqual(result, [{"id": 1}, {"id": 2}, {"id": 3}])
        self.assertEqual(mock_get.call_count, 2)

    @patch('requests.Session.get')
    def test_get_user_self(self, mock_get):
        """Test get_user_self method."""
        if CanvasClient is None:
            self.fail("CanvasClient not implemented")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 123, "name": "Test User"}
        mock_get.return_value = mock_response

        result = self.client.get_user_self()
        self.assertEqual(result, {"id": 123, "name": "Test User"})
        mock_get.assert_called_with("https://example.com/api/v1/users/self", params=None)

    @patch('requests.Session.get')
    def test_get_courses(self, mock_get):
        """Test get_courses method."""
        if CanvasClient is None:
            self.fail("CanvasClient not implemented")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 1, "name": "Course 1"}]
        mock_response.links = {}
        mock_get.return_value = mock_response

        result = self.client.get_courses()
        self.assertEqual(result, [{"id": 1, "name": "Course 1"}])
        mock_get.assert_called_with("https://example.com/api/v1/courses", params=None)

    @patch('requests.Session.get')
    def test_get_enrollments(self, mock_get):
        """Test get_enrollments method."""
        if CanvasClient is None:
            self.fail("CanvasClient not implemented")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 1, "type": "StudentEnrollment"}]
        mock_response.links = {}
        mock_get.return_value = mock_response

        result = self.client.get_enrollments(123)
        self.assertEqual(result, [{"id": 1, "type": "StudentEnrollment"}])
        mock_get.assert_called_with("https://example.com/api/v1/courses/123/enrollments", params=None)

    @patch('requests.Session.get')
    def test_get_assignments(self, mock_get):
        """Test get_assignments method."""
        if CanvasClient is None:
            self.fail("CanvasClient not implemented")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 1, "name": "Assignment 1"}]
        mock_response.links = {}
        mock_get.return_value = mock_response

        result = self.client.get_assignments(123)
        self.assertEqual(result, [{"id": 1, "name": "Assignment 1"}])
        mock_get.assert_called_with("https://example.com/api/v1/courses/123/assignments", params=None)

if __name__ == '__main__':
    unittest.main()
