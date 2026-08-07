import os
import tempfile
import unittest

from src.storage.disk_store import DiskStore
from src.parser.parser import parse_sql
from src.engine.sql_executor import execute_statement


class TestSQLExecutor(unittest.TestCase):
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

    def run_sql(self, sql):
        statement = parse_sql(sql)
        return execute_statement(statement, self.store)

    def test_insert_via_sql_writes_to_store(self):
        self.run_sql("INSERT INTO users VALUES (1, 'Alice')")
        self.assertEqual(self.store.get(1), "Alice")

    def test_insert_via_sql_returns_none(self):
        result = self.run_sql("INSERT INTO users VALUES (1, 'Alice')")
        self.assertIsNone(result)

    def test_select_all_returns_every_row(self):
        self.run_sql("INSERT INTO t VALUES (1, 'a')")
        self.run_sql("INSERT INTO t VALUES (2, 'b')")
        rows = self.run_sql("SELECT * FROM t")
        self.assertEqual(rows, [(1, "a"), (2, "b")])

    def test_select_on_empty_store_returns_empty_list(self):
        rows = self.run_sql("SELECT * FROM t")
        self.assertEqual(rows, [])

    def test_select_with_where_key_equals(self):
        self.run_sql("INSERT INTO t VALUES (1, 'a')")
        self.run_sql("INSERT INTO t VALUES (2, 'b')")
        rows = self.run_sql("SELECT * FROM t WHERE key = 2")
        self.assertEqual(rows, [(2, "b")])

    def test_select_with_where_key_greater_than(self):
        for i in range(5):
            self.run_sql(f"INSERT INTO t VALUES ({i}, 'v{i}')")
        rows = self.run_sql("SELECT * FROM t WHERE key > 2")
        self.assertEqual(rows, [(3, "v3"), (4, "v4")])

    def test_select_with_where_value_equals(self):
        self.run_sql("INSERT INTO t VALUES (1, 'Alice')")
        self.run_sql("INSERT INTO t VALUES (2, 'Bob')")
        rows = self.run_sql("SELECT * FROM t WHERE value = 'Bob'")
        self.assertEqual(rows, [(2, "Bob")])

    def test_select_with_where_matching_nothing_returns_empty_list(self):
        self.run_sql("INSERT INTO t VALUES (1, 'a')")
        rows = self.run_sql("SELECT * FROM t WHERE key = 99")
        self.assertEqual(rows, [])

    def test_select_where_value_with_ordering_operator_does_not_crash(self):
        # value is always a string; comparing it with '>' against a
        # number should not match anything, and must not raise.
        self.run_sql("INSERT INTO t VALUES (1, 'a')")
        rows = self.run_sql("SELECT * FROM t WHERE value > 5")
        self.assertEqual(rows, [])

    def test_insert_via_sql_overwrites_existing_key(self):
        self.run_sql("INSERT INTO t VALUES (1, 'first')")
        self.run_sql("INSERT INTO t VALUES (1, 'second')")
        rows = self.run_sql("SELECT * FROM t")
        self.assertEqual(rows, [(1, "second")])

    def test_data_inserted_via_sql_persists_after_reopen(self):
        self.run_sql("INSERT INTO t VALUES (1, 'Alice')")
        self.store.close()

        reopened_store = DiskStore(self.db_path)
        statement = parse_sql("SELECT * FROM t")
        rows = execute_statement(statement, reopened_store)
        self.assertEqual(rows, [(1, "Alice")])
        reopened_store.close()


if __name__ == "__main__":
    unittest.main()
