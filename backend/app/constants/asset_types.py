#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资产类型常量配置
定义系统中支持的所有理财产品类型及其属性
"""


class ProductCategory:
    """产品大类"""
    MARKET = 'market'               # 市价型（股票/ETF/基金/贵金属等）
    FIXED_INCOME = 'fixed_income'   # 固定收益型
    MANUAL = 'manual'               # 手动录入型


class AssetType:
    """资产类型常量"""

    # ===== 市价型产品 =====
    STOCK = 'stock'                 # 股票
    ETF_INDEX = 'etf_index'         # 宽基ETF
    ETF_SECTOR = 'etf_sector'       # 行业ETF
    FUND = 'fund'                   # 基金
    GOLD = 'gold'                   # 黄金
    SILVER = 'silver'               # 白银

    # ===== 固定收益类 =====
    BANK_DEPOSIT = 'bank_deposit'           # 银行定期存款
    BANK_CURRENT = 'bank_current'           # 银行活期存款
    BANK_WEALTH = 'bank_wealth'             # 银行理财产品
    TREASURY_BOND = 'treasury_bond'         # 国债
    CORPORATE_BOND = 'corporate_bond'       # 企业债
    MONEY_FUND = 'money_fund'               # 货币基金

    # ===== 其他产品 =====
    INSURANCE = 'insurance'         # 保险理财
    TRUST = 'trust'                 # 信托产品
    OTHER = 'other'                 # 其他


# 资产类型配置
ASSET_TYPE_CONFIG = {
    # ===== 市价型产品 =====
    AssetType.STOCK: {
        'name': '股票',
        'category': ProductCategory.MARKET,
        'has_realtime_price': True,
        'price_source': 'stock',
        'risk_level': 'R4',
        'form_fields': [],  # 使用默认字段
    },
    AssetType.ETF_INDEX: {
        'name': '宽基ETF',
        'category': ProductCategory.MARKET,
        'has_realtime_price': True,
        'price_source': 'stock',
        'risk_level': 'R3',
        'form_fields': [],
    },
    AssetType.ETF_SECTOR: {
        'name': '行业ETF',
        'category': ProductCategory.MARKET,
        'has_realtime_price': True,
        'price_source': 'stock',
        'risk_level': 'R3',
        'form_fields': [],
    },
    AssetType.FUND: {
        'name': '基金',
        'category': ProductCategory.MARKET,
        'has_realtime_price': True,
        'price_source': 'fund',
        'risk_level': 'R3',
        'form_fields': [],
    },
    AssetType.GOLD: {
        'name': '黄金',
        'category': ProductCategory.MARKET,
        'has_realtime_price': True,
        'price_source': 'precious_metal',
        'risk_level': 'R3',
        'form_fields': ['weight', 'purity', 'buy_channel'],
    },
    AssetType.SILVER: {
        'name': '白银',
        'category': ProductCategory.MARKET,
        'has_realtime_price': True,
        'price_source': 'precious_metal',
        'risk_level': 'R4',
        'form_fields': ['weight', 'purity', 'buy_channel'],
    },

    # ===== 固定收益类 =====
    AssetType.BANK_DEPOSIT: {
        'name': '银行定期存款',
        'category': ProductCategory.FIXED_INCOME,
        'has_realtime_price': False,
        'risk_level': 'R1',
        'form_fields': ['interest_rate', 'start_date', 'end_date', 'redeemable'],
    },
    AssetType.BANK_CURRENT: {
        'name': '银行活期存款',
        'category': ProductCategory.FIXED_INCOME,
        'has_realtime_price': False,
        'risk_level': 'R1',
        'form_fields': ['interest_rate'],
    },
    AssetType.BANK_WEALTH: {
        'name': '银行理财产品',
        'category': ProductCategory.FIXED_INCOME,
        'has_realtime_price': False,
        'risk_level': 'R2',
        'form_fields': ['interest_rate', 'start_date', 'end_date', 'redeemable', 'risk_level'],
    },
    AssetType.TREASURY_BOND: {
        'name': '国债',
        'category': ProductCategory.FIXED_INCOME,
        'has_realtime_price': False,
        'risk_level': 'R1',
        'form_fields': ['interest_rate', 'start_date', 'end_date', 'payment_cycle'],
    },
    AssetType.CORPORATE_BOND: {
        'name': '企业债',
        'category': ProductCategory.FIXED_INCOME,
        'has_realtime_price': False,
        'risk_level': 'R3',
        'form_fields': ['interest_rate', 'start_date', 'end_date', 'payment_cycle', 'issuer'],
    },
    AssetType.MONEY_FUND: {
        'name': '货币基金',
        'category': ProductCategory.FIXED_INCOME,
        'has_realtime_price': True,
        'price_source': 'money_fund',
        'risk_level': 'R1',
        'form_fields': ['interest_rate'],
    },

    # ===== 其他产品 =====
    AssetType.INSURANCE: {
        'name': '保险理财',
        'category': ProductCategory.MANUAL,
        'has_realtime_price': False,
        'risk_level': 'R2',
        'form_fields': ['interest_rate', 'start_date', 'end_date', 'issuer'],
    },
    AssetType.TRUST: {
        'name': '信托产品',
        'category': ProductCategory.MANUAL,
        'has_realtime_price': False,
        'risk_level': 'R4',
        'form_fields': ['interest_rate', 'start_date', 'end_date', 'issuer'],
    },
    AssetType.OTHER: {
        'name': '其他',
        'category': ProductCategory.MANUAL,
        'has_realtime_price': False,
        'risk_level': 'R3',
        'form_fields': [],
    },
}


# 资产类型分组（用于前端下拉框）
ASSET_TYPE_GROUPS = [
    {
        'group': '市价型产品',
        'types': [
            AssetType.STOCK,
            AssetType.ETF_INDEX,
            AssetType.ETF_SECTOR,
            AssetType.FUND,
            AssetType.GOLD,
            AssetType.SILVER,
        ]
    },
    {
        'group': '固定收益类',
        'types': [
            AssetType.BANK_DEPOSIT,
            AssetType.BANK_CURRENT,
            AssetType.BANK_WEALTH,
            AssetType.TREASURY_BOND,
            AssetType.CORPORATE_BOND,
            AssetType.MONEY_FUND,
        ]
    },
    {
        'group': '其他产品',
        'types': [
            AssetType.INSURANCE,
            AssetType.TRUST,
            AssetType.OTHER,
        ]
    },
]


# 产品参数字段定义
PRODUCT_PARAM_FIELDS = {
    'interest_rate': {
        'name': '年化利率',
        'type': 'number',
        'unit': '%',
        'placeholder': '如: 3.5',
    },
    'start_date': {
        'name': '起息日/买入日期',
        'type': 'date',
    },
    'end_date': {
        'name': '到期日',
        'type': 'date',
    },
    'redeemable': {
        'name': '可提前赎回',
        'type': 'checkbox',
    },
    'payment_cycle': {
        'name': '付息方式',
        'type': 'select',
        'options': [
            {'value': 'at_maturity', 'label': '到期付息'},
            {'value': 'monthly', 'label': '按月付息'},
            {'value': 'quarterly', 'label': '按季付息'},
            {'value': 'yearly', 'label': '按年付息'},
        ]
    },
    'interest_type': {
        'name': '计息方式',
        'type': 'select',
        'options': [
            {'value': 'simple', 'label': '单利'},
            {'value': 'compound', 'label': '复利'},
        ]
    },
    'issuer': {
        'name': '发行机构',
        'type': 'text',
        'placeholder': '如: 工商银行',
    },
    'risk_level': {
        'name': '风险等级',
        'type': 'select',
        'options': [
            {'value': 'R1', 'label': 'R1-低风险'},
            {'value': 'R2', 'label': 'R2-中低风险'},
            {'value': 'R3', 'label': 'R3-中风险'},
            {'value': 'R4', 'label': 'R4-中高风险'},
            {'value': 'R5', 'label': 'R5-高风险'},
        ]
    },
    'weight': {
        'name': '重量',
        'type': 'number',
        'unit': '克',
        'placeholder': '如: 10',
    },
    'purity': {
        'name': '纯度',
        'type': 'number',
        'placeholder': '如: 0.9999',
    },
    'buy_channel': {
        'name': '购买渠道',
        'type': 'select',
        'options': [
            {'value': 'bank', 'label': '银行'},
            {'value': 'platform', 'label': '交易平台'},
            {'value': 'physical', 'label': '实物购买'},
        ]
    },
}


def get_asset_type_name(asset_type):
    """获取资产类型的中文名称"""
    config = ASSET_TYPE_CONFIG.get(asset_type)
    return config['name'] if config else asset_type


def get_asset_type_category(asset_type):
    """获取资产类型的产品大类"""
    config = ASSET_TYPE_CONFIG.get(asset_type)
    return config['category'] if config else ProductCategory.MARKET


def get_asset_type_config(asset_type):
    """获取资产类型的完整配置"""
    return ASSET_TYPE_CONFIG.get(asset_type, ASSET_TYPE_CONFIG.get(AssetType.OTHER))