import json
import os


def _reject_duplicate_pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON object key")
        value[key] = item
    return value


def loads_strict(data, *, min_integer=None, max_integer=None):
    """Parse UTF-8 JSON without duplicate keys, floats, or constants."""

    if not isinstance(data, bytes):
        raise TypeError("strict JSON input must be bytes")

    def parse_integer(value):
        parsed = int(value)
        if min_integer is not None and parsed < min_integer:
            raise ValueError("JSON integer below minimum")
        if max_integer is not None and parsed > max_integer:
            raise ValueError("JSON integer above maximum")
        return parsed

    def reject_float(value):
        raise ValueError(f"JSON float is forbidden: {value}")

    def reject_constant(value):
        raise ValueError(f"JSON constant is forbidden: {value}")

    return json.loads(
        data.decode("utf-8"),
        object_pairs_hook=_reject_duplicate_pairs,
        parse_int=parse_integer,
        parse_float=reject_float,
        parse_constant=reject_constant,
    )


def write_all(fd, data):
    """Write all bytes to an already-open descriptor or raise."""

    if not isinstance(data, bytes):
        raise TypeError("write_all input must be bytes")
    offset = 0
    while offset < len(data):
        written = os.write(fd, data[offset:])
        if written <= 0:
            raise OSError("short write")
        offset += written


def read_all(fd, *, chunk_size=1024 * 1024):
    """Read all bytes from the descriptor's current offset."""

    chunks = []
    while True:
        chunk = os.read(fd, chunk_size)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def load(filename):
    # loads the json content of a file
    # (error will be raised if file doesn't exist)

    file = {}
    with open(filename) as file:
        file = json.load(file)

    return file


def save(filename, content={}):
    # saves the json content to a file

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as outfile:
        json.dump(
            content,
            outfile,
            indent=2,
        )

    return outfile
