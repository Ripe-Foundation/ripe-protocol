"""
Bridge protocol tokens across a CCIP lane, straight through the router.

Transporter only lists tokens Chainlink has onboarded into its UI, so a self served
token like RIPE has to call `Router.ccipSend()` itself. This does that: quote the fee,
approve the router, send, and print the message id to follow on the CCIP explorer.

    python -m scripts.ccip_send --chain base-sepolia --amount 10
    python -m scripts.ccip_send --chain base-sepolia --amount 10 --fork   # dry run
"""

import os

import boa
import click
import dotenv

from config.Ccip import CCIP
from scripts.utils import ccip, log
from scripts.utils.migration_helpers import get_account

dotenv.load_dotenv()

MIGRATION_HISTORY_DIR = "./migration_history"
EIGHTEEN_DECIMALS = 10**18


@click.command()
@click.option("--chain", default="base-sepolia", help="Chain to send from.")
@click.option("--to-chain", default="", help="Chain to send to. Defaults to the only remote chain.")
@click.option("--environment", default="v2", help="Manifest environment to read addresses from.")
@click.option("--token", default="RipeToken", help="Contract name in the manifest.")
@click.option("--amount", default="1", help="Amount to bridge, in whole tokens.")
@click.option("--receiver", default="", help="Recipient on the destination chain. Defaults to the sender.")
@click.option("--account", default="DEPLOYER", help="Account name, reads <NAME>_PRIVATE_KEY.")
@click.option("--rpc", default="", help="RPC url. Defaults to the alchemy url for the chain.")
@click.option("--fork", is_flag=True, default=False, help="Simulate against a fork, broadcasting nothing.")
@click.option("--as-address", default="", help="Fork only: simulate as this address, no key needed.")
@click.option("--fee-token", default="native", help="What to pay the CCIP fee in: native or link.")
def cli(chain, to_chain, environment, token, amount, receiver, account, rpc, fork, as_address, fee_token):
    """Send tokens across a CCIP lane."""
    config = CCIP[chain]
    to_chain = to_chain or config["REMOTE_CHAINS"][0]
    rpc = rpc or f"https://{chain}.g.alchemy.com/v2/{os.environ.get('WEB3_ALCHEMY_API_KEY')}"

    assert not as_address or fork, "--as-address only makes sense with --fork"

    sender = get_account(account) if not as_address else None
    sender_address = as_address or sender.address
    receiver = receiver or sender_address
    amount = int(float(amount) * EIGHTEEN_DECIMALS)

    log.h1(f"Bridging {token} from {chain} to {to_chain}")

    env = boa.fork(rpc) if fork else boa.set_network_env(rpc)
    with env:
        if fork:
            boa.env.eoa = sender_address
            log.info("fork mode: nothing will be broadcast")
        else:
            boa.env.add_account(sender)

        manifest = _manifest(chain, environment)[token]
        erc20 = boa.load_partial(manifest["file"]).at(manifest["address"])
        router = ccip.router(chain)
        selector = CCIP[to_chain]["CHAIN_SELECTOR"]

        log.info(f"token    {erc20.address}")
        log.info(f"router   {router.address}")
        log.info(f"sender   {sender_address}")
        log.info(f"receiver {receiver} on {to_chain} ({selector})")
        log.info(f"amount   {amount / EIGHTEEN_DECIMALS}")

        balance = erc20.balanceOf(sender_address)
        assert balance >= amount, (
            f"{sender_address} holds {balance / EIGHTEEN_DECIMALS} {token}, needs {amount / EIGHTEEN_DECIMALS}"
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
        held = fee_erc20.balanceOf(sender_address) if fee_erc20 else boa.env.get_balance(sender_address)
        log.info(f"fee      {fee / EIGHTEEN_DECIMALS} {symbol}")
        log.info(f"balance  {held / EIGHTEEN_DECIMALS} {symbol}")

        if fork and held <= fee:
            if fee_erc20:
                raise Exception(f"sender holds {held / EIGHTEEN_DECIMALS} {symbol}, fee is {fee / EIGHTEEN_DECIMALS}")
            boa.env.set_balance(sender_address, fee + EIGHTEEN_DECIMALS // 10)
            log.info("fork mode: topped the sender up so the simulation can continue")
            log.error(
                f"for real, {sender_address} needs at least "
                f"{fee / EIGHTEEN_DECIMALS} native on {chain}, plus gas"
            )
        else:
            assert held > fee, f"not enough {symbol} to cover the {fee / EIGHTEEN_DECIMALS} fee"

        log.h2("Approving the router")
        erc20.approve(router.address, amount, sender=sender_address)
        if fee_erc20:
            fee_erc20.approve(router.address, fee, sender=sender_address)

        log.h2("Sending")
        message_id = router.ccipSend(
            selector, message, value=0 if fee_erc20 else fee, sender=sender_address
        )
        message_id = message_id.hex() if isinstance(message_id, bytes) else str(message_id)
        if not message_id.startswith("0x"):
            message_id = f"0x{message_id}"

        log.h1(f"Message {message_id}")
        log.info(f"track it at https://ccip.chain.link/msg/{message_id}")
        log.info(f"{token} left on the source chain: {erc20.balanceOf(sender_address) / EIGHTEEN_DECIMALS}")


def _fee_token(chain, fee_token):
    """
    None means the native coin (paid as msg.value), otherwise the erc20 to pay the fee in.
    """
    if fee_token.lower() in ("", "native", "eth"):
        return None

    address = CCIP[chain].get(fee_token.upper(), fee_token)
    assert address.startswith("0x"), f"unknown fee token {fee_token} on {chain}"
    return boa.loads_abi(
        '[{"type":"function","name":"approve","stateMutability":"nonpayable",'
        '"inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],'
        '"outputs":[{"name":"","type":"bool"}]},'
        '{"type":"function","name":"balanceOf","stateMutability":"view",'
        '"inputs":[{"name":"account","type":"address"}],"outputs":[{"name":"","type":"uint256"}]},'
        '{"type":"function","name":"symbol","stateMutability":"view",'
        '"inputs":[],"outputs":[{"name":"","type":"string"}]}]',
        name="FeeToken",
    ).at(address)


def _manifest(chain, environment):
    from scripts.utils import json_file

    filename = os.path.join(MIGRATION_HISTORY_DIR, chain, environment, "current-manifest.json")
    return json_file.load(filename)["contracts"]


if __name__ == "__main__":
    cli()
