# SPDX-License-Identifier: Apache-2.0
# Experimental stock-derived facts, not a complete or boot-tested board.
DEVICE_PATH := device/lenovo/khaje

# ELF/kernel architecture and stock userspace ABI list; variants remain UNKNOWN.
TARGET_ARCH := arm64
TARGET_CPU_ABI := arm64-v8a
TARGET_2ND_ARCH := arm
TARGET_2ND_CPU_ABI := armeabi-v7a
TARGET_2ND_CPU_ABI2 := armeabi
# TODO: TARGET_ARCH_VARIANT / TARGET_CPU_VARIANT and secondary variants.
# Do not confuse upstream fallback defaults with confirmed hardware values.

# Stock property ro.board.platform, not the product codename.
TARGET_BOARD_PLATFORM := bengal

BOARD_BOOT_HEADER_VERSION := 4
BOARD_KERNEL_PAGESIZE := 4096
TARGET_PREBUILT_KERNEL := $(DEVICE_PATH)/prebuilts/stock_572/Image

# Runtime reports slot B, DTB 0 / DTBO 3; B DTB 0 differs from A DTB 0.
# Preserve the complete .680 B containers and their stock selection mechanism.
# Runtime banner/load observations do not prove binary identity or Lineage compatibility.
BOARD_PREBUILT_VENDOR_BOOTIMAGE := $(DEVICE_PATH)/prebuilts/stock_680/vendor_boot.img
BOARD_PREBUILT_DTBOIMAGE := $(DEVICE_PATH)/prebuilts/stock_680/dtbo.img

BOARD_SUPER_PARTITION_SIZE := 12884901888
BOARD_SYSTEMIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_SYSTEM_EXTIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_PRODUCTIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_VENDORIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_ODMIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_VENDOR_DLKMIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_SYSTEM_DLKMIMAGE_FILE_SYSTEM_TYPE := ext4

TARGET_COPY_OUT_SYSTEM_EXT := system_ext
TARGET_COPY_OUT_PRODUCT := product
TARGET_COPY_OUT_VENDOR := vendor
TARGET_COPY_OUT_ODM := odm
TARGET_COPY_OUT_VENDOR_DLKM := vendor_dlkm
TARGET_COPY_OUT_SYSTEM_DLKM := system_dlkm

# Generated alongside khaje-vendor.mk after the pinned extraction.
-include vendor/lenovo/khaje/BoardConfigVendor.mk

# No GPT sizes, flash block size, active DT indices, AVB/OTA policy or offsets guessed.
# The native framework build must not silently proceed using incomplete configuration.
$(error khaje blocked: vendor makefiles and source-provider ABI graph missing; GPT limits and boot/init_boot plus VINTF/SELinux/AVB/OTA integration pending. See docs/next-build-blockers.md)
