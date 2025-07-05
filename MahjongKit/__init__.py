#!/usr/bin/env python3
"""
SichuanMahjongKit - 血战到底麻将库

高性能、高精度的四川麻将计算库
基于血战到底规则实现
"""

try:
    from .core import Tile, TilesConverter, SuitType, PlayerState, Meld, MeldType
    from .validator import WinValidator, TingValidator
    from .analyzer import HandAnalyzer, GameAnalyzer, DiscardAnalysis
except ImportError:
    from core import Tile, TilesConverter, SuitType, PlayerState, Meld, MeldType
    from validator import WinValidator, TingValidator
    from analyzer import HandAnalyzer, GameAnalyzer, DiscardAnalysis

__version__ = "1.0.0"
__author__ = "Claude"
__description__ = "SichuanMahjongKit - 血战到底麻将库"

# 导出主要类和函数
__all__ = [
    # 核心类
    'Tile', 'TilesConverter', 'SuitType', 'PlayerState', 'Meld', 'MeldType',
    # 验证器
    'WinValidator', 'TingValidator',
    # 分析器
    'HandAnalyzer', 'GameAnalyzer', 'DiscardAnalysis'
]