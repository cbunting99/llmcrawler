from bs4 import BeautifulSoup
import logging
import re
from urllib.parse import urlparse, unquote

logger = logging.getLogger(__name__)

class HTMLParser:
    def __init__(self, config):
        self.config = config
        self.SELECTORS = self.config.get('SELECTORS')

    def _get_selectors(self, domain):
        return self.SELECTORS.get(domain, self.SELECTORS['default'])

    def extract_metadata(self, html, url):
        try:
            soup = BeautifulSoup(html, 'html.parser')
            domain = urlparse(url).netloc
            selectors = self._get_selectors(domain)
            
            title = self._extract_text_from_selector(soup, selectors['title'])
            artist = self._extract_text_from_selector(soup, selectors['artist'])
            
            if not artist:
                artist = self._extract_artist_from_url(url)
            
            if not artist:
                artist = self._extract_artist_from_domain(domain)
            
            if title:
                title = self._clean_text(title)
            if artist:
                artist = self._clean_text(artist)
            return title, artist
        except Exception as e:
            logger.error(f"Error extracting metadata from {url}: {str(e)}")
        return None, None

    def extract_lyrics(self, html, url):
        soup = BeautifulSoup(html, 'html.parser')
        try:
            domain = urlparse(url).netloc
            selectors = self._get_selectors(domain)
            lyrics = self._extract_text_from_selector(soup, selectors['lyrics'])
            if not lyrics:
                logger.warning(f"No lyrics found at {url}")
                return None
            return lyrics
        except Exception as e:
            logger.error(f"Error extracting lyrics from {url}: {str(e)}")
            return None

    def _extract_text_from_selector(self, soup, selectors):
        for selector in selectors:
            try:
                if selector.startswith('meta['):
                    element = soup.select_one(selector)
                    if element and element.get('content'):
                        return element['content']
                else:
                    elements = soup.select(selector)
                    if elements:
                        return '\n'.join(element.get_text(strip=True, separator='\n') 
                                       for element in elements)
            except Exception as e:
                logger.debug(f"Error with selector {selector}: {str(e)}")
        return None

    def _clean_text(self, text):
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\[[^\]]*\]', '', text)
        text = re.sub(r'[^\w\s.,!?\'"-]', ' ', text)
        text = ' '.join(text.split())
        return text.strip()