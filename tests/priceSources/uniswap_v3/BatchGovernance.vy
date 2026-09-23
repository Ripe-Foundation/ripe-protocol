# @version 0.4.3
# Test-only atomic batch: like MultiSend, returned False is not a revert.
@external
def execute(targets: DynArray[address, 8], payloads: DynArray[Bytes[196], 8]) -> DynArray[Bytes[32], 8]:
    assert len(targets) == len(payloads)
    results: DynArray[Bytes[32], 8] = []
    for i: uint256 in range(len(targets), bound=8):
        results.append(raw_call(targets[i], payloads[i], max_outsize=32))
    return results
