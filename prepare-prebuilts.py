#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Copy audited candidates byte-for-byte; kernel .572 and runtime-aligned B containers."""
from pathlib import Path
import argparse
import hashlib
import shutil
import struct
from stock_source import DEVICE, proof, sha256_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock-root', type=Path, required=True)
    args = parser.parse_args()
    expected = proof()
    root = args.stock_root.resolve()
    vendor_version = expected.get('prebuilt_vendor_version', '.572')
    slot = 'b' if vendor_version == '.680' else 'a'
    for name in ['boot_a.img', 'vendor_boot_' + slot + '.img', 'dtbo_' + slot + '.img']:
        if sha256_file(root / name) != expected['original_images'][name]['sha256']:
            raise SystemExit('Changed source image: ' + name)
    with (root / 'boot_a.img').open('rb') as stream:
        header = stream.read(4096)
        if header[:8] != b'ANDROID!' or struct.unpack_from('<I', header, 40)[0] != 4:
            raise SystemExit('Unexpected boot header')
        kernel = stream.read(struct.unpack_from('<I', header, 8)[0])
    if hashlib.sha256(kernel).hexdigest() != expected['kernel_payload_sha256']:
        raise SystemExit('Changed stock kernel payload')
    files = [('stock_572/Image', None),
             ('stock_' + vendor_version.removeprefix('.') + '/vendor_boot.img', 'vendor_boot_' + slot + '.img'),
             ('stock_' + vendor_version.removeprefix('.') + '/dtbo.img', 'dtbo_' + slot + '.img')]
    for name, source in files:
        target = DEVICE / 'prebuilts' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        digest = expected['kernel_payload_sha256'] if source is None else expected['original_images'][source]['sha256']
        if target.exists():
            if target.is_symlink() or sha256_file(target) != digest:
                raise SystemExit('Refusing to overwrite a changed prebuilt: ' + str(target))
            continue
        if source is None:
            target.write_bytes(kernel)
        else:
            shutil.copyfile(root / source, target)
        if sha256_file(target) != digest:
            raise SystemExit('Copy verification failed: ' + str(target))
    print('Prepared unmodified .572 kernel and ' + vendor_version + ' full DT/ramdisk containers; Lineage compatibility UNKNOWN')


if __name__ == '__main__':
    main()
