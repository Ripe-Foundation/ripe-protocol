import pytest

def filter_logs(contract, event_name, _strict=False):
    return [e for e in contract.get_logs(strict=_strict) if type(e).__name__ == event_name]
