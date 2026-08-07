import unittest

from src.storage.page import encode_page, decode_page, MAX_VALUE_SIZE


class TestPage(unittest.TestCase):
    def test_encode_then_decode_returns_original_data(self):
        raw_page = encode_page(1, "hello world")
        is_occupied, key, value = decode_page(raw_page)

        self.assertTrue(is_occupied)
        self.assertEqual(key, 1)
        self.assertEqual(value, "hello world")

    def test_encoded_page_is_exactly_page_size(self):
        raw_page = encode_page(1, "short value")
        self.assertEqual(len(raw_page), 4096)

    def test_free_page_decodes_as_not_occupied(self):
        raw_page = encode_page(1, "", occupied=False)
        is_occupied, _, _ = decode_page(raw_page)
        self.assertFalse(is_occupied)

    def test_empty_value_round_trips_correctly(self):
        raw_page = encode_page(1, "")
        _, _, value = decode_page(raw_page)
        self.assertEqual(value, "")

    def test_value_over_max_size_raises_value_error(self):
        oversized_value = "x" * (MAX_VALUE_SIZE + 1)
        with self.assertRaises(ValueError):
            encode_page(1, oversized_value)

    def test_value_at_max_size_encodes_successfully(self):
        max_size_value = "x" * MAX_VALUE_SIZE
        raw_page = encode_page(1, max_size_value)
        _, _, value = decode_page(raw_page)
        self.assertEqual(value, max_size_value)


if __name__ == "__main__":
    unittest.main()
