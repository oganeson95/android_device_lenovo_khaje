#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Regenerate vendor makefiles with the same LineageOS API and unchanged pinned blobs."""
from pathlib import Path
import importlib.util
import sys

device = Path(__file__).resolve().parent
sys.path.insert(0, str(device))
from stock_source import verify_vendor


def main():
    if len(sys.argv) != 1:
        raise SystemExit('Usage: setup-makefiles.py')
    verify_vendor(device.parents[2] / 'vendor' / 'lenovo' / 'khaje' / 'proprietary')
    spec = importlib.util.spec_from_file_location('khaje_extract_files', device / 'extract-files.py')
    entry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(entry)
    sys.argv = [str(device / 'setup-makefiles.py'), '--regenerate_makefiles']
    entry.ExtractUtils.device(entry.module).run()


if __name__ == '__main__':
    main()
