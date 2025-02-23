import requests
import random
import logging

logger = logging.getLogger(__name__)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36 Edg/91.0.864.59'
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

class HTTPRequest:
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        self.headers = {'User-Agent': get_random_user_agent()}
        self.session.headers.update(self.headers)

    def get(self, url, render_js=False):
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Request failed for {url}: {e}")
            return None


def rotate_proxy(proxies: List[str]) -> Optional[str]:
    """Randomly select a proxy from the list."""
    if not proxies:
        return None
    return random.choice(proxies)


class ProxyRotator:
    def __init__(self, proxies: List[str]):
        self.proxies = proxies
        self.current_index = -1
        self.failed_proxies = set()

    def get_next_proxy(self) -> Optional[Dict[str, str]]:
        if not self.proxies:
            return None

        attempts = 0
        while attempts < len(self.proxies):
            self.current_index = (self.current_index + 1) % len(self.proxies)
            proxy = self.proxies[self.current_index]
            
            if proxy not in self.failed_proxies:
                return {
                    'http': proxy,
                    'https': proxy
                }
            attempts += 1
        
        return None

    def mark_proxy_failed(self, proxy: str):
        self.failed_proxies.add(proxy)
        msg = f"Marked proxy as failed: {proxy}"
        logger.warning(msg)

def test_proxy(session: requests.Session, proxy: Dict[str, str]) -> bool:
    try:
        response = session.get('http://httpbin.org/ip', proxies=proxy, timeout=5)
        return response.status_code == 200
    except:
        return False

class HTTPRequest:
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        self.headers = {'User-Agent': get_random_user_agent()}
        self.session.headers.update(self.headers)
        self.proxies = config.get('proxies', [])
        self.proxy_rotator = ProxyRotator(self.proxies)
        self.current_proxy = self.proxy_rotator.get_next_proxy()
        if self.current_proxy and test_proxy(self.session, self.current_proxy):
            self.session.proxies = self.current_proxy
            logger.info(f"Using proxy: {self.current_proxy['http']}")
        else:
            logger.warning("No working proxy found, proceeding without proxy")

    def get(self, url, render_js=False):
        max_retries = 3
        retries = 0
        while retries < max_retries:
            try:
                response = self.session.get(url, timeout=10, proxies=self.session.proxies)
                response.raise_for_status()
                return response.text
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed for {url}: {e}")
                if isinstance(e, (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout)):
                    if self.current_proxy:
                        self.proxy_rotator.mark_proxy_failed(self.current_proxy['http'])
                if retries < max_retries - 1:
                    logger.info(f"Retrying {url} with a different proxy ({retries + 1}/{max_retries})")
                    self.current_proxy = self.proxy_rotator.get_next_proxy()
                    if self.current_proxy:
                        self.session.proxies = self.current_proxy
                        logger.info(f"Switched to proxy: {self.current_proxy['http']}")
                    else:
                        logger.warning("No more proxies available. Skipping retry.")
                        break
                else:
                    logger.error(f"Failed to get {url} after {max_retries} retries.")
                    return None
                retries += 1
            except Exception as e:
                logger.error(f"Request failed for {url}: {e}")
                return None
        return None