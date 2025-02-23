import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class URLManager:
    def __init__(self, urls):
        self.urls = urls
        self.allowed_domains = self._extract_domains(urls)
        self.crawled_urls = set()

    def _extract_domains(self, urls):
        domains = set()
        for url in urls:
            try:
                domain = urlparse(url).netloc
                if domain:
                    domains.add(domain)
            except Exception as e:
                logger.error(f"Invalid URL format: {url}")
        return domains

    def is_allowed_domain(self, url):
        try:
            domain = urlparse(url).netloc
            return domain in self.allowed_domains
        except Exception:
            return False

    def get_next_url(self):
        for url in self.urls:
            if url not in self.crawled_urls and self.is_allowed_domain(url):
                return url
        return None

    def mark_crawled(self, url):
        self.crawled_urls.add(url)