"""
Bridge protocol tokens across a CCIP lane, straight through the router.

Transporter only lists tokens Chainlink has onboarded into its UI, so a self-served
token like RIPE has to call `Router.ccipSend()` itself. This tool currently supports
fork simulation/preflight only. It deliberately has no live signer or Safe transaction
backend and therefore cannot broadcast.

    python -m scripts.ccip_send --chain base-mainnet --environment v1 \
        --amount 10 --to-rpc https://destination.example \
        --receiver 0x... --fork --as-address 0x... \
        --acknowledge-destination-control

Arguments, the manifest, profile identity, and RPC chain ID are validated before the
account/backend boundary. Fork mode also requires an explicit receiver and an operator
acknowledgement that the destination is controlled; that acknowledgement and a
code-empty check are not cryptographic ownership proof. Non-fork execution remains
blocked by an unresolved receiver-control evidence gate and, independently,
`CCIP_LIVE_SIGNER_UNBOUND` until a real backend is separately reviewed and authorized.
"""

import json
import os
import re
from pathlib import Path
from urllib import request

import boa
import click
import dotenv
from eth_utils import is_address, to_checksum_address

from config.Ccip import CCIP, require_ccip_live_send_evidence
from config.network_profiles import (
    NetworkProfileError,
    Operation,
    get_profile,
    resolve_rpc_reference,
    verify_chain_identity,
)
from scripts.utils import ccip, log

dotenv.load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
MIGRATION_HISTORY_DIR = ROOT / "migration_history"
EIGHTEEN_DECIMALS = 10**18
MAX_UINT256 = 2**256 - 1
TOKEN_AMOUNT_RE = re.compile(r"(?:0|[1-9][0-9]*)(?:\.([0-9]{1,18}))?")
ENVIRONMENT_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")


@click.command()
@click.option(
    "--chain",
    required=True,
    type=click.Choice(sorted(CCIP), case_sensitive=True),
    help="Explicit source-chain profile.",
)
@click.option(
    "--to-chain",
    default="",
    help="Chain to send to. Defaults to the only remote chain.",
)
@click.option(
    "--environment",
    required=True,
    help="Manifest environment to read addresses from (for example v1).",
)
@click.option(
    "--token",
    default="RipeToken",
    type=click.Choice(("RipeToken", "GreenToken"), case_sensitive=True),
    help="Protocol token to bridge (both use 18 decimals).",
)
@click.option(
    "--amount",
    required=True,
    help="Exact decimal token amount (up to 18 decimal places).",
)
@click.option(
    "--receiver",
    required=True,
    help="Explicit recipient on the destination chain; no sender fallback is inferred.",
)
@click.option(
    "--rpc",
    default="",
    help="RPC URL. Defaults to the selected profile's RPC environment variable.",
)
@click.option(
    "--to-rpc",
    required=True,
    help="Explicit destination-chain HTTP(S) RPC used to verify chain identity and current code emptiness.",
)
@click.option(
    "--fork",
    is_flag=True,
    default=False,
    help="Simulate against a fork; this is the only executable mode.",
)
@click.option(
    "--as-address",
    default="",
    help="Fork-only sender to impersonate; no private key is loaded.",
)
@click.option(
    "--acknowledge-destination-control",
    is_flag=True,
    default=False,
    help=(
        "Fork-only operator acknowledgement that the explicit receiver is controlled; "
        "this is not cryptographic ownership proof or live-send authorization."
    ),
)
@click.option(
    "--fee-token", default="native", help="What to pay the CCIP fee in: native or link."
)
def cli(
    chain,
    to_chain,
    environment,
    token,
    amount,
    receiver,
    rpc,
    to_rpc,
    fork,
    as_address,
    acknowledge_destination_control,
    fee_token,
):
    """Preflight a token transfer across a configured CCIP lane."""
    try:
        amount = _parse_amount(amount)
        to_chain = _validate_request(
            chain,
            to_chain,
            environment,
            token,
            receiver,
            fork,
            as_address,
            acknowledge_destination_control,
        )

        profile = get_profile(chain)
        operation = Operation.CONSOLE_EXPLORATION
        rpc_reference = resolve_rpc_reference(
            profile,
            operation,
            os.environ,
            explicit_rpc=rpc or None,
        )
        verify_chain_identity(
            profile,
            operation,
            rpc_reference,
            _read_chain_id,
        )

        destination_profile = get_profile(to_chain)
        destination_rpc_reference = resolve_rpc_reference(
            destination_profile,
            operation,
            os.environ,
            explicit_rpc=to_rpc,
        )
        verify_chain_identity(
            destination_profile,
            operation,
            destination_rpc_reference,
            _read_chain_id,
        )

        receiver = to_checksum_address(receiver)
        _require_zero_gas_code_empty_destination(
            destination_rpc_reference.value, receiver
        )

        manifest = _manifest(chain, environment)
        token_record = _manifest_token(manifest, token, chain, environment)
        sender_address = _select_sender(
            fork,
            as_address,
            source_chain=chain,
            destination_chain=to_chain,
            receiver=receiver,
        )
    except (
        AssertionError,
        KeyError,
        NetworkProfileError,
        RuntimeError,
        ValueError,
    ) as error:
        raise click.ClickException(str(error)) from None

    log.h1(f"Bridging {token} from {chain} to {to_chain}")

    env = boa.fork(rpc_reference.value)
    with env:
        boa.env.eoa = sender_address
        log.info("fork mode: nothing will be broadcast")

        erc20 = boa.load_partial(str(ROOT / token_record["file"])).at(
            token_record["address"]
        )
        router = ccip.router(chain)
        selector = CCIP[to_chain]["CHAIN_SELECTOR"]

        log.info(f"token    {erc20.address}")
        log.info(f"router   {router.address}")
        log.info(f"sender   {sender_address}")
        log.info(f"receiver {receiver} on {to_chain} ({selector})")
        log.info(
            "destination code is empty at the preflight block; this and the "
            "operator acknowledgement do not prove receiver control"
        )
        log.info(f"amount   {_format_amount(amount)}")

        balance = erc20.balanceOf(sender_address)
        assert balance >= amount, (
            f"{sender_address} holds {_format_amount(balance)} {token}, "
            f"needs {_format_amount(amount)}"
        )
        assert router.isChainSupported(selector), f"router does not support {to_chain}"

        fee_erc20 = _fee_token(chain, fee_token)
        message = ccip.token_transfer_message(
            receiver,
            erc20.address,
            amount,
            fee_token=fee_erc20.address if fee_erc20 else ccip.ZERO_ADDRESS,
        )

        log.h2("Quoting the fee")
        fee = router.getFee(selector, message)
        symbol = fee_erc20.symbol() if fee_erc20 else "native"
        held = (
            fee_erc20.balanceOf(sender_address)
            if fee_erc20
            else boa.env.get_balance(sender_address)
        )
        log.info(f"fee      {_format_amount(fee)} {symbol}")
        log.info(f"balance  {_format_amount(held)} {symbol}")

        if _fee_balance_is_insufficient(held, fee, pays_in_erc20=fee_erc20 is not None):
            if fee_erc20:
                raise Exception(
                    f"sender holds {_format_amount(held)} {symbol}, "
                    f"fee is {_format_amount(fee)}"
                )
            boa.env.set_balance(sender_address, fee + EIGHTEEN_DECIMALS // 10)
            log.info("fork mode: topped the sender up so the simulation can continue")
            log.error(
                f"for real, {sender_address} needs at least "
                f"{_format_amount(fee)} native on {chain}, plus gas"
            )

        log.h2("Approving the router")
        erc20.approve(router.address, amount, sender=sender_address)
        if fee_erc20:
            fee_erc20.approve(router.address, fee, sender=sender_address)

        log.h2("Sending")
        message_id = router.ccipSend(
            selector, message, value=0 if fee_erc20 else fee, sender=sender_address
        )
        message_id = (
            message_id.hex() if isinstance(message_id, bytes) else str(message_id)
        )
        if not message_id.startswith("0x"):
            message_id = f"0x{message_id}"

        log.h1(f"Message {message_id}")
        log.info(f"track it at https://ccip.chain.link/msg/{message_id}")
        log.info(
            f"{token} left on the source chain: "
            f"{_format_amount(erc20.balanceOf(sender_address))}"
        )


def _parse_amount(value):
    """Parse an 18-decimal token amount without binary floating point."""
    if not isinstance(value, str) or not TOKEN_AMOUNT_RE.fullmatch(value):
        raise ValueError(
            "invalid --amount: use a positive decimal with at most 18 decimal places; "
            "signs and scientific notation are not accepted"
        )

    whole_text, _, fraction_text = value.partition(".")
    if len(whole_text) > 78:
        raise ValueError("invalid --amount: value exceeds uint256")
    fraction = int(fraction_text.ljust(18, "0")) if fraction_text else 0
    amount = int(whole_text) * EIGHTEEN_DECIMALS + fraction
    if amount <= 0:
        raise ValueError("invalid --amount: value must be greater than zero")
    if amount > MAX_UINT256:
        raise ValueError("invalid --amount: value exceeds uint256")
    return amount


def _format_amount(value):
    whole, fraction = divmod(int(value), EIGHTEEN_DECIMALS)
    if not fraction:
        return str(whole)
    return f"{whole}.{fraction:018d}".rstrip("0")


def _validate_request(
    chain,
    to_chain,
    environment,
    token,
    receiver,
    fork,
    as_address,
    acknowledge_destination_control,
):
    config = CCIP[chain]
    remotes = tuple(config["REMOTE_CHAINS"])
    to_chain = to_chain or (remotes[0] if len(remotes) == 1 else "")
    if not to_chain or to_chain not in remotes:
        raise ValueError(
            f"invalid --to-chain {to_chain!r}: {chain} permits {list(remotes)}"
        )
    if chain not in CCIP[to_chain].get("REMOTE_CHAINS", ()):
        raise ValueError(f"CCIP lane {chain} -> {to_chain} is not reciprocal")
    if CCIP[chain]["CHAIN_SELECTOR"] == CCIP[to_chain]["CHAIN_SELECTOR"]:
        raise ValueError(f"CCIP lane {chain} -> {to_chain} reuses a chain selector")
    if not ENVIRONMENT_RE.fullmatch(environment) or ".." in environment:
        raise ValueError("invalid --environment")
    if not token:
        raise ValueError("invalid --token")
    if as_address and not fork:
        raise ValueError("--as-address is fork-only")
    if fork and not as_address:
        raise ValueError(
            "--as-address is required in fork mode; private keys are never loaded"
        )
    if acknowledge_destination_control and not fork:
        raise ValueError("--acknowledge-destination-control is fork-only")
    if fork and not acknowledge_destination_control:
        raise ValueError(
            "--acknowledge-destination-control is required in fork mode; "
            "it records an operator assertion only and is not ownership proof"
        )
    for option, address in (("--as-address", as_address), ("--receiver", receiver)):
        if address and (not is_address(address) or int(address, 16) == 0):
            raise ValueError(
                f"invalid {option}: expected a nonzero 20-byte EVM address"
            )
    return to_chain


def _select_sender(fork, as_address, *, source_chain, destination_chain, receiver):
    if not fork:
        require_ccip_live_send_evidence(source_chain, destination_chain, receiver)
        raise ValueError(
            "CCIP_LIVE_SIGNER_UNBOUND: live submission is disabled because no "
            "reviewed signer or Safe transaction backend is bound; use --fork "
            "--as-address for preflight, or separately authorize and implement a backend"
        )
    return to_checksum_address(as_address)


def _rpc_result(rpc_url, method, params):
    if not rpc_url.startswith(("http://", "https://")):
        raise ValueError("CCIP RPC verification requires an HTTP(S) URL")
    payload = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    ).encode()
    rpc_request = request.Request(
        rpc_url,
        data=payload,
        headers={"content-type": "application/json"},
        method="POST",
    )
    with request.urlopen(rpc_request, timeout=15) as response:
        result = json.loads(response.read())
    if "error" in result or "result" not in result:
        raise ValueError(f"RPC did not return {method}")
    return result["result"]


def _read_chain_id(rpc_url):
    return _rpc_result(rpc_url, "eth_chainId", [])


def _read_code(rpc_url, address):
    return _rpc_result(rpc_url, "eth_getCode", [address, "latest"])


def _require_zero_gas_code_empty_destination(rpc_url, receiver):
    """Require no current destination bytecode for a zero-gas CCIP message."""
    # Code emptiness neither proves that an EOA controls this address nor rules
    # out future deployment (for example via CREATE2). Reject the reserved
    # low-address/precompile range separately from the bytecode check.
    if int(receiver, 16) <= 0xFFFF:
        raise ValueError(
            "CCIP_ZERO_GAS_DESTINATION_RESERVED_ADDRESS: destination is in the "
            f"reserved low-address range: {receiver}"
        )
    code = _read_code(rpc_url, receiver)
    if not isinstance(code, str) or code.lower() != "0x":
        raise ValueError(
            "CCIP_ZERO_GAS_DESTINATION_CODE_NOT_EMPTY: destination eth_getCode must "
            f"be 0x for {receiver}, got {code!r}"
        )


def _fee_balance_is_insufficient(held, fee, *, pays_in_erc20):
    """ERC-20 fees may consume the exact balance; native fees still need gas."""
    return held < fee if pays_in_erc20 else held <= fee


def _manifest_token(manifest, token, chain, environment):
    try:
        record = manifest[token]
    except KeyError:
        raise ValueError(
            f"manifest {chain}/{environment} has no contract named {token!r}"
        ) from None
    address = record.get("address")
    source = record.get("file")
    if not isinstance(address, str) or not is_address(address) or int(address, 16) == 0:
        raise ValueError(
            f"manifest {chain}/{environment} {token} has an invalid address"
        )
    if not isinstance(source, str) or not source or not (ROOT / source).is_file():
        raise ValueError(
            f"manifest {chain}/{environment} {token} has no loadable source"
        )
    return record


def _fee_token(chain, fee_token):
    """
    None means the native coin (paid as msg.value), otherwise the erc20 to pay the fee in.
    """
    if fee_token.lower() in ("", "native", "eth"):
        return None

    address = CCIP[chain].get(fee_token.upper(), fee_token)
    assert is_address(address) and int(address, 16) != 0, (
        f"unknown fee token {fee_token} on {chain}"
    )
    return boa.loads_abi(
        '[{"type":"function","name":"approve","stateMutability":"nonpayable",'
        '"inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],'
        '"outputs":[{"name":"","type":"bool"}]},'
        '{"type":"function","name":"balanceOf","stateMutability":"view",'
        '"inputs":[{"name":"account","type":"address"}],"outputs":[{"name":"","type":"uint256"}]},'
        '{"type":"function","name":"symbol","stateMutability":"view",'
        '"inputs":[],"outputs":[{"name":"","type":"string"}]}]',
        name="FeeToken",
    ).at(to_checksum_address(address))


def _manifest(chain, environment):
    from scripts.utils import json_file

    filename = MIGRATION_HISTORY_DIR / chain / environment / "current-manifest.json"
    if not filename.is_file():
        raise ValueError(f"no current manifest for {chain}/{environment}")
    return json_file.load(filename)["contracts"]


if __name__ == "__main__":
    cli()
