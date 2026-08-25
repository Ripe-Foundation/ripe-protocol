"""Generic deployment-manifest coverage for struct constructor arguments."""

from eth_abi import encode

from scripts.utils.migration import _encode_expected_constructor_args
from scripts.utils.migration_helpers import encode_constructor_args


CONSTRUCTOR_ABI = [
    {
        "type": "constructor",
        "inputs": [
            {"name": "hq", "type": "address"},
            {
                "name": "config",
                "type": "tuple",
                "components": [
                    {"name": "cap", "type": "uint256"},
                    {"name": "rate", "type": "uint256"},
                ],
            },
        ],
    }
]


def test_manifest_and_promotion_encode_struct_constructor_identically():
    hq = "0x" + "12" * 20
    values = (hq, (10_000_000, 4 * 10**18))
    expected = encode(
        ["address", "(uint256,uint256)"],
        values,
    )

    assert bytes.fromhex(encode_constructor_args(CONSTRUCTOR_ABI, values)) == expected
    assert _encode_expected_constructor_args(CONSTRUCTOR_ABI, values) == expected
