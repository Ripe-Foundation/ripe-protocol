import json
import os
import stat
import tempfile


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


def save(filename, content=None):
    """Crash-atomically replace one JSON file in its existing directory."""

    if content is None:
        content = {}
    directory = os.path.dirname(filename) or "."
    os.makedirs(directory, exist_ok=True)
    payload = json.dumps(content, indent=2).encode("utf-8")
    target_mode = 0o644
    try:
        target_mode = stat.S_IMODE(os.stat(filename).st_mode)
    except FileNotFoundError:
        pass

    fd, temporary = tempfile.mkstemp(
        prefix=f".{os.path.basename(filename)}.",
        suffix=".tmp",
        dir=directory,
    )
    descriptor_open = True
    try:
        os.fchmod(fd, target_mode)
        write_all(fd, payload)
        os.fsync(fd)
        os.close(fd)
        descriptor_open = False
        os.replace(temporary, filename)
        temporary = None

        directory_fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if descriptor_open:
            os.close(fd)
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass

    return filename
