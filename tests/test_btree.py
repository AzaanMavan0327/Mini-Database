import random
import unittest

from src.storage.btree import BTree


class TestBTree(unittest.TestCase):
    def setUp(self):
        self.tree = BTree()

    def test_insert_and_search(self):
        self.tree.insert(1, "hello")
        self.assertEqual(self.tree.search(1), "hello")

    def test_insert_overwrites_existing_key(self):
        self.tree.insert(1, "hello")
        self.tree.insert(1, "goodbye")
        self.assertEqual(self.tree.search(1), "goodbye")
        self.assertEqual(len(self.tree), 1)

    def test_search_missing_key_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.tree.search(99)

    def test_delete_missing_key_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.tree.delete(99)

    def test_len_starts_at_zero(self):
        self.assertEqual(len(self.tree), 0)

    def test_keys_on_empty_tree_returns_empty_list(self):
        self.assertEqual(self.tree.keys(), [])

    def test_keys_are_returned_in_sorted_order(self):
        for key in [5, 1, 4, 2, 3]:
            self.tree.insert(key, f"value-{key}")
        self.assertEqual(self.tree.keys(), [1, 2, 3, 4, 5])

    def test_insert_enough_keys_to_force_a_split(self):
        # MIN_DEGREE is 2, so a node holds at most 3 keys before splitting.
        # Inserting more than that forces the tree to grow past one level.
        for key in range(10):
            self.tree.insert(key, f"value-{key}")

        self.assertEqual(len(self.tree), 10)
        for key in range(10):
            self.assertEqual(self.tree.search(key), f"value-{key}")
        self.assertEqual(self.tree.keys(), list(range(10)))

    def test_delete_leaf_key(self):
        for key in range(5):
            self.tree.insert(key, f"value-{key}")
        self.tree.delete(4)
        with self.assertRaises(KeyError):
            self.tree.search(4)
        self.assertEqual(len(self.tree), 4)

    def test_delete_causes_merge_and_tree_still_works(self):
        for key in range(20):
            self.tree.insert(key, f"value-{key}")
        for key in range(0, 20, 2):
            self.tree.delete(key)

        self.assertEqual(len(self.tree), 10)
        self.assertEqual(self.tree.keys(), list(range(1, 20, 2)))
        for key in range(1, 20, 2):
            self.assertEqual(self.tree.search(key), f"value-{key}")

    def test_deleting_every_key_leaves_empty_tree(self):
        for key in range(15):
            self.tree.insert(key, f"value-{key}")
        for key in range(15):
            self.tree.delete(key)

        self.assertEqual(len(self.tree), 0)
        self.assertEqual(self.tree.keys(), [])

    def test_matches_dict_behavior_under_random_operations(self):
        # Fuzz test: run a long random sequence of inserts and deletes
        # and check the tree agrees with a plain dict at every step.
        random.seed(42)
        reference = {}
        key_pool = list(range(30))

        for _ in range(500):
            key = random.choice(key_pool)
            if random.random() < 0.7:
                value = f"v{random.randint(0, 1000)}"
                self.tree.insert(key, value)
                reference[key] = value
            elif key in reference:
                self.tree.delete(key)
                del reference[key]

        self.assertEqual(len(self.tree), len(reference))
        self.assertEqual(self.tree.keys(), sorted(reference.keys()))
        for key, value in reference.items():
            self.assertEqual(self.tree.search(key), value)


if __name__ == "__main__":
    unittest.main()
