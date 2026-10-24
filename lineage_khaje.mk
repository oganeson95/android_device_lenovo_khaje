# SPDX-License-Identifier: Apache-2.0
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base.mk)

# Stock runtime reports wifi in three product-class properties.
$(call inherit-product, vendor/lineage/config/common_full_tablet_wifionly.mk)
$(call inherit-product, device/lenovo/khaje/device.mk)

PRODUCT_NAME := lineage_khaje
PRODUCT_DEVICE := khaje
PRODUCT_BRAND := Lenovo
PRODUCT_MODEL := TB331FC
PRODUCT_MANUFACTURER := LENOVO
