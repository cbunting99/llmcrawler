import unittest
import json
import os
from unittest.mock import MagicMock, patch
from persistence import Persistence

class TestPersistence(unittest.TestCase):
    def setUp(self):
        self.config = {"temp_dir": "test_temp"}
        self.persistence = Persistence(self.config)
        self.output_file = "test_output.json"
        # Create temp directory if it doesn't exist
        os.makedirs(self.persistence.temp_dir, exist_ok=True)

    def tearDown(self):
        # Clean up temp directory and output file
        if os.path.exists(self.output_file):
            os.remove(self.output_file)
        if os.path.exists(self.persistence.temp_dir):
            for file in os.listdir(self.persistence.temp_dir):
                os.remove(os.path.join(self.persistence.temp_dir, file))
            os.rmdir(self.persistence.temp_dir)

    def test_load_existing_data_success(self):
        # Create a test output file
        test_data = [{"test": "data"}]
        with open(self.output_file, 'w') as f:
            json.dump(test_data, f)

        loaded_data = self.persistence.load_existing_data(self.output_file)
        self.assertEqual(loaded_data, test_data)

    def test_load_existing_data_file_not_found(self):
        loaded_data = self.persistence.load_existing_data("nonexistent_file.json")
        self.assertEqual(loaded_data, [])

    def test_save_data_success(self):
        test_data = [{"test": "data"}]
        result = self.persistence.save_data(test_data, self.output_file)
        self.assertTrue(result)

        # Verify that the file was created and contains the correct data
        with open(self.output_file, 'r') as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data, test_data)

    def test_save_data_failure(self):
        # Mock os.replace to simulate a failure
        with patch("os.replace", side_effect=Exception("Replace failed")):
            test_data = [{"test": "data"}]
            result = self.persistence.save_data(test_data, self.output_file)
            self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()