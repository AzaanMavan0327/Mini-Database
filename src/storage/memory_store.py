class MemoryStore:
    """A simple in-memory key-value store backed by a dict.

    Keys are expected to be integers and values are expected to be
    strings. Data is not persisted and will be lost when the program
    exits.
    """

    def __init__(self):
        self._data = {}

    def insert(self, key, value):
        self._data[key] = value

    def get(self, key):
        if key not in self._data:
            raise KeyError(f"Key {key} not found")
        return self._data[key]

    def delete(self, key):
        if key not in self._data:
            raise KeyError(f"Key {key} not found")
        del self._data[key]

    def keys(self):
        return list(self._data.keys())

    def __len__(self):
        return len(self._data)
