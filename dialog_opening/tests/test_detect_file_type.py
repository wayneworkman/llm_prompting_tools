# tests/test_detect_file_type.py (place in ./tests/test_detect_file_type.py)

import unittest
import os
import tempfile
from lib.detect_file_type import is_binary_file

class TestDetectFileType(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_known_text_extension(self):
        """
        If the file extension is in TEXT_EXTENSIONS, is_binary_file should return False
        without inspecting the content.
        """
        txt_path = os.path.join(self.root, "example.txt")
        with open(txt_path, "w", encoding='utf-8') as f:
            f.write("Some ASCII text here.\n")

        # .txt is in TEXT_EXTENSIONS by default
        self.assertFalse(is_binary_file(txt_path), "A .txt file should be classified as text.")

    def test_known_binary_extension(self):
        """
        If the file extension is in BINARY_EXTENSIONS, is_binary_file should return True
        without reading the content.
        """
        bin_path = os.path.join(self.root, "image.png")
        with open(bin_path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")

        # .png is in BINARY_EXTENSIONS by default
        self.assertTrue(is_binary_file(bin_path), "A .png file should be classified as binary.")

    def test_null_byte_detection(self):
        """
        If the content chunk contains a null byte, is_binary_file should return True.
        """
        unknown_path = os.path.join(self.root, "unknown.dat")
        # Extension .dat not in known text/binary sets, so we do the chunk check
        with open(unknown_path, "wb") as f:
            f.write(b"This is some text...\x00...and a null byte in the middle.")

        self.assertTrue(is_binary_file(unknown_path),
                        "A file with a null byte in the first chunk should be classified as binary.")

    def test_ascii_threshold(self):
        """
        If enough bytes are outside the allowed ASCII set (more than ascii_threshold),
        the file should be classified as binary. We'll artificially create a small chunk
        with half weird bytes.
        """
        unknown_path = os.path.join(self.root, "file.xyz")
        # Extension .xyz not in known sets, triggers chunk-based detection
        data = bytearray([65, 66, 67])  # 'ABC'
        data += bytearray([0xFF, 0xFE, 0xFD])  # 3 weird bytes
        # That's 3 ASCII vs 3 weird => 50% weird
        # Our default ascii_threshold in detect_file_type is 0.10, so 0.50 triggers binary
        with open(unknown_path, "wb") as f:
            f.write(data)

        self.assertTrue(is_binary_file(unknown_path),
                        "If weird bytes fraction > 0.10, it should be classified as binary.")

    def test_below_threshold_considered_text(self):
        """
        If the fraction of non-ASCII bytes is small, the file remains text.
        We'll generate a chunk with <5% weird bytes.
        """
        unknown_path = os.path.join(self.root, "some.abc")
        content = bytearray(b"Hello world!")  # all ASCII
        content += bytearray([0xFF])  # just 1 weird byte
        # That’s ~12 ASCII bytes vs 1 weird => ~8% weird
        with open(unknown_path, "wb") as f:
            f.write(content)

        self.assertFalse(is_binary_file(unknown_path),
                         "If weird bytes fraction <= 0.10, it should be classified as text.")

    def test_file_not_found(self):
        """
        If the file doesn't exist, the function currently raises FileNotFoundError
        (per the code). Test that behavior to confirm.
        """
        missing_path = os.path.join(self.root, "missing.whatever")
        with self.assertRaises(FileNotFoundError):
            is_binary_file(missing_path)

    def test_empty_file(self):
        """
        An empty file should not be considered binary (it's just zero bytes).
        """
        empty_path = os.path.join(self.root, "empty.unknown")
        open(empty_path, "w").close()  # create an empty file
        self.assertFalse(is_binary_file(empty_path),
                         "Empty files are treated as text under the default logic.")

    def test_partial_read(self):
        """
        Confirm that only the first chunk_size bytes are read. We'll create a large file,
        putting weird bytes after the first 1024 bytes so they don't affect classification.
        """
        big_path = os.path.join(self.root, "big.unknown")
        with open(big_path, "wb") as f:
            # Write at least 1200 bytes (for example) of ASCII text, so chunk_size=1024 sees no weird bytes
            f.write(b"ASCII TEXT " * 120)  # ~1320 bytes
            # Now put null/FF bytes after that chunk boundary
            f.write(b"\x00\xFF\x00")

        self.assertFalse(
            is_binary_file(big_path),
            "Weird bytes beyond the first chunk_size should not affect classification by default."
        )

if __name__ == "__main__":
    unittest.main()
