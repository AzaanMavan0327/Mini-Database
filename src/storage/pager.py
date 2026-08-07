import os

from src.storage.page import PAGE_SIZE


class Pager:
    """Reads and writes fixed-size pages to a database file on disk."""

    def __init__(self, file_path):
        self.file_path = file_path
        file_exists = os.path.exists(file_path)
        mode = "r+b" if file_exists else "w+b"
        self._file = open(file_path, mode)

    def get_page_count(self):
        self._file.seek(0, os.SEEK_END)
        file_size = self._file.tell()
        return file_size // PAGE_SIZE

    def read_page(self, page_number):
        offset = page_number * PAGE_SIZE
        self._file.seek(offset)
        data = self._file.read(PAGE_SIZE)
        if len(data) < PAGE_SIZE:
            raise IOError(f"Page {page_number} is incomplete or does not exist")
        return data

    def write_page(self, page_number, data):
        if len(data) != PAGE_SIZE:
            raise ValueError(f"Page data must be exactly {PAGE_SIZE} bytes, got {len(data)}")
        offset = page_number * PAGE_SIZE
        self._file.seek(offset)
        self._file.write(data)
        self._file.flush()

    def close(self):
        self._file.close()
