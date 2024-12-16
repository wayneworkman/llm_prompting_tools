# tests/test_file_info.py
import unittest
from unittest.mock import patch, MagicMock
from lib.file_info import human_readable_size, format_file_line
from stat import S_IFREG, S_IRUSR, S_IWUSR

class TestFileInfo(unittest.TestCase):
    def test_human_readable_size(self):
        self.assertEqual(human_readable_size(500), "500B")
        self.assertEqual(human_readable_size(1024), "1.0K")
        self.assertEqual(human_readable_size(1500), "1.5K")
        self.assertEqual(human_readable_size(1024**2), "1.0M")
        self.assertEqual(human_readable_size(1024**3), "1.0G")

    @patch('pwd.getpwuid')
    @patch('grp.getgrgid')
    def test_format_file_line(self, mock_grp, mock_pwd):
        mock_pwd.return_value.pw_name = 'owner'
        mock_grp.return_value.gr_name = 'group'

        mock_st = MagicMock()
        mock_st.st_mode = S_IFREG | S_IRUSR | S_IWUSR
        mock_st.st_nlink = 1
        mock_st.st_uid = 1000
        mock_st.st_gid = 1000
        mock_st.st_size = 1234
        mock_st.st_mtime = 1609459200  # 2021-01-01 00:00:00

        line = format_file_line("/path/to/file.txt", mock_st)
        # Example output: "-rw------- 1 owner group 1.2K Jan 01 00:00 file.txt"
        self.assertIn("owner", line)
        self.assertIn("group", line)
        self.assertIn("1.2K", line)
        self.assertIn("file.txt", line)

if __name__ == '__main__':
    unittest.main()
