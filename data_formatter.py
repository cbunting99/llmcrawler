import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DataFormatter:
    def __init__(self):
        pass

    def format_data(self, title, artist, lyrics, url):
        try:
            prompt = self._format_prompt(title, artist)
            return {
                'title': title or 'Unknown Title',
                'artist': artist or 'Unknown Artist',
                'prompt': prompt,
                'completion': lyrics,
                'url': url,
                'last_crawled': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error formatting data: {e}")
            return None

    def _format_prompt(self, title, artist):
        if title and artist:
            return f"Write lyrics for a song titled '{title}' in the style of {artist}."
        elif title:
            return f"Write lyrics for a song titled '{title}'."
        elif artist:
            return f"Write song lyrics in the style of {artist}."
        else:
            return "Write song lyrics in a similar style to this example:"