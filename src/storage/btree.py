class BTreeNode:
    def __init__(self, is_leaf=True):
        self.keys = []
        self.values = []
        self.children = []
        self.is_leaf = is_leaf


class BTree:
    """A B-tree index mapping keys to values (e.g. page numbers).

    Keeps keys in sorted order and rebalances itself on insert and delete,
    so search, insert, and delete all stay O(log n) even as the number of
    keys grows into the thousands.

    MIN_DEGREE controls how many keys each node can hold: at most
    2 * MIN_DEGREE - 1, and at least MIN_DEGREE - 1 (except the root).
    Real databases size this around their disk page size; a small value
    is used here so splits and merges happen with only a handful of
    keys, which makes the tree easy to trace through while testing.
    """

    MIN_DEGREE = 2

    def __init__(self):
        self.root = BTreeNode(is_leaf=True)
        self._size = 0

    def __len__(self):
        return self._size

    def search(self, key):
        result = self._find(self.root, key)
        if result is None:
            raise KeyError(f"Key {key} not found")
        node, index = result
        return node.values[index]

    def insert(self, key, value):
        existing = self._find(self.root, key)
        if existing is not None:
            node, index = existing
            node.values[index] = value
            return

        max_keys = 2 * self.MIN_DEGREE - 1
        if len(self.root.keys) == max_keys:
            new_root = BTreeNode(is_leaf=False)
            new_root.children.append(self.root)
            self._split_child(new_root, 0)
            self.root = new_root

        self._insert_non_full(self.root, key, value)
        self._size += 1

    def delete(self, key):
        if self._find(self.root, key) is None:
            raise KeyError(f"Key {key} not found")

        self._delete_from_node(self.root, key)
        self._size -= 1

        if not self.root.is_leaf and len(self.root.keys) == 0:
            self.root = self.root.children[0]

    def keys(self):
        result = []
        self._collect_keys(self.root, result)
        return result

    # --- search and insert helpers ---

    def _find(self, node, key):
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        if i < len(node.keys) and node.keys[i] == key:
            return node, i
        if node.is_leaf:
            return None
        return self._find(node.children[i], key)

    def _collect_keys(self, node, result):
        for i in range(len(node.keys)):
            if not node.is_leaf:
                self._collect_keys(node.children[i], result)
            result.append(node.keys[i])
        if not node.is_leaf:
            self._collect_keys(node.children[len(node.keys)], result)

    def _split_child(self, parent, child_index):
        t = self.MIN_DEGREE
        child = parent.children[child_index]
        new_node = BTreeNode(is_leaf=child.is_leaf)

        mid_key = child.keys[t - 1]
        mid_value = child.values[t - 1]

        new_node.keys = child.keys[t:]
        new_node.values = child.values[t:]
        child.keys = child.keys[:t - 1]
        child.values = child.values[:t - 1]

        if not child.is_leaf:
            new_node.children = child.children[t:]
            child.children = child.children[:t]

        parent.children.insert(child_index + 1, new_node)
        parent.keys.insert(child_index, mid_key)
        parent.values.insert(child_index, mid_value)

    def _insert_non_full(self, node, key, value):
        i = len(node.keys) - 1

        if node.is_leaf:
            node.keys.append(None)
            node.values.append(None)
            while i >= 0 and key < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                node.values[i + 1] = node.values[i]
                i -= 1
            node.keys[i + 1] = key
            node.values[i + 1] = value
            return

        while i >= 0 and key < node.keys[i]:
            i -= 1
        i += 1

        max_keys = 2 * self.MIN_DEGREE - 1
        if len(node.children[i].keys) == max_keys:
            self._split_child(node, i)
            if key > node.keys[i]:
                i += 1

        self._insert_non_full(node.children[i], key, value)

    # --- delete helpers ---

    def _delete_from_node(self, node, key):
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1

        if i < len(node.keys) and node.keys[i] == key:
            if node.is_leaf:
                node.keys.pop(i)
                node.values.pop(i)
                return

            left_child = node.children[i]
            right_child = node.children[i + 1]
            t = self.MIN_DEGREE

            if len(left_child.keys) >= t:
                pred_key, pred_value = self._max_key_value(left_child)
                node.keys[i] = pred_key
                node.values[i] = pred_value
                self._delete_from_node(left_child, pred_key)
            elif len(right_child.keys) >= t:
                succ_key, succ_value = self._min_key_value(right_child)
                node.keys[i] = succ_key
                node.values[i] = succ_value
                self._delete_from_node(right_child, succ_key)
            else:
                self._merge_children(node, i)
                self._delete_from_node(left_child, key)
            return

        if node.is_leaf:
            raise KeyError(f"Key {key} not found")

        child = self._ensure_child_has_min_keys(node, i)
        self._delete_from_node(child, key)

    def _max_key_value(self, node):
        while not node.is_leaf:
            node = node.children[-1]
        return node.keys[-1], node.values[-1]

    def _min_key_value(self, node):
        while not node.is_leaf:
            node = node.children[0]
        return node.keys[0], node.values[0]

    def _ensure_child_has_min_keys(self, parent, index):
        """Make sure parent.children[index] has enough keys to safely
        recurse into, borrowing from a sibling or merging as needed.
        Returns the child node to descend into, since a merge can move
        it to a different index."""
        t = self.MIN_DEGREE
        child = parent.children[index]
        if len(child.keys) >= t:
            return child

        has_left_sibling = index > 0
        has_right_sibling = index < len(parent.children) - 1

        if has_left_sibling and len(parent.children[index - 1].keys) >= t:
            self._borrow_from_left(parent, index)
            return child
        elif has_right_sibling and len(parent.children[index + 1].keys) >= t:
            self._borrow_from_right(parent, index)
            return child
        elif has_left_sibling:
            self._merge_children(parent, index - 1)
            return parent.children[index - 1]
        else:
            self._merge_children(parent, index)
            return parent.children[index]

    def _borrow_from_left(self, parent, index):
        child = parent.children[index]
        left_sibling = parent.children[index - 1]

        child.keys.insert(0, parent.keys[index - 1])
        child.values.insert(0, parent.values[index - 1])

        parent.keys[index - 1] = left_sibling.keys.pop()
        parent.values[index - 1] = left_sibling.values.pop()

        if not child.is_leaf:
            child.children.insert(0, left_sibling.children.pop())

    def _borrow_from_right(self, parent, index):
        child = parent.children[index]
        right_sibling = parent.children[index + 1]

        child.keys.append(parent.keys[index])
        child.values.append(parent.values[index])

        parent.keys[index] = right_sibling.keys.pop(0)
        parent.values[index] = right_sibling.values.pop(0)

        if not child.is_leaf:
            child.children.append(right_sibling.children.pop(0))

    def _merge_children(self, parent, index):
        left_child = parent.children[index]
        right_child = parent.children[index + 1]

        left_child.keys.append(parent.keys[index])
        left_child.values.append(parent.values[index])
        left_child.keys.extend(right_child.keys)
        left_child.values.extend(right_child.values)

        if not left_child.is_leaf:
            left_child.children.extend(right_child.children)

        parent.keys.pop(index)
        parent.values.pop(index)
        parent.children.pop(index + 1)
