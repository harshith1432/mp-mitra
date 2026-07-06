import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Ensure the project root is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import mpmitra

class TestServiceManager(unittest.TestCase):

    def test_version_loading(self):
        self.assertIsNotNone(mpmitra.VERSION)
        self.assertNotEqual(mpmitra.VERSION, "unknown")

    @patch("psutil.pid_exists")
    def test_is_process_mpmitra_invalid(self, mock_pid_exists):
        mock_pid_exists.return_value = False
        self.assertFalse(mpmitra.is_process_mpmitra(0))
        self.assertFalse(mpmitra.is_process_mpmitra(-100))
        self.assertFalse(mpmitra.is_process_mpmitra(99999))

    @patch("psutil.Process")
    @patch("psutil.pid_exists")
    def test_is_process_mpmitra_valid(self, mock_pid_exists, mock_process):
        mock_pid_exists.return_value = True
        mock_proc = MagicMock()
        mock_proc.cmdline.return_value = ["python", "mpmitra.py", "--server"]
        mock_proc.name.return_value = "python"
        mock_process.return_value = mock_proc

        self.assertTrue(mpmitra.is_process_mpmitra(1234))

        mock_proc.cmdline.return_value = ["node", "index.js"]
        self.assertFalse(mpmitra.is_process_mpmitra(1234))

if __name__ == "__main__":
    unittest.main()
