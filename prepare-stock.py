#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Prepare only selected .680 files directly from immutable super's audited LP view."""
from pathlib import Path
import argparse
import hashlib
import json
from stock_source import DEVICE, LpPartition, Ext4, plan, proof, sha256_file, verify_stage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='new directory; never overwritten')
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise SystemExit('Output must be a new directory; no cleanup or overwrite is performed')
    source = args.stock_root.resolve() / 'super.img'
    expected = proof()
    digest = sha256_file(source)
    if digest != expected['original_images']['super.img']['sha256']:
        raise SystemExit('super SHA-256 differs from the audited source; refusing to extract')
    partition = LpPartition(source, 1, 'vendor_b', expected['lp_metadata_view_1_sha256'])
    payloads = []
    try:
        fs = Ext4(partition)
        for entry in plan()['files']:
            if entry['source_partition'] != 'vendor_b' or not entry['path'].startswith('vendor/'):
                raise ValueError('This extractor only accepts selected vendor_b files')
            relative = entry['path'].removeprefix('vendor/')
            inode = fs.resolve(relative)
            data = fs.content(inode)
            if inode != entry['inode'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
                raise ValueError('Source inode/hash differs: ' + entry['path'])
            payloads.append((entry['path'], data))
    finally:
        partition.close()
    output.mkdir(parents=True)
    for relative, data in payloads:
        dest = output / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    receipt = {'super_sha256': digest, 'metadata_view': 1, 'partition': 'vendor_b',
               'version': 'ZUXOS_1.1.10.680_251219_PRC', 'runtime_reconstructed': False,
               'blob_plan_sha256': sha256_file(DEVICE / 'configs/blob-plan.json'),
               'files': len(payloads)}
    (output / 'khaje-source-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    verify_stage(output)
    print(f'Prepared and verified {len(payloads)} selected files; originals read only')


if __name__ == '__main__':
    main()
