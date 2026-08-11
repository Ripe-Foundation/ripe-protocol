from pathlib import Path
from unittest import mock

import pytest
from click.testing import CliRunner

from scripts.utils import ccip


ROOT = Path(__file__).resolve().parents[1]
WIRE_MIGRATIONS = (
    "migrations/base-mainnet/2026080701_CcipWire.py",
    "migrations/robinhood-mainnet/2026080701_CcipWire.py",
    "migrations/base-sepolia/0002_CcipWire.py",
    "migrations/robinhood-testnet/0002_CcipWire.py",
)


def _ccip_send_module():
    with mock.patch("dotenv.load_dotenv"):
        import scripts.ccip_send as module

    return module


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        ("1", 10**18),
        ("1.5", 15 * 10**17),
        ("0.000000000000000001", 1),
        ("123456789012345678.123456789012345678", 123456789012345678123456789012345678),
    ),
)
def test_ccip_amount_parser_is_exact(text, expected):
    module = _ccip_send_module()
    assert module._parse_amount(text) == expected
    assert module._parse_amount(module._format_amount(expected)) == expected


def test_ccip_amount_parser_accepts_exact_uint256_maximum():
    module = _ccip_send_module()
    text = module._format_amount(module.MAX_UINT256)
    assert module._parse_amount(text) == module.MAX_UINT256


@pytest.mark.parametrize(
    "text",
    (
        "",
        "0",
        "0.0",
        "-1",
        "+1",
        "1e18",
        ".1",
        "1.",
        "00",
        "1.0000000000000000001",
        " 1",
        "1 ",
    ),
)
def test_ccip_amount_parser_rejects_ambiguous_or_nonpositive_values(text):
    with pytest.raises(ValueError):
        _ccip_send_module()._parse_amount(text)


def test_ccip_amount_parser_rejects_uint256_overflow():
    module = _ccip_send_module()
    overflow = module._format_amount(module.MAX_UINT256 + 1)
    with pytest.raises(ValueError, match="exceeds uint256"):
        module._parse_amount(overflow)


def _live_args():
    return [
        "--chain",
        "base-mainnet",
        "--environment",
        "v1",
        "--amount",
        "1.000000000000000001",
        "--rpc",
        "https://rpc.invalid",
    ]


def test_live_send_validates_chain_and_manifest_then_fails_at_backend(monkeypatch):
    module = _ccip_send_module()
    observed = []
    real_manifest = module._manifest

    monkeypatch.setattr(module, "_read_chain_id", lambda rpc: 8453)

    def manifest(chain, environment):
        observed.append((chain, environment))
        return real_manifest(chain, environment)

    monkeypatch.setattr(module, "_manifest", manifest)
    result = CliRunner().invoke(module.cli, _live_args())

    assert result.exit_code != 0
    assert "CCIP_LIVE_SIGNER_UNBOUND" in result.output
    assert observed == [("base-mainnet", "v1")]


def test_chain_id_mismatch_fails_before_live_backend(monkeypatch):
    module = _ccip_send_module()
    monkeypatch.setattr(module, "_read_chain_id", lambda rpc: 4663)

    result = CliRunner().invoke(module.cli, _live_args())

    assert result.exit_code != 0
    assert "H02_CHAIN_ID_MISMATCH" in result.output
    assert "expected_chain_id=8453" in result.output
    assert "observed_chain_id=4663" in result.output
    assert "CCIP_LIVE_SIGNER_UNBOUND" not in result.output


def test_invalid_amount_fails_before_any_rpc_read(monkeypatch):
    module = _ccip_send_module()
    reader = mock.Mock(side_effect=AssertionError("RPC must not be read"))
    monkeypatch.setattr(module, "_read_chain_id", reader)
    args = _live_args()
    args[args.index("1.000000000000000001")] = "1e18"

    result = CliRunner().invoke(module.cli, args)

    assert result.exit_code != 0
    assert "invalid --amount" in result.output
    reader.assert_not_called()


def test_fork_requires_explicit_impersonated_address_before_rpc(monkeypatch):
    module = _ccip_send_module()
    reader = mock.Mock(side_effect=AssertionError("RPC must not be read"))
    monkeypatch.setattr(module, "_read_chain_id", reader)

    result = CliRunner().invoke(module.cli, [*_live_args(), "--fork"])

    assert result.exit_code != 0
    assert "--as-address is required in fork mode" in result.output
    reader.assert_not_called()


class _ConfiguredPool:
    def __init__(self, selector, remote_pool, remote_token, rate=(False, 0, 0)):
        self.selector = selector
        self.remote_pools = [ccip.encode_address(remote_pool)]
        self.remote_token = ccip.encode_address(remote_token)
        self.rate = rate
        self.rate_admin = "0x0000000000000000000000000000000000000000"
        self.calls = []

    def isSupportedChain(self, selector):
        self.calls.append("isSupportedChain")
        return selector == self.selector

    def getRemoteToken(self, selector):
        self.calls.append("getRemoteToken")
        return self.remote_token

    def getRemotePools(self, selector):
        self.calls.append("getRemotePools")
        return self.remote_pools

    def _bucket(self):
        enabled, capacity, rate = self.rate
        return (capacity, 1, enabled, capacity, rate)

    def getCurrentOutboundRateLimiterState(self, selector):
        self.calls.append("getCurrentOutboundRateLimiterState")
        return self._bucket()

    def getCurrentInboundRateLimiterState(self, selector):
        self.calls.append("getCurrentInboundRateLimiterState")
        return self._bucket()

    def getRateLimitAdmin(self):
        self.calls.append("getRateLimitAdmin")
        return self.rate_admin


def test_supported_lane_is_fully_revalidated():
    selector = 6180753054346818345
    remote_pool = "0xE51aF1311832818A6D366081Fc535CA56357a6EE"
    remote_token = "0x4D3f37a965b21aB4122e92Dd41D2693E742c883b"
    pool = _ConfiguredPool(selector, remote_pool, remote_token)

    ccip.assert_lane_configuration(
        pool,
        selector,
        remote_pool,
        remote_token,
        (False, 0, 0),
        "0x0000000000000000000000000000000000000000",
    )

    assert pool.calls == [
        "isSupportedChain",
        "getRemoteToken",
        "getRemotePools",
        "getCurrentOutboundRateLimiterState",
        "getCurrentInboundRateLimiterState",
        "getRateLimitAdmin",
    ]


@pytest.mark.parametrize("mutation", ("token", "extra_pool", "rate", "rate_admin"))
def test_supported_lane_revalidation_rejects_stale_or_wrong_wiring(mutation):
    selector = 6180753054346818345
    remote_pool = "0xE51aF1311832818A6D366081Fc535CA56357a6EE"
    remote_token = "0x4D3f37a965b21aB4122e92Dd41D2693E742c883b"
    pool = _ConfiguredPool(selector, remote_pool, remote_token)
    if mutation == "token":
        pool.remote_token = ccip.encode_address(
            "0x355bB7F0f6c730e4460d620420a300fa08FF82F3"
        )
    elif mutation == "extra_pool":
        pool.remote_pools.append(
            ccip.encode_address("0x4B19f165Bb1Ce3f19Bbe828D150706B9deeEeC95")
        )
    elif mutation == "rate":
        pool.rate = (True, 10**18, 10**15)
    else:
        pool.rate_admin = "0xe488a42D33b3Af5d3E5Cd5680938d8369716D1bf"

    with pytest.raises(AssertionError):
        ccip.assert_lane_configuration(
            pool,
            selector,
            remote_pool,
            remote_token,
            (False, 0, 0),
            "0x0000000000000000000000000000000000000000",
        )


@pytest.mark.parametrize("relative_path", WIRE_MIGRATIONS)
def test_wire_migration_revalidates_supported_lane_and_gates_new_mutation(
    relative_path,
):
    source = (ROOT / relative_path).read_text()
    supported_branch = source.index("if pool.isSupportedChain(remote_selector):")
    revalidation = source.index(
        "ccip.assert_lane_configuration(", supported_branch
    )
    mutation = source.index("migration.execute(pool.applyChainUpdates", supported_branch)

    assert "continue" not in source[supported_branch:revalidation]
    assert "require_ccip_wiring_gates()" in source[supported_branch:mutation]
