# SichuanMahjongKit - 血战到底麻将库

基于血战到底规则的高性能、高精度Python麻将计算库。

## 功能特点

- **完整的血战到底规则支持**: 包括定缺、碰杠、胡牌验证等
- **智能分析引擎**: 提供最优出牌建议、向听数计算、进张统计
- **牌谱分析**: 支持JSON格式牌谱的详细分析
- **灵活的数据格式**: 支持多种牌的表示方法(字符串、27位数组、Tile对象)
- **模块化设计**: 核心功能独立，易于集成和扩展

## 核心模块

### 1. core.py - 核心数据结构
- `Tile`: 单张麻将牌
- `TilesConverter`: 牌的格式转换器
- `PlayerState`: 玩家状态管理
- `Meld`: 副露(碰、杠)管理

### 2. validator.py - 胡牌验证
- `WinValidator`: 胡牌验证器
- `TingValidator`: 听牌和向听数计算

### 3. analyzer.py - 智能分析
- `HandAnalyzer`: 手牌分析器
- `GameAnalyzer`: 游戏状态分析器
- `DiscardAnalysis`: 弃牌分析结果

## 快速开始

### 基本使用

```python
from MahjongKit import Tile, TilesConverter, HandAnalyzer, WinValidator

# 创建牌
tile = Tile.from_chinese("1万")
tiles = TilesConverter.string_to_tiles("123m456s789p")

# 检查胡牌
is_winning = WinValidator.is_winning_hand(tiles)

# 分析最佳出牌
analyses = HandAnalyzer.analyze_discard_options(tiles)
best_discard = analyses[0]
print(f"建议打出: {best_discard.discard_tile}")
```

### 牌谱分析

```bash
# 分析牌谱文件
python demo.py test_final.json
```

## 示例输出

```
=== 血战到底麻将分析 ===
牌谱文件: test_final.json
游戏类型: xuezhan_daodi

🎯 第2手 - 玩家0摸牌: 6条
摸牌前手牌: 4899m123347999s
摸牌后手牌: 4899m1233467999s
当前向听: 0
是否听牌: 是
💡 建议打出: 4m
   打出后向听: 0
   有效进张: 0张
📊 弃牌选择分析:
   1. 弃4m: 0向听, 0进张, 得分1000.0
   2. 弃8m: 0向听, 0进张, 得分1000.0
🔍 策略建议:
   🎯 已听牌! 胡牌张: []
   建议打出: 4m
   剩余胡牌张: 0张
```

## 技术特点

### 血战到底规则支持

- **定缺系统**: 玩家必须定缺一门花色
- **花色限制**: 手牌不超过2门花色才能胡牌
- **副露支持**: 碰牌、明杠、加杠
- **花猪检测**: 自动检测三门花色的花猪状态

### 智能分析算法

- **向听数计算**: 准确计算标准胡牌和七对的向听数
- **进张统计**: 统计减少向听数的有效进张
- **综合评分**: 考虑向听数、进张数的综合评分系统
- **胡牌概率**: 基于已知牌计算胡牌概率

### 多格式支持

```python
# 字符串格式
tiles_str = "123m456s789p"

# 中文格式
chinese_tiles = ["1万", "2万", "3万"]

# 27位数组格式
array_27 = [1,1,1,0,0,0,0,0,0, 1,1,1,0,0,0,0,0,0, 1,1,1,0,0,0,0,0,0]

# 相互转换
tiles = TilesConverter.string_to_tiles(tiles_str)
array = TilesConverter.tiles_to_27_array(tiles)
back_str = TilesConverter.array_27_to_string(array)
```

## 性能优化

- **递归算法**: 高效的胡牌验证和向听数计算
- **缓存机制**: 重复计算结果缓存
- **批量分析**: 支持批量弃牌分析
- **内存优化**: 合理的数据结构设计

## 扩展功能

### 自定义规则

```python
class CustomWinValidator(WinValidator):
    @staticmethod
    def _check_suit_limit(tiles, melds):
        # 自定义花色限制逻辑
        return True
```

### 分析结果导出

```python
# 导出分析结果
analysis_results = analyzer.analyze_replay()
with open('analysis_report.json', 'w') as f:
    json.dump(analysis_results, f, indent=2)
```

## 测试

```bash
# 运行核心模块测试
python core.py

# 运行验证器测试
python validator.py

# 运行分析器测试
python analyzer.py
```

## 开发者指南

### 添加新功能

1. 在相应模块中添加新类或方法
2. 更新 `__init__.py` 导出列表
3. 添加测试用例
4. 更新文档

### 规则定制

本库设计为易于扩展，可以轻松添加新的麻将规则:

```python
class NewRuleValidator(WinValidator):
    @staticmethod
    def is_winning_hand(tiles, melds=None):
        # 实现新规则的胡牌验证
        pass
```

## 许可证

MIT License

## 更新日志

### v1.0.0
- 完整的血战到底规则支持
- 智能分析引擎
- 牌谱分析功能
- 多格式数据支持