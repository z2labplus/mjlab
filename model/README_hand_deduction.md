# 🎯 麻将手牌推导工具集使用指南

本工具集包含5个文件，用于麻将手牌的逆向推导和验证分析。

## 📁 文件概览

| 文件名 | 主要功能 | 使用场景 | 难度 |
|--------|----------|----------|------|
| `hand_deduction_tool.py` | **主工具** - 实际推导手牌 | 日常使用 | ⭐ |
| `game_data_template.json` | 数据格式模板 | 准备数据 | ⭐ |
| `simple_hand_verification.py` | 原理演示 | 学习理解 | ⭐ |
| `improved_hand_reconstruction.py` | 可行性分析 | 评估数据质量 | ⭐⭐ |
| `hand_reconstruction.py` | 复杂分析器 | 深度分析 | ⭐⭐⭐ |

---

## 🚀 快速开始（推荐使用）

### 1️⃣ **主工具：hand_deduction_tool.py**

**这是您最主要使用的工具！**

#### 创建数据模板
```bash
python hand_deduction_tool.py --create_template
```

#### 推导手牌
```bash
python hand_deduction_tool.py --input your_game_data.json
```

#### 完整使用流程
```bash
# 步骤1: 创建模板
python hand_deduction_tool.py --create_template

# 步骤2: 编辑 game_data_template.json，填入您的游戏数据

# 步骤3: 运行推导
python hand_deduction_tool.py --input game_data_template.json
```

### 2️⃣ **数据模板：game_data_template.json**

**您需要编辑这个文件来提供游戏数据**

```json
{
  "players": {
    "0": {
      "name": "张三",
      "final_hand": ["2万", "3万", "4万", "5万", "6万", "7万", "8万"],
      "actions": [
        {"type": "draw", "card": "5条"},
        {"type": "discard", "card": "9万"},
        {"type": "peng", "card": "2条"}
      ],
      "melds": [
        {"type": "peng", "cards": ["2条", "2条", "2条"]}
      ]
    }
  }
}
```

---

## 📚 学习和分析工具

### 3️⃣ **原理演示：simple_hand_verification.py**

**用于理解手牌推导的基本原理**

```bash
python simple_hand_verification.py
```

**输出示例：**
```
🎯 麻将手牌逆向推导原理演示
==================================================
1. 初始手牌 (13张): ['1万', '2万', '3万', ...]
2. 最终手牌 (11张): ['2万', '3万', '4万', ...]
🧮 逆向推导过程:
   最终手牌: 11张
   + 弃牌: 2张
   + 碰杠消耗: 2张
   - 摸牌: 2张
✅ 推导结果: 完全匹配！
```

### 4️⃣ **可行性分析：improved_hand_reconstruction.py**

**评估数据质量和推导可行性**

```bash
python improved_hand_reconstruction.py
```

**输出示例：**
```
📊 可行性评估:
   评分: 100/100
   等级: 高
   推荐方法: 直接验证法
📋 影响因素:
   ✅ 有初始手牌记录
   ✅ 有最终状态信息
   ✅ 操作记录完整
```

### 5️⃣ **复杂分析器：hand_reconstruction.py**

**对现有牌谱文件进行深度分析**

```bash
python hand_reconstruction.py --replay_file sample_replay.json
```

**输出示例：**
```
--- 玩家 0: 张三 ---
声明的初始手牌: ['1万', '1万', '2万', '3万', ...]
重构的初始手牌: ['1万', '2万', '3万', '4万', ...]
重构可能性: True
置信度: 0.95
```

---

## 🎯 实际使用场景

### 场景1：我有完整的游戏记录，想推导初始手牌

```bash
# 1. 准备数据
python hand_deduction_tool.py --create_template

# 2. 编辑 game_data_template.json，填入：
#    - 每个玩家的最终手牌
#    - 摸牌、弃牌、碰杠的操作记录

# 3. 运行推导
python hand_deduction_tool.py --input game_data_template.json
```

### 场景2：我想了解推导原理

```bash
# 运行原理演示
python simple_hand_verification.py
```

### 场景3：我有现成的牌谱JSON文件

```bash
# 分析牌谱文件的推导可行性
python improved_hand_reconstruction.py

# 深度分析特定牌谱
python hand_reconstruction.py --replay_file your_replay.json
```

### 场景4：我想评估数据质量

```bash
# 检查数据完整性和推导可行性
python improved_hand_reconstruction.py
```

---

## 🔧 数据格式要求

### 必需数据
- **最终手牌**: 游戏结束时每个玩家的手牌
- **操作记录**: 摸牌、弃牌、碰杠的详细记录

### 操作格式
```json
{
  "type": "操作类型",
  "card": "具体牌面",
  "gang_type": "杠牌类型(可选)"
}
```

### 操作类型
- `draw`: 摸牌
- `discard`: 弃牌  
- `peng`: 碰牌
- `gang`: 杠牌

### 杠牌类型
- `an_gang`: 暗杠（手牌4张）
- `ming_gang`: 明杠（手牌3张+弃牌1张）
- `jia_gang`: 加杠（碰后加1张）

---

## 📊 输出结果说明

### 成功推导
```
✅ 推导成功 (置信度: 1.00)
🎴 推导的初始手牌 (13张):
   ['1万', '2万', '3万', '4万', '5万', '6万', '7万', '8万', '9万', '1条', '2条', '3条', '4条']
📊 计算过程:
   最终手牌: 11张
   + 弃牌: 2张  
   + 碰杠消耗: 2张
   - 摸牌: 2张
   = 初始手牌: 13张
```

### 失败或有问题
```
❌ 推导失败 (置信度: 0.70)
⚠️ 问题:
   • 牌 '1万' 需要 5 张，但牌库只有 4 张
   • 重构的初始手牌总数为 14 张，不是标准的13张
```

---

## 💡 使用技巧

### 1. 数据准备技巧
- 确保操作记录的时间顺序正确
- 碰杠操作要记录消耗的手牌数量
- 最终手牌要完整准确

### 2. 问题排查
- 如果推导失败，检查牌的数量是否超出限制
- 如果置信度低，检查操作记录是否完整
- 如果总数不对，检查摸牌弃牌记录

### 3. 提高准确度
- 提供越详细的操作记录，推导越准确
- 包含碰杠的具体信息
- 确保数据的一致性

---

## 🔍 常见问题

### Q1: 我只有部分数据，能推导吗？
A: 可以尝试，但置信度会降低。至少需要最终手牌和主要操作记录。

### Q2: 推导结果为什么不是13张？
A: 可能操作记录不完整，或者某些摸牌/弃牌没有记录。

### Q3: 如何提高推导成功率？
A: 
- 提供完整的操作记录
- 确保牌面信息准确
- 包含所有碰杠的详细信息

### Q4: 可以推导字牌（东南西北中发白）吗？
A: 可以，工具支持标准麻将的所有牌型。

---

## 🎯 推荐使用顺序

1. **先运行** `simple_hand_verification.py` **了解原理**
2. **使用** `hand_deduction_tool.py` **进行实际推导**
3. **如需分析现有牌谱，使用** `improved_hand_reconstruction.py`
4. **深度分析用** `hand_reconstruction.py`

---

## 📞 技术支持

如果您在使用过程中遇到问题：
1. 检查数据格式是否符合模板要求
2. 确认操作记录的完整性
3. 查看错误信息中的具体提示
4. 参考本指南的故障排除部分