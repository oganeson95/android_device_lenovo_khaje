#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""LineageOS 22.2 extract-utils entry point; accepts only the verified local stage."""
from pathlib import Path
import sys

DEVICE = Path(__file__).resolve().parent
ANDROID_ROOT = DEVICE.parents[2]
sys.path.insert(0, str(ANDROID_ROOT / 'tools' / 'extract-utils'))

try:
    from extract_utils.main import ExtractUtils
    from extract_utils.fixups_blob import blob_fixup
    from extract_utils.module import ExtractUtilsModule
except ModuleNotFoundError as exc:
    raise SystemExit('Missing LineageOS lineage-22.2 tools/extract-utils checkout: ' + str(exc))

def lib_fixup_protobuf_vendorcompat(lib: str, partition: str, *args, **kwargs):
    return f'{lib}-vendorcompat' if partition == 'vendor' else None


lib_fixups = {
    (
        'libprotobuf-cpp-full-3.9.1',
        'libprotobuf-cpp-lite-3.9.1',
    ): lib_fixup_protobuf_vendorcompat,
}


blob_fixups = {
    'vendor/bin/hw/vendor.lenovo.hardware.battery-service': blob_fixup()
        .add_needed('libbase_shim.so'),
}


module = ExtractUtilsModule(
    'khaje',
    'lenovo',
    lib_fixups=lib_fixups,
    blob_fixups=blob_fixups,
    namespace_imports=[
        'device/lenovo/khaje',
        'hardware/qcom/sm7250/display',
        'vendor/qcom/opensource/display',
    ],
    check_elf=True,
)


def main():
    from stock_source import verify_stage
    if len(sys.argv) != 2:
        raise SystemExit('Usage: extract-files.py <stage produced by prepare-stock.py>')
    stage = Path(sys.argv[1]).resolve()
    verify_stage(stage)
    sys.argv = [str(DEVICE / 'extract-files.py'), str(stage)]
    ExtractUtils.device(module).run()
    # extract-utils can return on a failed extraction; independently require every pin.
    from stock_source import verify_vendor
    verify_vendor(ANDROID_ROOT / 'vendor' / 'lenovo' / 'khaje' / 'proprietary')


if __name__ == '__main__':
    main()
