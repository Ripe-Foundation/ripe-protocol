#!/usr/bin/env python3
"""Losslessly attach a complete fork JSON to a GitHub PR body without a commit hash cycle."""
import argparse
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path
import re

BEGIN='<!-- TWAP_FORK_EVIDENCE_BEGIN -->'
END='<!-- TWAP_FORK_EVIDENCE_END -->'
LIMIT=2_000_000


def pack(raw):
    data=json.loads(raw)
    if len(raw)>LIMIT or data.get('stage')!='complete' or data.get('header_consistency')!='matched':
        raise ValueError('only complete, header-verified fork evidence can be attached')
    if len(data['cases'])!=12 or any(c['status'] not in ('qualified','expected_rejected') for c in data['cases']):
        raise ValueError('fork evidence must have twelve verified outcomes')
    envelope={'encoding':'gzip+base64','revision':data['code_revision'],
              'sha256':hashlib.sha256(raw).hexdigest(),
              'data':base64.b64encode(gzip.compress(raw,mtime=0)).decode()}
    return ('<details>\n<summary>Complete final-head fork JSON (lossless; extract with scripts/twap_fork_evidence.py)</summary>\n\n'
            +BEGIN+'\n```json\n'+json.dumps(envelope,indent=2)+'\n```\n'+END+'\n</details>\n')


def unpack(report):
    match=re.search(re.escape(BEGIN)+r'\s*```json\s*(.*?)\s*```\s*'+re.escape(END),report,re.S)
    if not match:raise ValueError('missing fork evidence attachment')
    envelope=json.loads(match[1])
    if envelope['encoding']!='gzip+base64':raise ValueError('unsupported evidence encoding')
    compressed=base64.b64decode(envelope['data'],validate=True)
    with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:raw=stream.read(LIMIT+1)
    if len(raw)>LIMIT or hashlib.sha256(raw).hexdigest()!=envelope['sha256']:
        raise ValueError('fork evidence digest mismatch')
    if json.loads(raw)['code_revision']!=envelope['revision']:
        raise ValueError('fork evidence revision mismatch')
    return raw


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('pack','unpack'))
    parser.add_argument('input',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.mode=='pack':
        result=pack(args.input.read_bytes()).encode()
    else:
        if not args.output:parser.error('unpack requires --output')
        result=unpack(args.input.read_text())
    if args.output:args.output.write_bytes(result)
    else:print(result.decode(),end='')


if __name__=='__main__':main()
