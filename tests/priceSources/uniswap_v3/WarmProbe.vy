# @version 0.4.3
@view
@external
def twice(target: address, data: Bytes[100]) -> (Bytes[65], Bytes[65]):
    first: Bytes[65] = raw_call(target, data, max_outsize=65, gas=1000000, is_static_call=True)
    second: Bytes[65] = raw_call(target, data, max_outsize=65, gas=1000000, is_static_call=True)
    return first, second
