"""Deterministic canonical JSON encoding/decoding for fork-test evidence files.

Extracted from the retired manifest-v2 schema module: the fork test suite
(tests/deployment/fork/**) hashes and round-trips small JSON documents
(identity manifests, envelopes) and needs byte-stable output to do that, but
none of the schema validation, history, or filesystem-publication machinery
that module also carried. This is the ~50 lines of that module actually
reachable from a test.
"""

from __future__ import annotations

import unicodedata
from typing import Any

from scripts.utils import json_file

_MAX_INT = (1 << 256) - 1
_MIN_INT = -(1 << 255)


class ManifestError(ValueError):
    """Raised when a value can't be encoded as, or parsed from, canonical JSON."""


def _validate_unicode(value: str) -> None:
    if unicodedata.normalize("NFC", value) != value:
        raise ManifestError("string is not Unicode NFC-normalized")
    for character in value:
        codepoint = ord(character)
        if 0xD800 <= codepoint <= 0xDFFF:
            raise ManifestError("string contains an unpaired surrogate scalar")


def _validate_json_domain(value: Any) -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        if value < _MIN_INT or value > _MAX_INT:
            raise ManifestError("integer out of representable range")
        return
    if isinstance(value, float):
        raise ManifestError("floats are not representable in canonical JSON")
    if isinstance(value, str):
        _validate_unicode(value)
        return
    if isinstance(value, list):
        for item in value:
            _validate_json_domain(item)
        return
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ManifestError("object keys must be strings")
            _validate_unicode(key)
            _validate_json_domain(child)
        return
    raise ManifestError(f"value of type {type(value).__name__} is not JSON-representable")


def _escape_string(value: str) -> bytes:
    pieces = ['"']
    for character in value:
        codepoint = ord(character)
        if character == '"':
            pieces.append('\\"')
        elif character == "\\":
            pieces.append("\\\\")
        elif codepoint <= 0x1F:
            pieces.append(f"\\u00{codepoint:02x}")
        else:
            pieces.append(character)
    pieces.append('"')
    return "".join(pieces).encode("utf-8")


def _emit_canonical(value: Any, output: bytearray) -> None:
    if value is None:
        output.extend(b"null")
    elif value is True:
        output.extend(b"true")
    elif value is False:
        output.extend(b"false")
    elif isinstance(value, int) and not isinstance(value, bool):
        output.extend(str(value).encode("ascii"))
    elif isinstance(value, str):
        output.extend(_escape_string(value))
    elif isinstance(value, list):
        output.extend(b"[")
        for index, item in enumerate(value):
            if index:
                output.extend(b",")
            _emit_canonical(item, output)
        output.extend(b"]")
    elif isinstance(value, dict):
        output.extend(b"{")
        ordered_keys = sorted(value, key=lambda item: item.encode("utf-8"))
        for index, key in enumerate(ordered_keys):
            if index:
                output.extend(b",")
            output.extend(_escape_string(key))
            output.extend(b":")
            _emit_canonical(value[key], output)
        output.extend(b"}")
    else:
        raise ManifestError(f"value of type {type(value).__name__} is not JSON-representable")


def canonical_json_bytes(value: Any) -> bytes:
    """Return deterministic canonical JSON bytes, including one terminal LF."""
    _validate_json_domain(value)
    output = bytearray()
    _emit_canonical(value, output)
    output.extend(b"\n")
    return bytes(output)


def load_json_bytes(data: bytes) -> Any:
    """Strictly parse JSON bytes, rejecting duplicate keys and out-of-range integers."""
    try:
        return json_file.loads_strict(
            data,
            min_integer=_MIN_INT,
            max_integer=_MAX_INT,
        )
    except (UnicodeDecodeError, ValueError) as error:
        raise ManifestError(f"invalid JSON: {error}") from error
