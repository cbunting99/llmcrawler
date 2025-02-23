import unittest
from url_manager import URLManager

class TestURLManager(unittest.TestCase):
    def setUp(self):
        self.urls = [
            "http://example.com/lyrics1",
            "https://example.com/lyrics2",
            "invalid-url"
        ]
        self.url_manager = URLManager(self.urls)

    def test_extract_domains(self):
        expected_domains = {"example.com"}
        self.assertEqual(self.url_manager.allowed_domains, expected_domains)

    def test_is_allowed_domain(self):
        self.assertTrue(self.url_manager.is_allowed_domain("http://example.com/lyrics1"))
        self.assertFalse(self.url_manager.is_allowed_domain("http://invalid.com/lyrics"))
        self.assertFalse(self.url_manager.is_allowed_domain("invalid-url"))

    def test_get_next_url(self):
        next_url = self.url_manager.get_next_url()
        self.assertEqual(next_url, "http://example.com/lyrics1")
        self.url_manager.mark_crawled("http://example.com/lyrics1")
        next_url = self.url_manager.get_next_url()
        self.assertEqual(next_url, "https://example.com/lyrics2")
        self.url_manager.mark_crawled("https://example.com/lyrics2")
        next_url = self.url_manager.get_next_url()
        self.assertIsNone(next_url)

    def test_mark_crawled(self):
        self.url_manager.mark_crawled("http://example.com/lyrics1")
        self.assertIn("http://example.com/lyrics1", self.url_manager.crawled_urls)

if __name__ == '__main__':
    unittest.main()