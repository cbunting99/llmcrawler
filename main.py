import argparse
import logging
import time
from urllib.parse import urlparse
import sys

from config_manager import ConfigManager
from url_manager import URLManager
from http_request import HTTPRequest
from html_parser import HTMLParser
from data_formatter import DataFormatter
from persistence import Persistence
from error_logger import ErrorLogger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Crawl lyrics from specified URLs.')
    parser.add_argument('urls', nargs='*', help='List of URLs to crawl')
    parser.add_argument('--config', type=str, default='config.json', help='Path to configuration file')
    parser.add_argument('--check-updates', action='store_true', help='Check and update existing URLs')
    parser.add_argument('--rate-limit', type=float, default=15.5, help='Rate limit in seconds between requests')
    parser.add_argument('--proxy-file', type=str, help='Path to the proxy list file')
    args = parser.parse_args()

    if len(args.urls) < 1:
        error_msg = "No URLs provided. Usage: python main.py [--check-updates] URL1 URL2 ..."
        logger.error(error_msg)
        sys.stderr.write(f"ERROR: {error_msg}\n")
        sys.exit(1)

    # Initialize configuration
    config_manager = ConfigManager(args.config)
    config = config_manager.load_config()
    if args.proxy_file:
        config['proxy_file'] = args.proxy_file

    # Initialize URL manager
    url_manager = URLManager(args.urls)

    # Initialize HTTP request handler
    http_request = HTTPRequest(config)

    # Initialize HTML parser
    html_parser = HTMLParser(config)

    # Initialize data formatter
    data_formatter = DataFormatter()

    # Initialize persistence handler
    persistence = Persistence(config)

    # Initialize error logger
    error_logger = ErrorLogger(config)

    # Load existing data
    existing_data = persistence.load_existing_data('song_lyrics.json')

    logger.info("Starting continuous crawling process...")
    logger.info(f"Using rate limit of {args.rate_limit} seconds")

    while True:
        try:
            # Get the next URL to crawl
            url = url_manager.get_next_url()
            if not url:
                logger.info("No more URLs to crawl. Waiting for 24 hours before next check...")
                time.sleep(24 * 3600)
                url_manager = URLManager(args.urls)
                continue

            logger.info(f"Crawling URL: {url}")
            
            # Add rate limiting delay
            time.sleep(args.rate_limit)
            
            # Fetch HTML content
            html_content = http_request.get(url, render_js=True)
            if not html_content:
                error_logger.log_to_db('ERROR', url, "Failed to retrieve HTML content", "HTTP request failed")
                url_manager.mark_crawled(url)
                continue

            # Extract metadata and lyrics
            title, artist = html_parser.extract_metadata(html_content, url)
            lyrics = html_parser.extract_lyrics(html_content, url)

            if not lyrics:
                error_logger.log_to_db('WARNING', url, "No lyrics found", "Content extraction failed")
                url_manager.mark_crawled(url)
                continue

            # Format data
            formatted_data = data_formatter.format_data(title, artist, lyrics, url)
            if not formatted_data:
                error_logger.log_to_db('ERROR', url, "Failed to format data", "Data formatting error")
                url_manager.mark_crawled(url)
                continue

            # Persist data
            existing_data.append(formatted_data)
            persistence.save_data(existing_data, 'song_lyrics.json')
            url_manager.mark_crawled(url)

            logger.info(f"Successfully crawled and saved data for: {url}")

        except KeyboardInterrupt:
            logger.info("Crawling process stopped by user")
            break
        except Exception as e:
            error_msg = f"An unexpected error occurred: {e}"
            logger.error(error_msg)
            error_logger.log_to_db('EXCEPTION', url, error_msg, str(e))
            time.sleep(300)  # Wait 5 minutes before retrying

if __name__ == "__main__":
    main()