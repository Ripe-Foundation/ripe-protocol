"""Atomic, sanitized fork evidence and bounded subprocess execution (no EVM)."""
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import unquote,urlsplit


def rpc_endpoints(env):
    return tuple(env[key] for key in ('RIPE_TWAP_RPC_URL','RIPE_TWAP_ARCHIVE_RPC_URL') if env.get(key))


def sanitized(message,rpc_urls=(),limit=600):
    text=str(message)
    # Providers may report a bare host/path, without the URL scheme or labels.
    fragments=set()
    for url in rpc_urls:
        fragments.update((url,unquote(url)))
        try:parts=urlsplit(url)
        except ValueError:continue
        fragments.update((parts.netloc,parts.hostname,parts.path,unquote(parts.path),parts.query,unquote(parts.query)))
    for fragment in sorted(fragments-{None,'','/'},key=len,reverse=True):
        text=re.sub(re.escape(fragment),'<rpc-endpoint>',text,flags=re.I)
    # requests/urllib3 split endpoints into HTTPSConnectionPool(host=...) and
    # "Max retries exceeded with url: /v2/API_KEY". Both fragments are private.
    text=re.sub(r'''(?i)\bhost\s*=\s*(?:'[^']*'|"[^"]*"|[^,\s)]+)''','host=<rpc-host>',text)
    text=re.sub(r'''(?i)\burl\s*[:=]\s*(?:'[^']*'|"[^"]*"|[^\s,)]+)''','url=<rpc-path>',text)
    text=re.sub(r'https?://[^\s\]\[<>\"\')]+','<rpc-url>',text,flags=re.I)
    text=re.sub(r'(?<!\w)/(?:Users|home|private|tmp|var|opt)/[^\s\]\[<>\"\')]+','<local-path>',text)
    text=re.sub(r'(?i)\b(Bearer)\s+[^\s,;]+',r'\1 <redacted>',text)
    text=re.sub(r'(?i)\b(api[_-]?key|token|password|authorization)\s*[=:]\s*[^\s,;]+',r'\1=<redacted>',text)
    return text if limit is None else text[:limit]


def exception_reason(exc,rpc_urls=()):
    # BoaError.__str__ includes local source paths, storage and full traces.
    trace=getattr(exc,'stack_trace',None)
    try:reason=getattr(trace,'dev_reason',None) if trace is not None else None
    except (AttributeError,IndexError):reason=None
    return sanitized(f'{type(exc).__name__}: {reason or str(exc)}',rpc_urls)


def atomic_save(path,data):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.'+path.name+'-',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as stream:
            json.dump(data,stream,indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)


def initial_results(mode,assets,laboratory):
    return {'mode':mode,'pin':None,'stage':'initializing','header_consistency':'unverified',
            'cases':[{'asset':a,'window':w,'pin':None,'laboratory':laboratory,
                      'raw':{},'stage':'pending','status':'unverified','reason':'not started'}
                     for a in assets for w in (1800,3600,14400)]}


def failure(case,exc,infrastructure=False,rpc_urls=()):
    case.update(status='unverified' if infrastructure else 'failed',
                behavior_passed=False,reason=exception_reason(exc,rpc_urls))


def require_complete(data):
    if data['stage']!='complete':
        raise RuntimeError('fork worker did not complete: '+data['stage']+'; partial evidence retained')
    return data


def run_worker(command,*,cwd,env,timeout=600,initial):
    """Retain timeout evidence and fail incomplete worker execution."""
    path=Path(env['RIPE_TWAP_FORK_OUTPUT'])
    atomic_save(path,initial)
    try:
        result=subprocess.run(command,cwd=cwd,env=env,text=True,capture_output=True,timeout=timeout)
    except subprocess.TimeoutExpired:
        data=json.loads(path.read_text())
        data.update(stage='timeout',reason=f'worker deadline exceeded ({timeout}s)')
        for case in data['cases']:
            if case.get('header_consistency')=='matched' and case['status'] in ('passed','unavailable','failed'):
                continue
            case['observed_status']=case['status']
            case['observed_reason']=case.get('reason','')
            case.update(status='unverified',behavior_passed=False,
                        reason=f'worker deadline exceeded ({timeout}s) during '+case['stage'])
        atomic_save(path,data)
        return require_complete(data)
    if result.returncode:
        # Sanitize before truncating, so truncation cannot expose a key fragment.
        # Bound streams separately and put the fatal stderr tail first.
        urls=rpc_endpoints(env)
        stderr=sanitized(result.stderr,urls,limit=None)[-600:]
        stdout=sanitized(result.stdout,urls,limit=None)[-300:]
        raise RuntimeError(f'fork worker exited {result.returncode}; stderr: {stderr}; stdout: {stdout}')
    data=json.loads(path.read_text())
    return require_complete(data)
