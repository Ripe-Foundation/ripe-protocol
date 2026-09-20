"""Pinned Boa fork whose upstream transport permits reads only."""
from contextlib import contextmanager
import boa
from boa.environment import Env
from boa.rpc import EthereumRPC
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class ReadOnlyRPC(EthereumRPC):
    ALLOWED = {"eth_chainId", "eth_getBlockByNumber", "eth_getCode", "eth_getBalance", "eth_getStorageAt", "eth_getTransactionCount", "eth_getProof", "eth_call"}

    def __init__(self, url):
        super().__init__(url)
        retry = Retry(total=6, backoff_factor=1, status_forcelist=[429, 502, 503, 504], allowed_methods=["POST"])
        self._session.mount("https://", HTTPAdapter(max_retries=retry))
        self._session.mount("http://", HTTPAdapter(max_retries=retry))

    def fetch(self, method, params):
        if method not in self.ALLOWED:
            raise RuntimeError("FORK_UPSTREAM_WRITE_FORBIDDEN:" + method)
        return super().fetch(method, params)

    def fetch_multi(self, payloads):
        if any(method not in self.ALLOWED for method, _ in payloads):
            raise RuntimeError("FORK_UPSTREAM_WRITE_FORBIDDEN")
        return super().fetch_multi(payloads)


@contextmanager
def readonly_fork(url, block):
    env = Env()
    env.fork_rpc(ReadOnlyRPC(url), block_identifier=block)
    with boa.set_env(env):
        yield env
