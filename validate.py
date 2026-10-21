"""Offline replay entrypoint; references are never regenerated here."""
import argparse
import os
import subprocess
from v1_1.archive import ROOT, check_layer, check_legacy_pins, legacy_checks

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--plant',choices=['estimate','drop','weight','grid'])
    parser.add_argument('--out',help='JSON comparison audit destination')
    args=parser.parse_args()
    check_legacy_pins()
    check_layer()
    only=os.environ.get('ARCHIVE_V1_1_ONLY')=='1'
    if only:
        print('ARCHIVE_V1_1_ONLY=1: original full replay skipped; v1.0 hashes checked',flush=True)
    else:
        legacy_checks(['replay'])
        subprocess.run(['node','v1_1/exact/gosh/validate/replay-numeric.cjs'],cwd=ROOT,check=True)
    cmd=['node','v1_1/exact/replay.cjs']
    if args.plant: cmd+=['--plant',args.plant]
    if args.out: cmd+=['--out',args.out]
    return subprocess.run(cmd,cwd=ROOT).returncode

if __name__ == '__main__':
    raise SystemExit(main())
