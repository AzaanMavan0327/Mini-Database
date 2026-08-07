from src.storage.pager import Pager
from src.storage.page import encode_page, decode_page
from src.storage.btree import BTree


class DiskStore:
    """A key-value store that persists data to disk using fixed-size pages.

    Keeps a BTree index mapping key -> page number so reads and writes
    don't need to scan the whole file, and so keys() comes back in sorted
    order for free. The index is rebuilt by scanning the file once when
    the store is opened.
    """

    def __init__(self, file_path):
        self._pager = Pager(file_path)
        self._index = BTree()
        self._free_pages = []
        self._load_index()

    def _load_index(self):
        page_count = self._pager.get_page_count()
        for page_number in range(page_count):
            raw_page = self._pager.read_page(page_number)
            is_occupied, key, _ = decode_page(raw_page)
            if is_occupied:
                self._index.insert(key, page_number)
            else:
                self._free_pages.append(page_number)

    def insert(self, key, value):
        page_data = encode_page(key, value, occupied=True)

        try:
            page_number = self._index.search(key)
        except KeyError:
            if self._free_pages:
                page_number = self._free_pages.pop()
            else:
                page_number = self._pager.get_page_count()

        self._pager.write_page(page_number, page_data)
        self._index.insert(key, page_number)

    def get(self, key):
        page_number = self._index.search(key)
        raw_page = self._pager.read_page(page_number)
        _, _, value = decode_page(raw_page)
        return value

    def delete(self, key):
        page_number = self._index.search(key)
        empty_page_data = encode_page(key, "", occupied=False)
        self._pager.write_page(page_number, empty_page_data)
        self._index.delete(key)
        self._free_pages.append(page_number)

    def keys(self):
        return self._index.keys()

    def close(self):
        self._pager.close()

    def __len__(self):
        return len(self._index)
