import unittest
import json
import os
from config_manager import ConfigManager

class TestConfigManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary config file for testing
        self.config_data = {
            "test_key": "test_value",
            "nested_key": {"nested_value": 123}
        }
        self.config_file = "test_config.json"
        with open(self.config_file, 'w') as f:
            json.dump(self.config_data, f)

    def tearDown(self):
        # Remove the temporary config file
        os.remove(self.config_file)

    def test_load_config(self):
        config_manager = ConfigManager(self.config_file)
        self.assertEqual(config_manager.config, self.config_data)

    def test_load_config_file_not_found(self):
        config_manager = ConfigManager("nonexistent_config.json")
        self.assertEqual(config_manager.config, {})

    def test_load_config_invalid_json(self):
        # Create a config file with invalid JSON
        with open(self.config_file, 'w') as f:
            f.write("invalid json")
        config_manager = ConfigManager(self.config_file)
        self.assertEqual(config_manager.config, {})

    def test_get(self):
        config_manager = ConfigManager(self.config_file)
        self.assertEqual(config_manager.get("test_key"), "test_value")
        self.assertEqual(config_manager.get("nested_key"), {"nested_value": 123})
        self.assertEqual(config_manager.get("nonexistent_key"), None)
        self.assertEqual(config_manager.get("nonexistent_key", "default_value"), "default_value")

if __name__ == '__main__':
    unittest.main()