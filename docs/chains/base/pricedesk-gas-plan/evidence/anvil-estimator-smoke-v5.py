import json, os, subprocess, time
from pathlib import Path
from datetime import datetime, timezone
import requests

# Portability edit: only the generated output location differs from the capture.
review_output = Path(os.environ['PRICEDESK_REVIEW_OUTPUT'])
review_output.mkdir(parents=True, exist_ok=True)
out = review_output / 'pricedesk-v5-anvil-smoke.json'
result = {'checked_at': datetime.now(timezone.utc).isoformat(), 'scope': 'Local Anvil synthetic estimator/state smoke only; no Base fork or production qualification.'}
process = None
try:
    process = subprocess.Popen([os.environ.get('ANVIL', 'anvil'), '--host', '127.0.0.1', '--port', '18577', '--accounts', '0', '--silent'], env={'PATH': os.environ['PATH']}, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    def rpc(method, params):
        response = requests.post('http://127.0.0.1:18577', json={'jsonrpc':'2.0', 'id':1, 'method':method, 'params':params}, timeout=3)
        payload = response.json()
        if 'error' in payload: raise RuntimeError(str(payload['error']))
        return payload['result']
    for attempt in range(30):
        if process.poll() is not None:
            raise RuntimeError('Anvil exited: ' + process.stderr.read()[:1200])
        try:
            result['chain_id'] = int(rpc('eth_chainId',[]),16)
            break
        except requests.RequestException:
            time.sleep(0.1)
    assert result.get('chain_id') == 31337
    result['client_version'] = rpc('web3_clientVersion', [])
    sender='0x000000000000000000000000000000000000beef'
    target='0x000000000000000000000000000000000000dead'
    rpc('anvil_setBalance',[sender,hex(10**20)])
    rpc('anvil_impersonateAccount',[sender])
    rpc('anvil_setCode',[target,'0x600160005500'])
    tx={'from':sender,'to':target,'value':'0x0','data':'0x'}
    snapshot=rpc('evm_snapshot',[])
    estimate=int(rpc('eth_estimateGas',[tx]),16)
    estimates=[]
    for limit in [estimate,100000]:
        assert rpc('evm_revert',[snapshot])
        snapshot=rpc('evm_snapshot',[])
        txhash=rpc('eth_sendTransaction',[dict(tx,gas=hex(limit))])
        receipt=rpc('eth_getTransactionReceipt',[txhash])
        state=rpc('eth_getStorageAt',[target,'0x0','latest'])
        estimates.append({'gas_limit':limit,'status':receipt['status'],'gas_used':int(receipt['gasUsed'],16),'storage_slot_0':state})
    assert estimates[0]['status']==estimates[1]['status']=='0x1'
    assert int(estimates[0]['storage_slot_0'],16)==int(estimates[1]['storage_slot_0'],16)==1
    result.update(status='passed',estimate=estimate,trials=estimates)
except Exception as error:
    result.update(status='blocked',error=str(error))
finally:
    if process is not None and process.poll() is None:
        process.terminate()
        try:process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill();process.wait(timeout=3)
    out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
