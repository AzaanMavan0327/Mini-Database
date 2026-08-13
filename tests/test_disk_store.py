import os
import random
import tempfile
import unittest

from src.storage.disk_store import DiskStore


class TestDiskStore(unittest.TestCase):
    def setUp(self):
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.db_path = temp_file.name
        temp_file.close()
        os.remove(self.db_path)
        self.store = DiskStore(self.db_path)

    def tearDown(self):
        self.store.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

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

    def test_data_survives_reopening_the_store(self):
        self.store.insert(1, "hello")
        self.store.insert(2, "world")
        self.store.close()

        reopened_store = DiskStore(self.db_path)
        self.assertEqual(reopened_store.get(1), "hello")
        self.assertEqual(reopened_store.get(2), "world")
        reopened_store.close()

    def test_deleted_key_stays_deleted_after_reopening(self):
        self.store.insert(1, "hello")
        self.store.delete(1)
        self.store.close()

        reopened_store = DiskStore(self.db_path)
        with self.assertRaises(KeyError):
            reopened_store.get(1)
        reopened_store.close()

    def test_free_page_is_reused_after_delete(self):
        self.store.insert(1, "hello")
        self.store.delete(1)
        self.store.insert(2, "world")

        self.assertEqual(self.store.get(2), "world")
        self.assertEqual(len(self.store), 1)

    def test_keys_returns_all_inserted_keys_in_sorted_order(self):
        self.store.insert(2, "b")
        self.store.insert(1, "a")
        self.store.insert(3, "c")
        self.assertEqual(self.store.keys(), [1, 2, 3])

    def test_handles_a_larger_number_of_rows_correctly(self):
        # Catches bugs that only show up once the B-tree index has
        # split and merged several times, not just with a handful of rows.
        keys_in_insert_order = list(range(200))
        random.shuffle(keys_in_insert_order)

        for key in keys_in_insert_order:
            self.store.insert(key, f"value-{key}")

        keys_to_delete = keys_in_insert_order[:50]
        for key in keys_to_delete:
            self.store.delete(key)

        expected_keys = sorted(set(range(200)) - set(keys_to_delete))
        self.assertEqual(self.store.keys(), expected_keys)
        for key in expected_keys:
            self.assertEqual(self.store.get(key), f"value-{key}")


if __name__ == "__main__":
    unittest.main()
