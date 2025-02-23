import requests
from bs4 import BeautifulSoup
from requests_html import HTMLSession
from datetime import datetime, timedelta
import random
import csv
import logging
import sqlite3
from pathlib import Path
import sys
import json
import time
from urllib.parse import urlparse, unquote
from typing import List, Dict, Set, Optional, Tuple
import socket
import os
from functools import wraps
import tempfile
import re
import main
import http_request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_error_db():
    """Initialize the SQLite database for error logging."""
    db_path = Path('crawler_errors.db')
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    
    # Create table for error logging if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS error_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            error_type TEXT NOT NULL,
            url TEXT,
            message TEXT NOT NULL,
            details TEXT
        )
    ''')
    conn.commit()
    conn.close()
    return db_path

def log_to_db(error_type: str, url: str, message: str, details: str = None):
    """Log an error to the SQLite database."""
    try:
        conn = sqlite3.connect('crawler_errors.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO error_logs (timestamp, error_type, url, message, details)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            error_type,
            url,
            message,
            details
        ))
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to log to database: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

class LyricsCrawler:
    SELECTORS = {
        'genius.com': {
            'title': [
                'h1[class*="SongHeader__Title"]',
                'h1.header_with_cover_art-primary_info-title',
                'meta[property="og:title"]',
                'title'
            ],
            'artist': [
                'a[class*="SongHeader__Artist"]',
                'a.header_with_cover_art-primary_info-primary_artist',
                'meta[property="og:site_name"]',
                'meta[name="twitter:creator"]',
                'span[class*="SongHeader__Artist"]',
                'a[href*="/artists/"]'
            ],
            'lyrics': [
                'div[class*="Lyrics__Container"]',
                'div[class*="lyrics"]',
                '.song_body-lyrics'
            ]
        },
        'default': {
            'title': [
                'h1.song-title',
                'meta[property="og:title"]',
                '.song-header h1',
                'title',
                'meta[name="twitter:title"]'
            ],
            'artist': [
                'h2.artist-name',
                'meta[property="og:artist"]',
                '.artist-header h2',
                '.artist-name',
                'meta[name="artist"]',
                'meta[name="twitter:creator"]',
                'a[href*="/artist/"]',
                'span.artist',
                '.author'
            ],
            'lyrics': [
                'div.lyrics',
                '.lyric-content',
                '.song-lyrics',
                'div[class*="lyrics"]',
                '.text-lyrics'
            ]
        }
    }

    def __init__(self, urls: List[str]):  # Increased default rate limit
        self.config_manager = main.config_manager
        self.config = self.config_manager.config
        self.rate_limit = self.config.get('rate_limit', 5.0)  # Get rate limit from config
        self.urls = urls
        self.last_request_time = 0.0
        self.allowed_domains = self._extract_domains(urls)
        self.temp_dir = tempfile.mkdtemp()
        self.http_request = http_request.HTTPRequest(self.config)
        
        try:
            self.js_session = HTMLSession()
            self.js_session.headers.update(self.http_request.headers)
            if self.http_request.current_proxy:
                self.js_session.proxies = self.http_request.session.proxies
        except Exception as e:
            logger.warning(f"Failed to initialize JavaScript session: {e}")
            self.js_session = None
        
        self.stats = {
            'total_urls': len(urls),
            'urls_crawled': 0,
            'errors': 0,
            'metadata_missing': 0,
            'retries': 0,
            'js_rendered': 0,
            'proxy_failures': 0,
            'urls_updated': 0
        }

    def cleanup(self):
        """Clean up resources."""
        try:
            if hasattr(self, 'js_session') and self.js_session:
                self.js_session.close()
        except Exception as e:
            logger.debug(f"Error closing JavaScript session: {e}")
        
        try:
            if os.path.exists(self.temp_dir):
                for file in os.listdir(self.temp_dir):
                    os.remove(os.path.join(self.temp_dir, file))
                os.rmdir(self.temp_dir)
        except Exception as e:
            logger.debug(f"Error cleaning up temporary directory: {e}")
        
        self.http_request.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def _update_request_settings(self):
        """Update request settings with new proxy and User-Agent."""
        # Rotate User-Agent
        new_user_agent = self.http_request.get_random_user_agent()
        self.http_request.headers['User-Agent'] = new_user_agent
        self.http_request.session.headers.update(self.http_request.headers)
        
        if self.js_session:
            self.js_session.headers.update(self.http_request.headers)

    def _rate_limit(self):
        """Implement rate limiting between requests."""
        now = time.time()
        time_since_last = now - self.last_request_time
        if time_since_last < self.rate_limit:
            time.sleep(self.rate_limit - time_since_last)
        self.last_request_time = time.time()

    def _render_javascript(self, url: str) -> Optional[str]:
        """Render JavaScript content for a given URL."""
        if not self.js_session:
            return None
            
        try:
            response = self.js_session.get(url, timeout=30)
            response.raise_for_status()
            response.html.render(timeout=30)
            self.stats['js_rendered'] += 1
            return response.html.html
        except Exception as e:
            logger.warning(f"Failed to render JavaScript content for {url}: {e}")
            return None

    def _extract_domains(self, urls: List[str]) -> Set[str]:
        domains = set()
        for url in urls:
            try:
                domain = urlparse(url).netloc
                if domain:
                    domains.add(domain)
            except Exception as e:
                logger.error(f"Invalid URL format: {url}")
        return domains

    def _is_allowed_domain(self, url: str) -> bool:
        try:
            domain = urlparse(url).netloc
            return domain in self.allowed_domains
        except Exception:
            return False

    def _get_selectors(self, domain: str) -> Dict[str, List[str]]:
        return self.SELECTORS.get(domain, self.SELECTORS['default'])

    def _extract_metadata(self, url: str, soup: BeautifulSoup) -> Tuple[Optional[str], Optional[str]]:
        title = None
        artist = None
        try:
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
        except Exception as e:
            logger.error(f"Error extracting metadata from {url}: {str(e)}")
        
        return title, artist

    def _extract_text_from_selector(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
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

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\[[^\]]*\]', '', text)
        text = re.sub(r'[^\w\s.,!?\'"-]', ' ', text)
        text = ' '.join(text.split())
        return text.strip()

    
    def extract_lyrics(self, url: str) -> Dict[str, str]:
        """Extract lyrics and metadata from a given URL."""
        if not self._is_allowed_domain(url):
            error_msg = f"Domain not in allowed list: {urlparse(url).netloc}"
            logger.error(error_msg)
            log_to_db('ERROR', url, error_msg, 'Domain validation failed')
            sys.stderr.write(f"ERROR: {error_msg}\n")
            return None

        try:
            self._rate_limit()
            
            # Update request settings before making request
            self._update_request_settings()
            print(json.dumps({'status': 'crawling', 'url': url}), flush=True)
            
            # Try JavaScript rendering first
            html_content = self._render_javascript(url)
            if html_content:
                soup = BeautifulSoup(html_content, 'html.parser')
                logger.info(f"Using JavaScript-rendered content for {url}")
            else:
                # Fall back to regular requests if JS rendering fails
                logger.info(f"Falling back to regular scraping for {url}")
                html_content = self.http_request.get(url)
                if html_content is None:
                    return None
                soup = BeautifulSoup(html_content, 'html.parser')
            
            # Test if content was actually loaded
            if not soup.find('body'):
                error_msg = f"No content found after scraping {url}"
                logger.error(error_msg)
                return None
            
            domain = urlparse(url).netloc
            selectors = self._get_selectors(domain)
            title, artist = self._extract_metadata(url, soup)
            
            if not title or not artist:
                self.stats['metadata_missing'] += 1
                missing = []
                if not title:
                    missing.append('title')
                if not artist:
                    missing.append('artist')
                warning_msg = f"Missing metadata ({', '.join(missing)}) for {url}"
                sys.stderr.write(f"WARNING: {warning_msg}\n")
            
            try:
                lyrics = self._extract_text_from_selector(soup, selectors['lyrics'])
                if not lyrics:
                    error_msg = f"No lyrics found at {url}"
                    logger.warning(error_msg)
                    sys.stderr.write(f"WARNING: {error_msg}\n")
                    return None
                
            except Exception as e:
                error_msg = f"HTML parsing error at {url}: {str(e)}"
                logger.error(error_msg)
                log_to_db('ERROR', url, error_msg, f"Parser error: {str(e)}")
                sys.stderr.write(f"ERROR: {error_msg}\n")
                self.stats['errors'] += 1
                self.print_status(error_msg)
                return None

            return {
                'title': title or 'Unknown Title',
                'artist': artist or 'Unknown Artist',
                'prompt': self._format_prompt(title, artist),
                'completion': lyrics,
                'url': url,
                'last_crawled': datetime.now().isoformat()
            }

        except Exception as e:
            error_msg = f"Unexpected error crawling {url}: {str(e)}"
            logger.error(error_msg)
            self.stats['errors'] += 1
            self.print_status(error_msg)
            return None

    def _load_existing_data(self, output_file: str) -> List[Dict[str, str]]:
        """Load existing data from JSON file if it exists."""
        try:
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load existing data: {e}")
        return []

    def _needs_update(self, data: Dict[str, str]) -> bool:
        """Check if the URL needs to be updated (older than 24 hours)."""
        if 'last_crawled' not in data:
            return True

        try:
            last_crawled = datetime.fromisoformat(data['last_crawled'])
            return datetime.now() - last_crawled > timedelta(hours=24)
        except (ValueError, TypeError):
            return True

    def check_and_update(self, output_file: str):
        """Check for URLs that need updating and update them."""
        existing_data = self._load_existing_data(output_file)
        updated = False

        logger.info("Checking for URLs that need updating...")
        for url in self.urls:
            domain = urlparse(url).netloc
            logger.info(f"Checking URL from {domain}: {url}")
            
            # Find existing data for this URL
            existing_entry = next((item for item in existing_data if item.get('url') == url), None)
            
            if not existing_entry or self._needs_update(existing_entry):
                logger.info(f"Updating {url}")
                result = self.extract_lyrics(url)
                if result:
                    if not existing_entry:
                        existing_data.append(result)
                    else:
                        existing_entry.update(result)
                    updated = True
                    self.stats['urls_updated'] += 1
                    self.print_status()
                else:
                    logger.warning(f"Failed to update {url}")
            else:
                logger.info(f"Skipping {url} - last crawled: {existing_entry['last_crawled']}")

        if updated:
            temp_file = os.path.join(self.temp_dir, 'temp_lyrics.json')
            try:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, indent=2, ensure_ascii=False)
                os.replace(temp_file, output_file)
                logger.info("Successfully updated lyrics database")
            except Exception as e:
                error_msg = f"Failed to save updated JSON file: {str(e)}"
                logger.error(f"{error_msg} for file: {output_file}")
                raise
        else:
            logger.info("No updates needed")

    def save_to_json(self, output_file: str):
        """Save extracted lyrics to a JSON file."""
        temp_file = os.path.join(self.temp_dir, 'temp_lyrics.json')
        lyrics_data = self._load_existing_data(output_file)
        
        try:
            for url in self.urls:
                domain = urlparse(url).netloc
                logger.info(f"Processing URL from {domain}: {url}")
                
                result = self.extract_lyrics(url)
                if result:
                    result['url'] = url
                    result['last_crawled'] = datetime.now().isoformat()
                    lyrics_data.append(result)
                    self.stats['urls_crawled'] += 1
                    self.print_status()
                else:
                    logger.warning(f"Skipping URL from {domain} due to extraction error: {url}")
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(lyrics_data, f, indent=2, ensure_ascii=False)
            os.replace(temp_file, output_file)
            
        except Exception as e:
            error_msg = f"Failed to save JSON file: {str(e)}"
            logger.error(f"{error_msg} for file: {output_file}")
            log_to_db('ERROR', None, error_msg, f"File operation error: {output_file}, Details: {str(e)}")
            raise
        finally:
            self.cleanup()

import argparse

def main():
    parser = argparse.ArgumentParser(description='Crawl lyrics from specified URLs.')
    parser.add_argument('urls', nargs='*', help='List of URLs to crawl')
    parser.add_argument('--rate-limit', type=float, default=5.0, help='Rate limit in seconds between requests')
    parser.add_argument('--check-updates', action='store_true', help='Check and update existing URLs')
    args = parser.parse_args()

    if not args.urls:
        error_msg = "No URLs provided. Usage: python crawl_lyrics.py [--check-updates] URL1 URL2 ..."
        logger.error(error_msg)
        log_to_db('ERROR', None, error_msg, 'Command line argument validation')
        sys.stderr.write(f"ERROR: {error_msg}\n")
        sys.exit(1)
    
    # Initialize error logging database
    init_error_db()
    
    logger.info("Starting continuous crawling process...")
    while True:
        try:
            with LyricsCrawler(args.urls) as crawler:
                if args.check_updates:
                    crawler.check_and_update('song_lyrics.json')
                    logger.info("Update check complete")
                else:
                    crawler.save_to_json('song_lyrics.json')
                    logger.info("Successfully saved lyrics to song_lyrics.json")
                    logger.info("To check for updates later, run: python crawl_lyrics.py --check-updates URL1 URL2 ...")

        # Wait for 24 hours before next iteration
            logger.info("Waiting 24 hours before next check...")
            time.sleep(24 * 3600)  # 24 hours in seconds

        except KeyboardInterrupt:
            logger.info("Crawling process stopped by user")
            break

        except Exception as e:
            error_msg = f"Failed to complete crawling process: {str(e)}"
            logger.error(error_msg)
            log_to_db('EXCEPTION', None, error_msg, str(e))
            sys.stderr.write(f"ERROR: {error_msg}\n")

        # Wait for 5 minutes before retrying after an error
        logger.info("Waiting 5 minutes before retrying...")
        time.sleep(300)  # 5 minutes in seconds

import main

if __name__ == "__main__":
    main.main()