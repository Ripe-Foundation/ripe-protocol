from types import SimpleNamespace

import pytest
from web3 import Web3 as RealWeb3

from config.BluePrint import ROBINHOOD_ADDRESSES
from scripts.utils import ledger_deployment


LEDGER_ADDRESS = "0x" + "1" * 40
SOURCE_SELECTOR = RealWeb3.keccak(text="ACTION_BLOCK_SOURCE()")[:4]
ACTION_BLOCK_SELECTOR = RealWeb3.keccak(text="getArbActionBlock()")[:4]


class _Migration:
    def __init__(self, rpc):
        self._rpc = rpc

    def rpc(self):
        return self._rpc


def _word(value):
    return value.to_bytes(32, "big")


@pytest.fixture
def node(monkeypatch):
    state = SimpleNamespace(
        connected=True,
        constructor_error=None,
        code=b"\x01",
        code_error=None,
        call_errors={},
        results={SOURCE_SELECTOR: _word(0x64), ACTION_BLOCK_SELECTOR: _word(99)},
        calls=[],
        code_reads=[],
        providers=[],
    )

    class FakeEth:
        def get_code(self, address):
            state.code_reads.append(address)
            if state.code_error is not None:
                raise state.code_error
            return state.code

        def call(self, transaction):
            state.calls.append(transaction)
            selector = transaction["data"]
            if selector in state.call_errors:
                raise state.call_errors[selector]
            return state.results[selector]

    class FakeWeb3:
        eth = FakeEth()

        def __init__(self, provider):
            state.providers.append(provider)
            if state.constructor_error is not None:
                raise state.constructor_error
            self.eth = self.__class__.eth

        @staticmethod
        def HTTPProvider(rpc):
            return ("provider", rpc)

        @staticmethod
        def to_checksum_address(address):
            return address

        @staticmethod
        def keccak(*, text):
            return RealWeb3.keccak(text=text)

        def is_connected(self):
            return state.connected

    monkeypatch.setattr(ledger_deployment, "_load_web3", lambda: FakeWeb3)
    return state


def _validate(node, expected_source=0x64, *, allow_local_preview=False):
    return ledger_deployment.validate_ledger_action_block_source(
        _Migration("https://rpc.example"),
        LEDGER_ADDRESS,
        expected_source,
        allow_local_preview=allow_local_preview,
    )


def test_expected_source_representations_normalize_identically(node):
    representations = (
        0x64,
        "0x64",
        ROBINHOOD_ADDRESSES["ARB_SYS"],
    )

    assert [_validate(node, source) for source in representations] == [
        (0x64, 99),
        (0x64, 99),
        (0x64, 99),
    ]


@pytest.mark.parametrize("source", [None, object(), True, 1.0, b"\x64"])
def test_unsupported_expected_source_types_fail_clearly(source):
    with pytest.raises(TypeError, match="integer or 0x-prefixed hex string"):
        ledger_deployment.validate_ledger_action_block_source(
            _Migration(None),
            LEDGER_ADDRESS,
            source,
            allow_local_preview=True,
        )


@pytest.mark.parametrize("source", ["64", "0x", "0xzz", "0x64-nope"])
def test_malformed_expected_source_strings_fail_clearly(source):
    with pytest.raises(ValueError, match="valid 0x-prefixed hex string"):
        ledger_deployment.validate_ledger_action_block_source(
            _Migration(None),
            LEDGER_ADDRESS,
            source,
            allow_local_preview=True,
        )


@pytest.mark.parametrize(
    "source,message",
    [
        (-1, "must not be negative"),
        (2**160, "exceeds the 160-bit address range"),
    ],
)
def test_out_of_range_expected_sources_fail_clearly(source, message):
    with pytest.raises(ValueError, match=message):
        ledger_deployment.validate_ledger_action_block_source(
            _Migration(None),
            LEDGER_ADDRESS,
            source,
            allow_local_preview=True,
        )


def test_correct_nonzero_source_and_positive_action_block(node):
    assert _validate(node) == (0x64, 99)
    assert [call["data"] for call in node.calls] == [
        SOURCE_SELECTOR,
        ACTION_BLOCK_SELECTOR,
    ]


def test_wrong_stored_source_fails(node):
    node.results[SOURCE_SELECTOR] = _word(0x65)

    with pytest.raises(AssertionError, match="Ledger action-block source mismatch"):
        _validate(node)


def test_zero_action_block_fails(node):
    node.results[ACTION_BLOCK_SELECTOR] = _word(0)

    with pytest.raises(AssertionError, match="ArbSys action block reads zero"):
        _validate(node)


@pytest.mark.parametrize("rpc", [None, "boa"])
def test_strict_mode_requires_real_rpc(rpc):
    with pytest.raises(
        AssertionError,
        match="production Ledger requires a real RPC node",
    ):
        ledger_deployment.validate_ledger_action_block_source(
            _Migration(rpc),
            LEDGER_ADDRESS,
            0x64,
        )


def test_rpc_connection_failure_fails_closed(node):
    node.connected = False

    with pytest.raises(
        AssertionError,
        match="production Ledger RPC is unavailable",
    ):
        _validate(node)


def test_missing_web3_dependency_is_not_mislabeled_as_rpc_failure(monkeypatch):
    failure = ImportError("web3 dependency is unavailable")

    def fail_to_load_web3():
        raise failure

    monkeypatch.setattr(ledger_deployment, "_load_web3", fail_to_load_web3)

    with pytest.raises(
        ImportError,
        match="web3 dependency is unavailable",
    ) as exc_info:
        ledger_deployment.validate_ledger_action_block_source(
            _Migration("https://rpc.example"),
            LEDGER_ADDRESS,
            0x64,
        )
    assert exc_info.value is failure


def test_rpc_constructor_failure_preserves_cause(node):
    failure = RuntimeError("provider construction failed")
    node.constructor_error = failure

    with pytest.raises(
        AssertionError,
        match="production Ledger RPC is unavailable",
    ) as exc_info:
        _validate(node)
    assert exc_info.value.__cause__ is failure


def test_missing_ledger_code_has_specific_strict_diagnosis(node):
    node.code = b""

    with pytest.raises(
        AssertionError,
        match="Ledger is not deployed on the configured RPC",
    ):
        _validate(node)
    assert node.calls == []


def test_malformed_action_block_source_readback_fails(node):
    node.results[SOURCE_SELECTOR] = b"\x00" * 31

    with pytest.raises(
        AssertionError,
        match=r"malformed ACTION_BLOCK_SOURCE\(\) readback",
    ):
        _validate(node)


def test_malformed_get_arb_action_block_readback_fails(node):
    node.results[ACTION_BLOCK_SELECTOR] = b"\x00" * 33

    with pytest.raises(
        AssertionError,
        match=r"malformed getArbActionBlock\(\) readback",
    ):
        _validate(node)


def test_node_call_failure_fails_closed(node):
    node.call_errors[SOURCE_SELECTOR] = RuntimeError("node call failed")

    with pytest.raises(RuntimeError, match="node call failed"):
        _validate(node)


def test_zero_expected_source_skips_liveness_call(node):
    node.results[SOURCE_SELECTOR] = _word(0)

    assert _validate(node, 0) == (0, None)
    assert [call["data"] for call in node.calls] == [SOURCE_SELECTOR]


@pytest.mark.parametrize("rpc", [None, "boa"])
def test_local_preview_without_real_rpc_is_an_explicit_skip(monkeypatch, rpc):
    messages = []
    monkeypatch.setattr(ledger_deployment.log, "info", messages.append)

    result = ledger_deployment.validate_ledger_action_block_source(
        _Migration(rpc),
        LEDGER_ADDRESS,
        0x64,
        allow_local_preview=True,
    )

    assert result is None
    assert any("local/fork preview" in message for message in messages)


def test_local_preview_without_upstream_candidate_code_is_an_explicit_skip(
    monkeypatch,
    node,
):
    messages = []
    node.code = b""
    monkeypatch.setattr(ledger_deployment.log, "info", messages.append)

    assert _validate(node, allow_local_preview=True) is None
    assert node.calls == []
    assert any("only in the local/fork EVM" in message for message in messages)


@pytest.mark.parametrize(
    "case,error_type,message",
    [
        ("wrong-source", AssertionError, "Ledger action-block source mismatch"),
        (
            "malformed-source",
            AssertionError,
            r"malformed ACTION_BLOCK_SOURCE\(\) readback",
        ),
        (
            "malformed-action-block",
            AssertionError,
            r"malformed getArbActionBlock\(\) readback",
        ),
        ("zero-action-block", AssertionError, "ArbSys action block reads zero"),
        ("node-call-failure", RuntimeError, "node call failed"),
    ],
)
def test_local_preview_with_node_code_performs_full_validation(
    node,
    case,
    error_type,
    message,
):
    if case == "wrong-source":
        node.results[SOURCE_SELECTOR] = _word(0x65)
    elif case == "malformed-source":
        node.results[SOURCE_SELECTOR] = b""
    elif case == "malformed-action-block":
        node.results[ACTION_BLOCK_SELECTOR] = b"\x00"
    elif case == "zero-action-block":
        node.results[ACTION_BLOCK_SELECTOR] = _word(0)
    else:
        node.call_errors[ACTION_BLOCK_SELECTOR] = RuntimeError("node call failed")

    with pytest.raises(error_type, match=message):
        _validate(node, allow_local_preview=True)
