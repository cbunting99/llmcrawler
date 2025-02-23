# Lyrics Crawler

**Author: Chris Bunting**

**THIS PROJECT IS CURRENTLY NOT WORKING AND HAS NOT BEEN FIXED YET.**

A web application for crawling and extracting song lyrics with real-time progress monitoring and Gemini 1.5 Flash tuning compatibility.

## Overview

This project combines Python web crawling with a Node.js web interface to extract song lyrics from various websites. The extracted data is formatted specifically for use with Gemini 1.5 Flash tuning, including proper metadata extraction and data cleaning.

## Technologies Used

### Backend
- Python 3.x
  - requests (HTTP client for web requests)
  - requests-html (JavaScript rendering)
  - beautifulsoup4 (HTML parsing)
  - sqlite3 (error logging)
  - unittest (testing framework)
  - argparse (command-line argument parsing)
  - pathlib (path manipulation)
- Node.js
  - Express.js (web server)
  - Socket.IO (real-time updates)
  - fs.promises (async file operations)

### Frontend
- HTML5
- CSS3 with CSS Variables
- JavaScript
- Socket.IO client
- Responsive design with mobile support

## Project Structure

The project has been modularized for better maintainability and testability:

### Python Modules
- `main.py` - Main orchestration logic
- `config_manager.py` - Configuration loading and management
- `url_manager.py` - URL handling and validation
- `http_request.py` - HTTP requests and proxy handling
- `html_parser.py` - HTML parsing and content extraction
- `data_formatter.py` - Data formatting for Gemini
- `persistence.py` - Data persistence operations
- `error_logger.py` - SQLite-based error logging

### Test Files
- `test_config_manager.py`
- `test_url_manager.py`
- `test_http_request.py`
- `test_html_parser.py`
- `test_data_formatter.py`
- `test_persistence.py`
- `test_error_logger.py`

## Features

### Core Features
- Site-specific selectors for popular lyrics websites
- Smart metadata extraction with multiple fallbacks
- Robust error logging with SQLite database
- Network timeout handling and proxy support with proxy rotation and retry logic
- Configurable rate limiting (both CLI and Web UI)
- Domain restriction for security
- Data cleaning and formatting
- Gemini 1.5 Flash compatibility
- Continuous crawling with 24-hour update checks

### Web Interface
- Dark mode support
- Multiple URL input methods
- Real-time URL validation
- Progress tracking
- CSV download functionality
- Responsive design
- Detailed error logging
- Progress persistence
- Manual rate limit input
- Proxy list file path input

## Installation

1. **Prerequisites**
   ```bash
   python --version  # Should be Python 3.x
   node --version   # Should be Node.js 12.x or higher
   ```

2. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

3. **Install Python Dependencies**
   ```bash
   pip install requests beautifulsoup4 lxml[html_clean]
   ```

4. **Install Node.js Dependencies**
   ```bash
   npm install
   ```

## Configuration

1. **Edit config.json**
   ```json
   {
     "SELECTORS": {
       "genius.com": {
         "title": ["h1.song-title"],
         "artist": ["h2.artist-name"],
         "lyrics": ["div.lyrics"]
       },
       "default": {
         "title": ["title"],
         "artist": ["meta[name=\"artist\"]"],
         "lyrics": ["div.lyrics"]
       }
     },
     "temp_dir": "temp"
   }
   ```

2. **Rate Limiting**
   - **Command Line:**
     ```bash
     python main.py --rate-limit 5.0 URL1 URL2  # 5 seconds between requests
     ```
   - **Web Interface:**
     - Enter the desired rate limit in the "Rate Limit" field (in seconds, minimum 1.0)

3.  **Proxy Support**
    - **Command Line:**
      ```bash
      python main.py --proxy-file proxies.txt URL1 URL2 # Use proxies from proxies.txt
      ```
    - **Web Interface:**
      - Enter the path to the proxy list file in the "Proxy List File Path" field.

## Usage

1. **Command Line Interface**
   ```bash
   # Basic usage
   python main.py URL1 URL2 URL3

   # With custom config file
   python main.py --config my_config.json URL1 URL2

   # With rate limit
   python main.py --rate-limit 3.0 URL1 URL2

   # With proxy file
   python main.py --proxy-file proxies.txt URL1 URL2

   # Check for updates
   python main.py --check-updates URL1 URL2
   ```

2. **Web Interface**
   ```bash
   # Start the server
   npm start

   # Access at http://localhost:3000
   ```
   - Enter URLs and rate limit in the web interface
   - Enter the proxy file path (optional)
   - Click "Start Crawling"

## Error Handling

- All errors are logged to `crawler_errors.db` SQLite database
- Error categories:
  - WARNING: Non-critical issues
  - ERROR: Critical failures
  - EXCEPTION: Unexpected errors
- Real-time error monitoring in web interface
- Automatic retry with cooldown after failures

## Development

1. **Running Tests**
   ```bash
   # Run all tests
   python -m unittest discover

   # Run specific test
   python -m unittest test_config_manager.py
   ```

2. **Adding New Sites**
   1. Update `config.json` with new selectors
   2. Test with sample URLs
   3. Add any site-specific parsing logic to `html_parser.py`

## License

This project is licensed under the MIT License. See the LICENSE file for details.
This project is unlicensed and proprietary.