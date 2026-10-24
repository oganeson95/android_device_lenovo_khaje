# Lenovo TB331FC / khaje — experimental bring-up

Target branch: `lineage-22.2` (Android 15). This is an incomplete, untested device
configuration. It is not a complete, stable, bootable, or supported ROM.

`BoardConfig.mk` intentionally stops configuration with an explicit error until
the blockers in `docs/next-build-blockers.md` are resolved. The error is a bring-up
guard, not evidence that every omitted variable is mandatory upstream. No build
or image assembly has been attempted.

The stock kernel candidate is the unmodified `.572` `boot_a` payload:
`5.15.149-android13-8-00014-gb219e2d2bfe5-ab12114171`. The original `.680` kernel
is absent. The runtime capture reports the same banner and 296 loaded module names; exact binary identity and LineageOS compatibility remain **UNKNOWN**.
No external kernel or root patch is integrated.

DT handling preserves the complete `.680` B `vendor_boot` and `dtbo` containers.
Runtime reports slot B / DTB 0 / DTBO 3; B base 0 differs from A base 0.
No individual DTB or overlay is selected or rebuilt. Container identity in the
executed system is strongly supported, pending binary readback; this does not
validate the final Lineage kernel/modules/vendor combination.

The 13 originals remain outside this tree. `configs/stock-source.json` fixes
their identity and distinguishes dump lengths from confirmed GPT limits.
Prebuilt copies are reproducible local outputs and ignored by Git.

## Selective extraction

Run these preparation scripts with Python 3 on the firmware workstation or in
the source checkout. `<stock-root>` contains the audited original `super.img`
and boot images. `<new-stage>` must not already exist.

```text
python3 device/lenovo/khaje/prepare-prebuilts.py --stock-root <stock-root>
python3 device/lenovo/khaje/prepare-stock.py --stock-root <stock-root> --output <new-stage>
```

The second script reads raw LP view 1 / `vendor_b` directly, resolves ext4 paths
and inodes and verifies all selected SHA-256 values before writing the stage.
It extracts only the 78 pinned files in `proprietary-files.txt`. The stage is a
source of verified `.680` file content, not a reconstructed runtime.

In a Linux `lineage-22.2` checkout with its official `tools/extract-utils` and
host tools present, these entry points produce/regenerate vendor makefiles:

```text
python3 device/lenovo/khaje/extract-files.py <new-stage>
python3 device/lenovo/khaje/setup-makefiles.py
```

Extraction accepts only a prepared local stage, never a default ADB source,
network URL, whole-vendor copy, or hash-changing mode. ELF checks remain enabled;
no blob fixups are applied. `setup-makefiles.py` requires the selected pinned
blobs to exist first. The vendor tree has not been generated in this phase.

`configs/blob-plan.json` records each source, SHA-256/SHA-1, function, selection
reason and dependency edge. Provenance is **CONFIRMED**; the initial selection
and its completeness are **INFERRED/UNKNOWN**. Known AOSP/platform/interface and
other source-provider candidates are excluded from automatic copying. Exact
module/ABI availability must still be checked in the chosen source checkout.

No empty rootdir, overlay or sepolicy placeholders are supplied. The preserved
vendor_boot carries the original first-stage fstab; framework/vendor VINTF,
SELinux, source HALs, runtime dlopen/config dependencies and OTA/AVB integration
remain explicitly incomplete.

Runtime integration: stock logical density 240 and Wi-Fi tablet product classification; see docs/runtime-audit.md. All original 69 source-provider pairs are located in stock; the expanded set has 71 pairs still requiring Lineage module/ABI/namespace validation.
