# 麻将API详细参考

## 服务器配置

- **Base URL**: `http://localhost:8000`
- **API前缀**: `/api/mahjong`
- **Content-Type**: `application/json`

## 数据模型

### Tile (麻将牌)
```json
{
  "type": "wan|tiao|tong",  // 牌类型
  "value": 1-9              // 牌面值
}
```

### 游戏状态响应
```json
{
  "success": true,
  "message": "操作成功",
  "game_state": {
    "player_hands": {
      "0": {"tiles": [...], "melds": [...]},
      "1": {"tiles": [...], "melds": [...]},
      "2": {"tiles": [...], "melds": [...]}, 
      "3": {"tiles": [...], "melds": [...]}
    },
    "discarded_tiles": [...],
    "player_discarded_tiles": {
      "0": [...], "1": [...], "2": [...], "3": [...]
    },
    "current_player": 0,
    "actions_history": [...]
  }
}
```

## API接口详情

### 1. POST /api/mahjong/operation
通用操作接口（推荐使用）

**请求体:**
```json
{
  "player_id": 0,                    // 必需：玩家ID (0-3)
  "operation_type": "peng",          // 必需：操作类型
  "tile": {                          // 必需：操作的牌
    "type": "wan",
    "value": 7
  },
  "source_player_id": 3              // 可选：来源玩家（碰牌、直杠时使用）
}
```

**operation_type 可选值:**
- `hand` - 添加手牌
- `discard` - 弃牌  
- `peng` - 碰牌
- `angang` - 暗杠
- `zhigang` - 直杠
- `jiagang` - 加杠

### 2. GET /api/mahjong/game-state
获取当前游戏状态

**响应:** 完整的游戏状态对象

### 3. POST /api/mahjong/reset
重置游戏到初始状态

**响应:**
```json
{
  "success": true,
  "message": "游戏重置成功",
  "game_state": {...}
}
```

### 4. POST /api/mahjong/add-hand-tile
添加手牌（便捷接口）

**Query参数:**
- `player_id`: 玩家ID (0-3)
- `tile_type`: 牌类型 (wan|tiao|tong)  
- `tile_value`: 牌面值 (1-9)

### 5. POST /api/mahjong/discard-tile
弃牌（便捷接口）

**Query参数:**
- `player_id`: 玩家ID (0-3)
- `tile_type`: 牌类型 (wan|tiao|tong)
- `tile_value`: 牌面值 (1-9)

### 6. POST /api/mahjong/peng
碰牌（便捷接口）

**Query参数:**
- `player_id`: 执行碰牌的玩家ID (0-3)
- `tile_type`: 牌类型 (wan|tiao|tong)
- `tile_value`: 牌面值 (1-9)
- `source_player_id`: 可选，被碰牌的来源玩家ID

### 7. POST /api/mahjong/gang
杠牌（便捷接口）

**Query参数:**
- `player_id`: 执行杠牌的玩家ID (0-3)
- `tile_type`: 牌类型 (wan|tiao|tong)
- `tile_value`: 牌面值 (1-9)
- `gang_type`: 杠牌类型 (angang|zhigang|jiagang)
- `source_player_id`: 可选，直杠时被杠牌的来源玩家ID

## HTTP状态码

- `200` - 操作成功
- `400` - 请求参数错误
- `422` - 数据验证失败  
- `500` - 服务器内部错误

## 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

## 游戏逻辑说明

### 手牌减少规则

**碰牌:**
- 我(0): 减少2张手牌
- 其他玩家: 减少3张手牌

**杠牌:**
- 暗杠: 减少4张手牌
- 直杠: 我减少3张，其他玩家减少4张
- 加杠: 减少1张手牌

### 智能手牌管理
- 其他玩家操作时会自动补齐所需手牌
- 优先移除匹配的牌类型
- 确保操作的逻辑完整性 