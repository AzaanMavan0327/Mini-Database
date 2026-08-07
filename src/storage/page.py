import struct

PAGE_SIZE = 4096

# Header layout: 1 byte occupied flag, 8 byte signed key, 4 byte value length
HEADER_FORMAT = "!B q I"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
MAX_VALUE_SIZE = PAGE_SIZE - HEADER_SIZE

OCCUPIED = 1
FREE = 0


def encode_page(key, value, occupied=True):
    """Pack a key-value pair into a fixed-size page of bytes."""
    value_bytes = value.encode("utf-8")
    if len(value_bytes) > MAX_VALUE_SIZE:
        raise ValueError(
            f"Value is too large: {len(value_bytes)} bytes, max is {MAX_VALUE_SIZE} bytes"
        )

    flag = OCCUPIED if occupied else FREE
    header = struct.pack(HEADER_FORMAT, flag, key, len(value_bytes))
    padding = b"\x00" * (MAX_VALUE_SIZE - len(value_bytes))
    return header + value_bytes + padding


def decode_page(raw_bytes):
    """Unpack a page of bytes back into (is_occupied, key, value)."""
    flag, key, value_length = struct.unpack(HEADER_FORMAT, raw_bytes[:HEADER_SIZE])
    value_bytes = raw_bytes[HEADER_SIZE:HEADER_SIZE + value_length]
    value = value_bytes.decode("utf-8")
    is_occupied = flag == OCCUPIED
    return is_occupied, key, value
