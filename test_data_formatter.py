import unittest
from data_formatter import DataFormatter

class TestDataFormatter(unittest.TestCase):
    def setUp(self):
        self.data_formatter = DataFormatter()

    def test_format_data(self):
        title = "Test Title"
        artist = "Test Artist"
        lyrics = "Test lyrics"
        url = "http://example.com"

        formatted_data = self.data_formatter.format_data(title, artist, lyrics, url)
        self.assertEqual(formatted_data['title'], title)
        self.assertEqual(formatted_data['artist'], artist)
        self.assertEqual(formatted_data['prompt'], f"Write lyrics for a song titled '{title}' in the style of {artist}.")
        self.assertEqual(formatted_data['completion'], lyrics)
        self.assertEqual(formatted_data['url'], url)
        self.assertIn('last_crawled', formatted_data)

    def test_format_data_missing_artist(self):
        title = "Test Title"
        artist = None
        lyrics = "Test lyrics"
        url = "http://example.com"

        formatted_data = self.data_formatter.format_data(title, artist, lyrics, url)
        self.assertEqual(formatted_data['title'], title)
        self.assertEqual(formatted_data['artist'], 'Unknown Artist')
        self.assertEqual(formatted_data['prompt'], f"Write lyrics for a song titled '{title}'." )
        self.assertEqual(formatted_data['completion'], lyrics)
        self.assertEqual(formatted_data['url'], url)
        self.assertIn('last_crawled', formatted_data)

    def test_format_data_missing_title(self):
        title = None
        artist = "Test Artist"
        lyrics = "Test lyrics"
        url = "http://example.com"

        formatted_data = self.data_formatter.format_data(title, artist, lyrics, url)
        self.assertEqual(formatted_data['title'], 'Unknown Title')
        self.assertEqual(formatted_data['artist'], artist)
        self.assertEqual(formatted_data['prompt'], f"Write song lyrics in the style of {artist}." )
        self.assertEqual(formatted_data['completion'], lyrics)
        self.assertEqual(formatted_data['url'], url)
        self.assertIn('last_crawled', formatted_data)

if __name__ == '__main__':
    unittest.main()