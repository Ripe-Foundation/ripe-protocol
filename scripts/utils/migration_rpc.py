"""Bounded read-only estimation retries for sequential live migrations."""

import time

from boa.rpc import RPC, RPCError

from scripts.utils import log


class MigrationRPC(RPC):
    def __init__(self, rpc):
        self.rpc = rpc

    @property
    def identifier(self):
        return self.rpc.identifier

    @property
    def name(self):
        return self.rpc.name

    def fetch(self, method, params):
        if method != "eth_estimateGas":
            # In particular, never retry a send or a receipt-side failure.
            return self.rpc.fetch(method, params)

        # Boa simulates against latest, but estimates against pending by default.
        # Sequential setup calls need the same mined state for both checks.
        params = [params[0], "latest"]
        for attempt in range(10):
            try:
                return self.rpc.fetch_uncached(method, params)
            except RPCError as exc:
                if exc.code != 3:
                    raise
                if attempt == 9:
                    # Avoid boa's bare AssertionError on local/RPC disagreement.
                    # Do not expose provider URLs or calldata from the RPC error.
                    raise RuntimeError(
                        "MIGRATION_GAS_ESTIMATE_REVERTED: latest-state estimation "
                        "failed 10 times; this transaction was not broadcast"
                    ) from None
                log.info("Gas estimate reverted; waiting 2s for RPC state "
                         f"({attempt + 1}/10, no transaction broadcast)")
                time.sleep(2)

    def fetch_uncached(self, method, params):
        if method == "eth_estimateGas":
            return self.fetch(method, params)
        return self.rpc.fetch_uncached(method, params)

    def fetch_multi(self, payloads):
        return self.rpc.fetch_multi(payloads)
