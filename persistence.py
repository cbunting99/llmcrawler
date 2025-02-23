import json
import logging
import os

logger = logging.getLogger(__name__)

class Persistence:
    def __init__(self, config):
        self.config = config
        self.temp_dir = self.config.get('temp_dir')
        if not self.temp_dir:
            self.temp_dir = 'temp'
            os.makedirs(self.temp_dir, exist_ok=True)

    def load_existing_data(self, output_file):
        try:
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load existing data: {e}")
        return []

    def save_data(self, data, output_file):
        temp_file = os.path.join(self.temp_dir, 'temp_lyrics.json')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(temp_file, output_file)
            logger.info(f"Successfully saved data to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save data to {output_file}: {e}")
            return False
        return True