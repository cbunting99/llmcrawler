import unittest
from unittest.mock import MagicMock
from bs4 import BeautifulSoup
from html_parser import HTMLParser

class TestHTMLParser(unittest.TestCase):
    def setUp(self):
        self.config = {
            'SELECTORS': {
                'example.com': {
                    'title': ['h1'],
                    'artist': ['.artist'],
                    'lyrics': ['div.lyrics']
                },
                'default': {
                    'title': ['title'],
                    'artist': ['meta[name="artist"]'],
                    'lyrics': ['div#lyrics']
                }
            }
        }
        self.html_parser = HTMLParser(self.config)

    def test_extract_metadata(self):
        html = """
        <html>
        <head>
            <title>Test Title</title>
            <meta name="artist" content="Test Artist">
        </head>
        <body>
            <h1>Main Title</h1>
            <div class="artist">Artist Name</div>
            <div id="lyrics">Test lyrics</div>
        </body>
        </html>
        """
        title, artist = self.html_parser.extract_metadata(html, "http://example.com")
        self.assertEqual(title, "Main Title")
        self.assertEqual(artist, "Artist Name")

        title, artist = self.html_parser.extract_metadata(html, "http://another-example.com")
        self.assertEqual(title, "Test Title")
        self.assertEqual(artist, "Test Artist")

    def test_extract_lyrics(self):
        html = """
        <html>
        <head><title>Test</title></head>
        <body><div class="lyrics">Test lyrics</div></body>
        </html>
        """
        lyrics = self.html_parser.extract_lyrics(html, "http://example.com")
        self.assertEqual(lyrics, "Test lyrics")
        
        html = """
        <html>
        <head><title>Test</title></head>
        <body><div id="lyrics">Test lyrics</div></body>
        </html>
        """
        lyrics = self.html_parser.extract_lyrics(html, "http://another-example.com")
        self.assertEqual(lyrics, "Test lyrics")

if __name__ == '__main__':
    unittest.main()