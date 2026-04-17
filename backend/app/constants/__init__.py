#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
常量模块
"""

from .asset_types import (
    ProductCategory,
    AssetType,
    ASSET_TYPE_CONFIG,
    ASSET_TYPE_GROUPS,
    PRODUCT_PARAM_FIELDS,
    get_asset_type_name,
    get_asset_type_category,
    get_asset_type_config,
)

__all__ = [
    'ProductCategory',
    'AssetType',
    'ASSET_TYPE_CONFIG',
    'ASSET_TYPE_GROUPS',
    'PRODUCT_PARAM_FIELDS',
    'get_asset_type_name',
    'get_asset_type_category',
    'get_asset_type_config',
]