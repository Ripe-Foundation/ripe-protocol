from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from utils.canonical_json import ManifestError, canonical_json_bytes, load_json_bytes

ROOT = Path(__file__).resolve().parents[2]


def test_canonical_serialization_exact_key_escape_and_newline_vector():
    value = {"\U00010000": 0, "": False, "a": "\b\t\n/\\"}
    expected = (
        '{"a":"\\u0008\\u0009\\u000a/\\\\","":false,"𐀀":0}\n'
    ).encode()
    assert canonical_json_bytes(value) == expected
    assert not canonical_json_bytes(value).endswith(b"\n\n")


def test_key_ordering_is_byte_lexicographic_not_insertion_order():
    assert canonical_json_bytes({"b": 1, "a": 2}) == b'{"a":2,"b":1}\n'


@pytest.mark.parametrize(
    "raw",
    (
        b'{"a":1,"a":2}',
        b'{"a":1.0}',
        b'{"a":NaN}',
        b'{"a":Infinity}',
        b'{"a":-Infinity}',
        b'{"a":-0.0}',
    ),
)
def test_strict_parser_rejects_duplicate_float_and_nonfinite(raw):
    with pytest.raises(ManifestError) as error:
        load_json_bytes(raw)
    assert error.value.code == "JSON_PARSE"


def test_load_json_bytes_round_trips_canonical_output():
    value = {"nested": [1, 2, {"k": None, "flag": True}], "s": "text"}
    assert load_json_bytes(canonical_json_bytes(value)) == value


@pytest.mark.parametrize(
    ("value", "code"),
    (
        (1.5, "FLOAT_FORBIDDEN"),
        ("\ud800", "UNICODE_INVALID_SCALAR"),
        ("é", "UNICODE_NOT_NFC"),
        (object(), "JSON_TYPE"),
    ),
)
def test_canonical_domain_rejects_float_surrogate_non_nfc_and_unrepresentable(
    value, code
):
    with pytest.raises(ManifestError) as error:
        canonical_json_bytes({"value": value})
    assert error.value.code == code


def test_object_keys_must_be_strings():
    with pytest.raises(ManifestError) as error:
        canonical_json_bytes({1: "a"})
    assert error.value.code == "OBJECT_KEY_TYPE"


@pytest.mark.parametrize(
    ("value", "should_raise"),
    (
        ((1 << 256) - 1, False),
        (-(1 << 255), False),
        (1 << 256, True),
        (-(1 << 255) - 1, True),
    ),
)
def test_integer_bounds_match_the_uint256_int256_envelope(value, should_raise):
    if should_raise:
        with pytest.raises(ManifestError) as error:
            canonical_json_bytes({"value": value})
        assert error.value.code == "INTEGER_RANGE"
    else:
        assert canonical_json_bytes({"value": value}) == f'{{"value":{value}}}\n'.encode()


@pytest.mark.parametrize(
    ("value", "should_raise"),
    (
        ((1 << 256) - 1, False),
        (-(1 << 255), False),
        (1 << 256, True),
        (-(1 << 255) - 1, True),
    ),
)
def test_load_json_bytes_enforces_the_same_integer_bounds(value, should_raise):
    raw = f'{{"value":{value}}}'.encode()
    if should_raise:
        with pytest.raises(ManifestError) as error:
            load_json_bytes(raw)
        assert error.value.code == "JSON_PARSE"
    else:
        assert load_json_bytes(raw) == {"value": value}


def test_load_json_bytes_rejects_invalid_utf8():
    with pytest.raises(ManifestError) as error:
        load_json_bytes(b'{"a":"\xff\xfe"}')
    assert error.value.code == "JSON_PARSE"


def test_load_json_bytes_requires_bytes():
    with pytest.raises(TypeError):
        load_json_bytes('{"a":1}')


def test_two_clean_processes_produce_identical_canonical_bytes(tmp_path):
    value = {
        "b": [1, 2, 3],
        "a": {"nested": True, "unicode": "\U00010000"},
        "": None,
    }
    expression = (
        "from utils.canonical_json import canonical_json_bytes;"
        f"import sys;sys.stdout.buffer.write(canonical_json_bytes({value!r}))"
    )
    environment = {
        "PATH": os.defpath,
        "PYTHONPATH": os.pathsep.join((str(ROOT), str(ROOT / "tests"))),
    }
    outputs = []
    for name in ("checkout-a", "checkout-b"):
        checkout = tmp_path / name
        checkout.mkdir(mode=0o700)
        result = subprocess.run(
            [sys.executable, "-c", expression],
            cwd=checkout,
            env=environment,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr.decode()
        outputs.append(result.stdout)
    assert outputs[0] == outputs[1] == canonical_json_bytes(value)
