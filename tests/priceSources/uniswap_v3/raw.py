"""Explicit synthetic ABI fixtures/fault injection, never gas stand-ins for V3.

Tiny immutable-return bytecode lets tests control *exact* ABI bytes, including
noncanonical values a typed Vyper mock cannot emit. No external compiler needed.
"""
import boa
from eth_utils import keccak


def selector(signature):
    return keccak(text=signature)[:4]


def word(value):
    if not isinstance(value, int):
        value = int(str(getattr(value, 'address', value)), 16)
    return (value % 2**256).to_bytes(32, 'big')


def words(*values):
    return b''.join(map(word, values))


def push(value, width=2):
    return bytes([0x5f + width]) + value.to_bytes(width, 'big')


def runtime(responses):
    """signature -> bytes or (bytes, burn_iterations); None exhausts all gas."""
    code = bytearray()
    jumps = []
    payloads = []
    for signature in responses:
        code.extend(b'\x5f\x35\x60\xe0\x1c\x63' + selector(signature) + b'\x14\x61')
        jumps.append(len(code))
        code.extend(b'\x00\x00\x57')
    code.extend(b'\x5f\x5f\xfd')
    for (signature, response), jump in zip(responses.items(), jumps):
        code[jump:jump+2] = len(code).to_bytes(2,'big')
        code.append(0x5b)
        if response is None:
            here = len(code)
            code.extend(b'\x5b' + push(here) + b'\x56')
            continue
        burn = 0
        if isinstance(response, tuple):
            response, burn = response
        if burn:
            code.extend(push(burn))
            loop = len(code)
            code.extend(b'\x5b\x60\x01\x90\x03\x80' + push(loop) + b'\x57\x50')
        # CODECOPY exactly N bytes then RETURN, including N=0/extra trailing bytes.
        data_pointer = len(code) + 4
        code.extend(push(len(response)) + push(0) + b'\x5f\x39' + push(len(response)) + b'\x5f\xf3')
        payloads.append((data_pointer, response))
    # Keep arbitrary return bytes after every JUMPDEST: bytes that resemble
    # PUSH opcodes must not hide later handlers from the EVM jump scanner.
    for pointer, response in payloads:
        code[pointer:pointer+2] = len(code).to_bytes(2, 'big')
        code.extend(response)
    return bytes(code)


class Raw:
    def __init__(self, responses=None, address=None):
        self.address = address or boa.env.generate_address()
        self.responses = responses or {}
        self.install()

    def install(self):
        boa.env.set_code(self.address, runtime(self.responses))

    def set(self, signature, data):
        self.responses[signature] = data
        self.install()


class Pool(Raw):
    def __init__(self, asset, quote, factory, tick=0, window=3600, liquidity=10**20):
        self.asset, self.quote, self.factory = asset, quote, factory
        a, q = sorted([asset.address, quote.address], key=lambda a:int(a,16))
        super().__init__({'factory()': word(factory), 'token0()': word(a), 'token1()': word(q), 'fee()': word(10000)})
        self.set_history(tick, window, liquidity)

    def set_history(self, tick=0, window=3600, liquidity=10**20, age=0, past=0, spl_past=0, cardinality=1000):
        # slot0 metadata is synthetic; historical accumulators may be frozen inputs.
        self.set('slot0()', words(2**96, 0, 0, cardinality, cardinality, 0, 1))
        self.set('liquidity()', word(liquidity))
        self.set('observations(uint256)', words((boa.env.timestamp-age)%2**32, 0, 0, 1))
        self.set('observe(uint32[])', words(64,160,2,past,past+tick*window,2,spl_past,spl_past+window*2**128//max(1,liquidity)))
