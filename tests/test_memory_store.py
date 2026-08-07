import unittest

from src.storage.memory_store import MemoryStore


class TestMemoryStore(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore()

    def test_insert_and_get(self):
        self.store.insert(1, "hello")
        self.assertEqual(self.store.get(1), "hello")

    def test_insert_overwrites_existing_key(self):
        self.store.insert(1, "hello")
        self.store.insert(1, "goodbye")
        self.assertEqual(self.store.get(1), "goodbye")

    def test_get_missing_key_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.store.get(99)

    def test_delete_removes_key(self):
        self.store.insert(1, "hello")
        self.store.delete(1)
        with self.assertRaises(KeyError):
            self.store.get(1)

    def test_delete_missing_key_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.store.delete(99)

    def test_keys_returns_all_inserted_keys(self):
        self.store.insert(1, "a")
        self.store.insert(2, "b")
        self.assertEqual(sorted(self.store.keys()), [1, 2])

    def test_len_reflects_number_of_entries(self):
        self.store.insert(1, "a")
        self.store.insert(2, "b")
        self.assertEqual(len(self.store), 2)


if __name__ == "__main__":
    unittest.main()
