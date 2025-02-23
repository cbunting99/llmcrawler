import unittest
from unittest.mock import patch, MagicMock
from http_request import HTTPRequest, get_random_user_agent
import requests

class TestHTTPRequest(unittest.TestCase):
    @patch('http_request.requests.Session')
    def setUp(self, MockSession):
        self.mock_session = MockSession.return_value
        self.config = {}
        self.http_request = HTTPRequest(self.config)
        self.http_request.session = self.mock_session

    def test_get_success(self):
        self.mock_session.get.return_value.raise_for_status = MagicMock()
        self.mock_session.get.return_value.text = "Test content"
        result = self.http_request.get("http://example.com")
        self.assertEqual(result, "Test content")

    def test_get_failure(self):
        self.mock_session.get.side_effect = Exception("Request failed")
        result = self.http_request.get("http://example.com")
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()