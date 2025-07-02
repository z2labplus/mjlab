# 血战麻将 API 使用指南

## 快速开始

### 1. 启动后端服务

```bash
cd backend
pip install -r requirements.txt
python start_server.py
```

服务地址：http://localhost:8000
API文档：http://localhost:8000/docs

### 2. 基础概念

**玩家ID映射：**
- 0 = 我
- 1 = 下家  
- 2 = 对家
- 3 = 上家

**牌类型：**
- wan = 万
- tiao = 条
- tong = 筒

**操作类型：**
- hand = 添加手牌
- discard = 弃牌
- peng = 碰牌
- angang = 暗杠
- zhigang = 直杠
- jiagang = 加杠

## 主要API接口

### 统一操作接口

```bash
POST /api/mahjong/operation
Content-Type: application/json

{
  "player_id": 2,
  "operation_type": "peng", 
  "tile": {"type": "wan", "value": 7},
  "source_player_id": 3
}
```

### 便捷接口

```bash
# 添加手牌
POST /api/mahjong/add-hand-tile?player_id=0&tile_type=wan&tile_value=7

# 弃牌
POST /api/mahjong/discard-tile?player_id=0&tile_type=wan&tile_value=5

# 碰牌
POST /api/mahjong/peng?player_id=2&tile_type=wan&tile_value=7&source_player_id=3

# 杠牌
POST /api/mahjong/gang?player_id=1&tile_type=tong&tile_value=5&gang_type=zhigang&source_player_id=2

# 获取游戏状态
GET /api/mahjong/game-state

# 重置游戏
POST /api/mahjong/reset
```

## 实际操作示例

### 对家碰7万（从上家）

```bash
curl -X POST "http://localhost:8000/api/mahjong/peng?player_id=2&tile_type=wan&tile_value=7&source_player_id=3"
```

### 下家直杠5筒（从对家）

```bash
curl -X POST "http://localhost:8000/api/mahjong/gang?player_id=1&tile_type=tong&tile_value=5&gang_type=zhigang&source_player_id=2"
```

### 上家暗杠3万

```bash
curl -X POST "http://localhost:8000/api/mahjong/gang?player_id=3&tile_type=wan&tile_value=3&gang_type=angang"
```

## 完整测试流程

```bash
# 1. 重置游戏
curl -X POST "http://localhost:8000/api/mahjong/reset"

# 2. 对家碰7万
curl -X POST "http://localhost:8000/api/mahjong/peng?player_id=2&tile_type=wan&tile_value=7&source_player_id=3"

# 3. 下家直杠5筒  
curl -X POST "http://localhost:8000/api/mahjong/gang?player_id=1&tile_type=tong&tile_value=5&gang_type=zhigang&source_player_id=2"

# 4. 查看结果
curl -X GET "http://localhost:8000/api/mahjong/game-state"
```

## 智能特性

- **自动手牌管理**：其他玩家进行操作时会自动补齐所需手牌
- **状态同步**：操作后自动更新游戏状态
- **历史记录**：所有操作都会记录在actions_history中

现在您可以通过这些API完全控制麻将牌局！🎊 