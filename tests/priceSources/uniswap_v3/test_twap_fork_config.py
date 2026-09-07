import pytest
from .fork_worker import configuration,pin


@pytest.mark.parametrize('env',[{}, {'RIPE_TWAP_PIN_MODE':'automatic'}, {'RIPE_TWAP_PIN_MODE':'pinned','RIPE_TWAP_BLOCK':'1'}, {'RIPE_TWAP_PIN_MODE':'pinned','RIPE_TWAP_BLOCK_HASH':'0x'+'ab'*32}, {'RIPE_TWAP_PIN_MODE':'fresh','RIPE_TWAP_BLOCK':'1'}, {'RIPE_TWAP_PIN_MODE':'fresh','RIPE_TWAP_BLOCK_HASH':'0x'+'ab'*32}])
def test_fork_modes_fail_closed_on_incomplete_or_mixed_pins(env):
    with pytest.raises(ValueError):configuration({'RIPE_TWAP_RPC_URL':'https://example.invalid',**env})


def test_fork_provider_selection_is_explicit():
    base={'RIPE_TWAP_RPC_URL':'https://fresh.invalid','RIPE_TWAP_ARCHIVE_RPC_URL':'https://archive.invalid'}
    assert configuration({**base,'RIPE_TWAP_PIN_MODE':'fresh'})[1]=='https://fresh.invalid'
    pinned={**base,'RIPE_TWAP_PIN_MODE':'pinned','RIPE_TWAP_BLOCK':'57037442','RIPE_TWAP_BLOCK_HASH':'0x'+'ab'*32}
    assert configuration(pinned)[1]=='https://archive.invalid'
    del pinned['RIPE_TWAP_ARCHIVE_RPC_URL']
    assert configuration(pinned)[1]=='https://fresh.invalid'


@pytest.mark.parametrize('error,expected',[({'code':-32000,'message':'metadata is not found'},'infrastructure'),({'code':3,'message':'execution reverted: OLD'},'revert')])
def test_rpc_state_failure_is_distinct_from_real_call_revert(error,expected):
    from types import SimpleNamespace
    from .fork_worker import Rpc,InfrastructureError,HistoricalCallRevert
    rpc=Rpc('https://example.invalid')
    rpc.session=SimpleNamespace(post=lambda *a,**kw:SimpleNamespace(status_code=200,json=lambda:{'error':error}))
    with pytest.raises(InfrastructureError if expected=='infrastructure' else HistoricalCallRevert):
        rpc.call('eth_call',[])


def test_partial_raw_calls_survive_provider_loss():
    from .fork_worker import collect,InfrastructureError,VECTORS
    class LostState:
        def eth_call(self,address,signature,*args):
            if signature=='latestRoundData()':raise InfrastructureError('state pruned')
            return '0x'+(18).to_bytes(32,'big').hex()
    raw={}
    with pytest.raises(InfrastructureError):collect(LostState(),VECTORS['assets'][0],1800,{'block':1},raw)
    assert set(raw)=={'assetDecimals','wethDecimals','anchorDecimals'}
