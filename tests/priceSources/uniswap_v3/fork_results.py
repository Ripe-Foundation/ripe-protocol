"""Atomic, sanitized fork evidence and bounded subprocess execution (no EVM)."""
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


def sanitized(message):
    text=str(message)
    text=re.sub(r'https?://[^\s\]\[<>\"\')]+','<rpc-url>',text,flags=re.I)
    text=re.sub(r'(?<!\w)/(?:Users|home|private|tmp|var|opt)/[^\s\]\[<>\"\')]+','<local-path>',text)
    text=re.sub(r'(?i)\b(Bearer)\s+[^\s,;]+',r'\1 <redacted>',text)
    text=re.sub(r'(?i)\b(api[_-]?key|token|password|authorization)\s*[=:]\s*[^\s,;]+',r'\1=<redacted>',text)
    return text[:600]


def exception_reason(exc):
    # BoaError.__str__ includes local source paths, storage and full traces.
    # Prefer its concise developer reason, then sanitize a plain exception.
    trace=getattr(exc,'stack_trace',None)
    try:reason=getattr(trace,'dev_reason',None) if trace is not None else None
    except (AttributeError,IndexError):reason=None
    return sanitized(f'{type(exc).__name__}: {reason or str(exc)}')


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


def failure(case,exc,infrastructure=False):
    case.update(status='unverified' if infrastructure else 'failed',
                behavior_passed=False,reason=exception_reason(exc))


def run_worker(command,*,cwd,env,timeout=600,initial):
    """On timeout retain verified completed cases and every saved partial input."""
    path=Path(env['RIPE_TWAP_FORK_OUTPUT'])
    # Overwrite any previous run before starting a new worker.
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
        return data
    if result.returncode:
        raise RuntimeError(sanitized(f'fork worker exited {result.returncode}: {result.stdout[-1500:]} {result.stderr[-1500:]}'))
    data=json.loads(path.read_text())
    assert data['stage']=='complete', 'worker exited without completing or reporting a deadline'
    return data
