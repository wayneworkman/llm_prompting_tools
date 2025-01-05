# lib/detect_file_type.py (place in ./lib/detect_file_type.py)
import os

TEXT_EXTENSIONS = {
    ".py", ".md", ".txt", ".rst", ".json", ".yaml", ".html", ".css", ".js",
    # ...add more if desired
}

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".exe", ".dll",
    # ...add more if desired
}

def is_binary_file(filename, chunk_size=1024, ascii_threshold=0.10):
    """
    Return True if the given filename is likely binary, False if likely text.

    1) If file extension is in TEXT_EXTENSIONS, return False (text).
    2) If file extension is in BINARY_EXTENSIONS, return True (binary).
    3) Otherwise, read up to 'chunk_size' bytes:
       - If it contains null bytes, declare binary.
       - Else, count how many bytes are outside ASCII range (32..126 plus a few control chars).
         If > ascii_threshold fraction are non-ASCII, treat it as binary.
    4) If none of the above signals binary, return False (text).
    """

    # 1) Known text extension => skip checks
    ext = os.path.splitext(filename)[1].lower()
    if ext in TEXT_EXTENSIONS:
        return False

    # 2) Known binary extension => skip checks
    if ext in BINARY_EXTENSIONS:
        return True

    # 3) Unknown extension => do the ASCII + null byte scan
    try:
        with open(filename, "rb") as f:
            chunk = f.read(chunk_size)
            # Check for null bytes
            if b'\x00' in chunk:
                return True

            # ASCII range 32..126, plus some whitespace controls
            allowed_chars = set(range(32, 127))  # space through tilde
            allowed_chars.update([9, 10, 13])   # tab, newline, carriage return

            total = len(chunk)
            non_ascii = sum(byte not in allowed_chars for byte in chunk)
            if total > 0:
                fraction_non_ascii = non_ascii / total
                if fraction_non_ascii > ascii_threshold:
                    return True

    except FileNotFoundError:
        # If file doesn't exist, do whatever your logic demands; might raise or return True/False
        raise

    # 4) If we got here, it’s likely text
    return False
