import json
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_file}")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in configuration file: {self.config_file}")
            return {}

    def get(self, key, default=None):
        return self.config.get(key, default)

    def load_proxies_from_file(self, proxy_file_path):
        """Load proxies from a text file, one proxy per line."""
        proxies = []
        try:
            with open(proxy_file_path, 'r') as f:
                proxies = [line.strip() for line in f if line.strip()]
            logger.info(f"Loaded {len(proxies)} proxies from {proxy_file_path}")
        except FileNotFoundError:
            logger.error(f"Proxy file not found: {proxy_file_path}")
            return []
        except Exception as e:
            logger.error(f"Failed to load proxies from {proxy_file_path}: {str(e)}")
            return []
        return proxies

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                # Load proxies if proxy_file is specified
                if 'proxy_file' in config:
                    config['proxies'] = self.load_proxies_from_file(config['proxy_file'])
                return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_file}")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in configuration file: {self.config_file}")
            return {}