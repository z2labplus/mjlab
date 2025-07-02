# 血战麻将牌谱格式说明

## 概述

血战麻将牌谱采用JSON格式存储，包含完整的游戏信息、玩家数据和操作序列。这种格式便于存储、传输和分析，同时保持了良好的可读性。

## 数据结构

### 顶层结构

```json
{
  "game_info": {
    // 游戏基本信息
  },
  "players": [
    // 玩家信息数组
  ],
  "actions": [
    // 操作序列数组
  ],
  "metadata": {
    // 牌谱元数据
  }
}
```

## 完整示例

```json
{
  "game_info": {
    "game_id": "game_abc123def456",
    "start_time": "2024-01-15T14:30:00Z",
    "end_time": "2024-01-15T15:15:00Z",
    "duration": 2700,
    "player_count": 4,
    "game_mode": "xuezhan"
  },
  "players": [
    {
      "id": 0,
      "name": "小明",
      "position": 0,
      "initial_hand": ["1万", "2万", "3万", "4万", "5万", "6万", "7万", "8万", "9万", "1条", "2条", "3条", "4条"],
      "missing_suit": "wan",
      "final_score": 15,
      "is_winner": true,
      "statistics": {
        "draw_count": 18,
        "discard_count": 17,
        "peng_count": 1,
        "gang_count": 1
      }
    },
    {
      "id": 1,
      "name": "小红",
      "position": 1,
      "initial_hand": ["1条", "2条", "3条", "4条", "5条", "6条", "7条", "8条", "9条", "1筒", "2筒", "3筒", "4筒"],
      "missing_suit": "tiao",
      "final_score": -5,
      "is_winner": false,
      "statistics": {
        "draw_count": 15,
        "discard_count": 15,
        "peng_count": 0,
        "gang_count": 0
      }
    },
    {
      "id": 2,
      "name": "小刚",
      "position": 2,
      "initial_hand": ["1筒", "2筒", "3筒", "4筒", "5筒", "6筒", "7筒", "8筒", "9筒", "1万", "2万", "3万", "4万"],
      "missing_suit": "tong",
      "final_score": -5,
      "is_winner": false,
      "statistics": {
        "draw_count": 16,
        "discard_count": 16,
        "peng_count": 1,
        "gang_count": 0
      }
    },
    {
      "id": 3,
      "name": "小美",
      "position": 3,
      "initial_hand": ["2万", "3万", "4万", "5万", "6万", "7万", "8万", "1条", "2条", "3条", "4条", "5条", "6条"],
      "missing_suit": "wan",
      "final_score": -5,
      "is_winner": false,
      "statistics": {
        "draw_count": 14,
        "discard_count": 14,
        "peng_count": 0,
        "gang_count": 0
      }
    }
  ],
  "actions": [
    {
      "sequence": 1,
      "timestamp": "2024-01-15T14:30:15Z",
      "player_id": 0,
      "action_type": "missing_suit",
      "card": null,
      "target_player": null,
      "gang_type": null,
      "score_change": 0
    },
    {
      "sequence": 2,
      "timestamp": "2024-01-15T14:30:18Z",
      "player_id": 1,
      "action_type": "missing_suit",
      "card": null,
      "target_player": null,
      "gang_type": null,
      "score_change": 0
    },
    {
      "sequence": 3,
      "timestamp": "2024-01-15T14:30:20Z",
      "player_id": 0,
      "action_type": "draw",
      "card": "5万",
      "target_player": null,
      "gang_type": null,
      "score_change": 0
    },
    {
      "sequence": 4,
      "timestamp": "2024-01-15T14:30:25Z",
      "player_id": 0,
      "action_type": "discard",
      "card": "1万",
      "target_player": null,
      "gang_type": null,
      "score_change": 0
    },
    {
      "sequence": 5,
      "timestamp": "2024-01-15T14:30:30Z",
      "player_id": 1,
      "action_type": "peng",
      "card": "1万",
      "target_player": 0,
      "gang_type": null,
      "score_change": 0
    },
    {
      "sequence": 6,
      "timestamp": "2024-01-15T14:30:35Z",
      "player_id": 1,
      "action_type": "discard",
      "card": "9条",
      "target_player": null,
      "gang_type": null,
      "score_change": 0
    },
    {
      "sequence": 7,
      "timestamp": "2024-01-15T14:30:40Z",
      "player_id": 2,
      "action_type": "gang",
      "card": "9条",
      "target_player": 1,
      "gang_type": "ming_gang",
      "score_change": 4
    },
    {
      "sequence": 8,
      "timestamp": "2024-01-15T14:32:10Z",
      "player_id": 0,
      "action_type": "hu",
      "card": "6万",
      "target_player": null,
      "gang_type": null,
      "score_change": 20
    }
  ],
  "metadata": {
    "generated_at": "2024-01-15T15:20:00Z",
    "version": "1.0",
    "format": "xuezhan_mahjong"
  }
}
```

## 字段说明

### game_info 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| game_id | string | 游戏唯一标识符 |
| start_time | string | 游戏开始时间 (ISO 8601格式) |
| end_time | string | 游戏结束时间 (ISO 8601格式) |
| duration | number | 游戏时长 (秒) |
| player_count | number | 玩家数量 |
| game_mode | string | 游戏模式 ("xuezhan") |

### players 数组

每个玩家对象包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | number | 玩家ID (0-3) |
| name | string | 玩家昵称 |
| position | number | 座位号 (0-3) |
| initial_hand | array | 起手牌列表 |
| missing_suit | string | 定缺花色 ("wan"/"tiao"/"tong") |
| final_score | number | 最终得分 |
| is_winner | boolean | 是否胜利 |
| statistics | object | 统计数据 |

### actions 数组

每个操作对象包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| sequence | number | 操作序号 |
| timestamp | string | 操作时间 (ISO 8601格式) |
| player_id | number | 操作玩家ID |
| action_type | string | 操作类型 |
| card | string | 相关牌面 (可选) |
| target_player | number | 目标玩家 (可选) |
| gang_type | string | 杠牌类型 (可选) |
| score_change | number | 分数变化 |

### 操作类型说明

| 类型 | 说明 | 相关字段 |
|------|------|----------|
| missing_suit | 定缺 | missing_suit |
| draw | 摸牌 | card |
| discard | 弃牌 | card |
| peng | 碰牌 | card, target_player |
| gang | 杠牌 | card, gang_type, target_player, score_change |
| hu | 胡牌 | card, score_change |
| pass | 过牌 | - |

### 杠牌类型

| 类型 | 说明 |
|------|------|
| an_gang | 暗杠 |
| ming_gang | 明杠 (直杠) |
| jia_gang | 加杠 |

## 使用场景

### 1. 牌谱分析

```python
import json

def analyze_replay(replay_data):
    """分析牌谱数据"""
    # 解析JSON数据
    data = json.loads(replay_data)
    
    # 获取游戏基本信息
    game_info = data["game_info"]
    players = data["players"]
    actions = data["actions"]
    
    # 分析游戏时长
    duration_minutes = game_info["duration"] / 60
    
    # 统计操作分布
    action_counts = {}
    for action in actions:
        action_type = action["action_type"]
        action_counts[action_type] = action_counts.get(action_type, 0) + 1
    
    # 找出胜利者
    winners = [p["name"] for p in players if p["is_winner"]]
    
    print(f"游戏时长: {duration_minutes:.1f}分钟")
    print(f"胜利者: {', '.join(winners)}")
    print(f"操作统计: {action_counts}")
```

### 2. 游戏回放

```javascript
// JavaScript前端回放示例
class ReplayPlayer {
    constructor(replayData) {
        this.data = JSON.parse(replayData);
        this.currentStep = 0;
    }
    
    getCurrentAction() {
        return this.data.actions[this.currentStep];
    }
    
    nextStep() {
        if (this.currentStep < this.data.actions.length - 1) {
            this.currentStep++;
            return this.getCurrentAction();
        }
        return null;
    }
    
    previousStep() {
        if (this.currentStep > 0) {
            this.currentStep--;
            return this.getCurrentAction();
        }
        return null;
    }
    
    getProgress() {
        return this.currentStep / this.data.actions.length;
    }
}
```

### 3. 数据导入

```python
def import_replay_to_database(replay_json):
    """将牌谱导入数据库"""
    data = json.loads(replay_json)
    
    # 创建游戏记录
    game = Game.objects.create(
        game_id=data["game_info"]["game_id"],
        start_time=data["game_info"]["start_time"],
        end_time=data["game_info"]["end_time"],
        duration=data["game_info"]["duration"]
    )
    
    # 创建玩家记录
    for player_data in data["players"]:
        Player.objects.create(
            game=game,
            player_id=player_data["id"],
            name=player_data["name"],
            final_score=player_data["final_score"],
            is_winner=player_data["is_winner"]
        )
    
    # 创建操作记录
    for action_data in data["actions"]:
        Action.objects.create(
            game=game,
            sequence=action_data["sequence"],
            player_id=action_data["player_id"],
            action_type=action_data["action_type"],
            timestamp=action_data["timestamp"]
        )
```

## 文件格式

### JSON格式
- **文件扩展名**: `.json`
- **编码**: UTF-8
- **MIME类型**: `application/json`
- **特点**: 直接可读，便于程序处理

### ZIP压缩包格式
- **文件扩展名**: `.zip`
- **包含文件**:
  - `{game_id}.json` - 完整牌谱数据
  - `summary.json` - 游戏摘要信息
  - `README.md` - 说明文档

## 兼容性说明

本牌谱格式设计参考了主流麻将游戏的牌谱标准，具有以下特点：

1. **标准化**: 使用标准的JSON格式，便于跨平台使用
2. **可扩展**: 预留了扩展字段，便于未来功能增强
3. **向后兼容**: 版本升级时保持向后兼容性
4. **自描述**: 包含完整的元数据信息

## API接口

获取和导出牌谱的API接口：

- `GET /api/v1/replay/{game_id}` - 获取牌谱数据
- `GET /api/v1/replay/{game_id}/export/json` - 导出JSON格式
- `GET /api/v1/replay/{game_id}/export/zip` - 导出ZIP格式
- `GET /api/v1/replay/list` - 获取牌谱列表
- `GET /api/v1/replay/player/{player_name}/history` - 获取玩家历史 