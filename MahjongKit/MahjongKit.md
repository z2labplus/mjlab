好的，我已经仔细阅读并解析了您提供的 `xuezhan_rule.txt` 文件。这份规则非常具体，包含了大量独特的番型、计分倍数、互斥关系（“不计...”）以及游戏结束时的特殊结算，这对于我们设计 `SichuanMahjongKit` 库至关重要。

基于这份详细规则，我们现在可以对之前的方案进行一次**彻底的、针对性的升级和细化**。

---

### **`SichuanMahjongKit` 增强与细化方案 (基于`xuezhan_rule.txt`)**

这个方案将严格遵循您提供的规则，确保库的逻辑与目标游戏完全匹配。

#### **核心设计思想变更**

1.  **倍数体系而非番数**: 规则使用的是基数乘以倍数的模式（`x256`, `x64`），而非传统的番数叠加。我们的计分模块必须反映这一点。
2.  **番型互斥**: "不计A、B、C"的规则非常普遍。计分系统必须采用**层级覆盖**或**互斥检查**的机制，而非简单的番型相加。
3.  **游戏状态的重要性**: `定缺`、`杠牌收入`、`听牌状态`、`花猪状态`等信息需要贯穿整个对局，并影响最终结算。

---

### **模块一：核心数据与状态管理 (Core Data & State Management)**

此模块是基础，现在需要更丰富地描述玩家和游戏状态。

1.  **`Tile` 与 `TilesConverter`**
    *   (维持原方案) 内部表示仍用 0-26 的整数，`TilesConverter` 负责与字符串、频率数组的转换。

2.  **`Meld` (副露)**
    *   (维持原方案) 类型: `PONG` (碰), `EXPOSED_GONG` (明杠), `CONCEALED_GONG` (暗杠), `UPGRADED_GONG` (补杠/巴杠)。增加补杠类型是为了处理“抢杠胡”。
    *   属性: `type`, `tile`, `from_player_index`。

3.  **`PlayerState` (玩家状态)** - **新增并强化**
    *   这是一个关键的数据类，用于跟踪每个玩家的完整信息。
    *   `hand_tiles`: 一个长度为27的频率数组，表示手牌。
    *   `melds`: 一个 `Meld` 对象列表。
    *   `declared_void_suit`: (String: 'm'/'p'/'s') 开局定缺的花色。
    *   `has_won`: (Boolean) 该玩家是否已经胡牌。
    *   `is_ting`: (Boolean) 是否听牌。**此状态在每次打牌后都需要更新**。
    *   `is_flowery_pig`: (Boolean) 是否是花猪。在对局结束时计算。
    *   `gang_income`: (Number) 通过杠牌获得的即时收益（豆）。
    *   `win_info`: (Object) 如果已胡牌，记录胡牌信息（胡的哪张牌、自摸还是点炮、番型倍数等）。

---

### **模块二：核心规则与判定器 (Rule & Validators)**

1.  **`WinValidator` (胡牌判定器)**
    *   **主函数**: `is_hu(hand_array, melds)`
    *   **核心实现逻辑**:
        1.  **缺门检查 `_check_void_suit(hand_array, melds)`**: 这是第一道铁律。合并手牌和副露中的牌，检查花色是否超过2门。如果超过，直接返回 `False`。
        2.  **牌型结构检查**:
            *   `_check_seven_pairs(hand_array)`: 检查是否满足七对结构（包括各种龙七对）。
            *   `_check_standard_pattern(hand_array)`: 检查是否满足“N组面子 + 1对将牌”的结构。
            *   `is_hu` 的逻辑是：`_check_void_suit` 通过后，只要满足七对结构 **或** 标准结构之一，即为胡牌。

2.  **`TingValidator` (听牌判定器)** - **新增**
    *   **主函数**: `get_ting_info(hand_array, melds, declared_void_suit)`
    *   **目的**: 判断玩家是否听牌，并找出听哪些牌。
    *   **核心实现逻辑**:
        1.  **花猪预判**: 首先检查当前手牌（含副露）是否已是三门花色。如果是，则不可能听牌，直接返回空。
        2.  **遍历所有可能的进张 (0-26)**:
            *   对于每张牌 `p`，将其加入手牌。
            *   调用 `WinValidator.is_hu()` 检查加入 `p` 后的手牌是否胡牌。
            *   如果胡牌，则 `p` 是一张听的牌。
        3.  **返回**: 一个列表，包含所有听的牌。如果列表不为空，则玩家处于听牌状态。

---

### **模块三：向听数与AI建议 (Shanten & AI Suggestion)**

1.  **`ShantenCalculator` (向听数计算器)**
    *   **主函数**: `calculate_shanten(hand_array, melds, declared_void_suit)`
    *   **核心实现逻辑 (严格遵循规则)**:
        1.  **识别“必打牌”**: 找出所有属于 `declared_void_suit` 的牌。这些牌的“向听贡献”为负无穷，必须打掉。向听数 = (必打牌数量) + (剩余牌的向听数)。
        2.  **计算剩余牌向听数**: 对剔除“必打牌”后的手牌，使用标准算法计算距离“七对”和“标准牌型”的最小步数。
        3.  **最终结果**: 返回一个整数，代表到达一个合法的、非花猪的听牌状态还需要打/换多少张牌。

2.  **`HandAnalyzer` (手牌分析器)**
    *   **主函数**: `suggest_discard(player_state)`
    *   **核心实现逻辑 (规则驱动)**:
        1.  **强制打缺**: 检查手牌中是否有 `declared_void_suit` 的牌。
            *   **如果有**: 必须从这些牌中选择一张打出。可以直接返回第一张找到的缺门牌。
            *   **如果没有**: 进入下一步。
        2.  **计算牌效**: 遍历手上每一张牌（非缺门）：
            *   模拟打出这张牌。
            *   计算打出后手牌的向听数 (`calculate_shanten`)。
            *   计算有效进张数 (`TingValidator.get_ting_info` 返回的列表长度)。
        3.  **决策**: 返回能使**向听数最小**，且在向听数相同的情况下使**有效进张数最大**的那张牌。

---

### **模块四：倍数计算器 (Multiplier Calculator)**

这是最能体现 `xuezhan_rule.txt` 特色的模块，必须精心设计。

*   **`MultiplierCalculator` 类**
*   **主函数**: `calculate(hand_tiles, melds, win_tile, context)`
    *   `context`: 一个包含所有对局信息的对象。
        *   `is_zimo` (自摸), `is_gsh` (杠上花), `is_qgh` (抢杠胡), `is_hdl` (海底捞), `is_tianhu`, `is_dihu`
        *   `is_jgd` (金钩钓): `len(hand_tiles) == 2` 且 `win_tile` 是其中一张。
        *   `num_of_gongs`: 杠的数量。
        *   `num_of_gen`: “根”的数量（手牌中4张一样的牌 + 杠）。

*   **核心实现逻辑 (层级与互斥)**:
    1.  **定义番型数据**: 创建一个结构化列表，包含每个番型的所有信息。
        ```python
        FAN_PATTERNS = [
            {'name': '清十八罗汉', 'multiplier': 256, 'check_func': is_qing_shiba, 'excludes': ['清一色', '十八罗汉', ...]},
            {'name': '将三龙七对', 'multiplier': 128, 'check_func': is_jiang_san_long, 'excludes': [...]},
            # ... 按倍数从高到低排序
            {'name': '平胡', 'multiplier': 1, 'check_func': is_pinghu, 'excludes': []}
        ]
        ```

    2.  **主番型判定 (Top-Down Check)**:
        *   遍历 `FAN_PATTERNS` 列表（从最高倍数开始）。
        *   对于每个番型，调用其 `check_func`。
        *   **第一个匹配成功的番型即为主番型**。记录其倍数和名称，然后停止遍历。这个方法天然解决了所有“不计”规则。

    3.  **计算额外倍数 (Additive Multipliers)**:
        *   在主番型倍数的基础上，检查 `context` 中的附加条件：
        *   `if context.is_zimo: total_multiplier *= 2`
        *   `if context.is_gsh: total_multiplier *= 2`
        *   ...依此类推，处理所有`x2`的附加项。

    4.  **计算“根”倍数 (Final Multiplier)**:
        *   计算 `num_of_gen` 的数量。
        *   `total_multiplier *= (2 ** num_of_gen)`。注意：规则中提到龙七对等不计根，这应在对应番型的 `check_func` 内部或主逻辑中处理，即如果主番型是龙七对，计算根的数量时要减去构成龙七对的那个根。

    5.  **返回**: 一个包含 `total_multiplier` 和 `pattern_names` 的结果对象。

*   **需要实现的具体检查函数 `is_...()`**:
    *   `is_qingyise()`: 检查所有牌是否同花色。
    *   `is_pengpenghu()`: 检查是否全由刻子和将牌组成。
    *   `is_qidui()`: 检查是否为七对。
    *   `is_longqidui()`: 检查是否为七对且含有一个根。
    *   `is_jiangdui()`: 检查是否为碰碰胡且所有牌都是2、5、8。
    *   ...为 `FAN_PATTERNS` 中的每一个番型编写一个精确的检查函数。

---

### **模块五：游戏终局结算 (Endgame Settlement)**

此模块不属于核心手牌计算，但对一个完整的库或游戏引擎至关重要。

*   **`SettlementEngine` 类**
*   **主函数**: `settle(all_player_states)`
*   **核心实现逻辑**:
    1.  **查花猪**:
        *   遍历所有玩家，检查其最终手牌（`hand_tiles` + `melds`），如果超过2门花色，标记为 `is_flowery_pig = True`。
        *   花猪玩家赔给其他每位非花猪玩家16倍（这里的“倍”可能是指一个基础分，需确认）。
    2.  **退税**:
        *   遍历所有未胡牌的玩家。
        *   如果该玩家 `is_ting == False`，则其 `gang_income` 清零，并将这部分收益返还给被杠的玩家。
    3.  **查大叫**:
        *   找出所有未胡牌的玩家，分为“听牌组”和“未听牌组”。
        *   对于每个“未听牌组”的玩家，他需要赔付给“听牌组”的所有玩家。
        *   赔付金额为：听牌玩家当时手牌的最大可能胡牌倍数。这就需要调用 `MultiplierCalculator`，模拟该听牌玩家所有听的牌，并计算出最大倍数。

---

### **总结与开发路线图**

1.  **第一步 (地基)**: 实现 `模块一` 和 `模块二`。确保牌的表示、转换、胡牌和听牌判定100%准确。这是所有后续功能的基础。
2.  **第二步 (AI核心)**: 实现 `模块三`。开发准确的向听数计算器和基于规则的打牌建议器。
3.  **第三步 (计分灵魂)**: 实现 `模块四`。这是最能体现游戏特色的部分。严格按照层级和互斥规则实现倍数计算。
4.  **第四步 (游戏逻辑)**: 实现 `模块五` 和一个简单的 `GameEngine` 来驱动整个流程，处理发牌、玩家动作、和局结算等。

这个方案已经将您提供的`xuezhan_rule.txt`完全融入了设计中，每个细节都有对应的实现规划。按照这个蓝图，您就可以着手构建一个强大且规则精确的 `SichuanMahjongKit` 库了。