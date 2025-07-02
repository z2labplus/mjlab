# 麻将API设置和使用指南

## 🎯 开发完成

我已经为您开发了完整的后端API来操作麻将牌局！现在您可以通过HTTP请求来执行所有前端界面支持的操作。

## 📁 新增文件

### 后端代码
- `backend/app/models/mahjong.py` - 扩展了数据模型
- `backend/app/services/mahjong_game_service.py` - 新增游戏服务
- `backend/app/api/mahjong.py` - 扩展了API接口

### 文档  
- `.cursor/docs/api_usage_guide.md` - API使用指南
- `.cursor/docs/api_reference.md` - API详细参考
- `.cursor/docs/api_setup_guide.md` - 本文档

## 🚀 启动步骤

### 1. 启动后端服务

```bash
# 进入后端目录
cd backend

# 安装依赖（如果还没安装）
pip install -r requirements.txt

# 启动服务
python start_server.py
```

### 2. 验证服务

服务启动后访问：
- 服务器：http://localhost:8000
- API文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

## 🎮 核心API操作

### 最重要的接口

```bash
# 统一操作接口（推荐使用）
POST http://localhost:8000/api/mahjong/operation
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
# 对家碰7万（从上家）
curl -X POST "http://localhost:8000/api/mahjong/peng?player_id=2&tile_type=wan&tile_value=7&source_player_id=3"

# 下家直杠5筒（从对家）  
curl -X POST "http://localhost:8000/api/mahjong/gang?player_id=1&tile_type=tong&tile_value=5&gang_type=zhigang&source_player_id=2"

# 上家暗杠3万
curl -X POST "http://localhost:8000/api/mahjong/gang?player_id=3&tile_type=wan&tile_value=3&gang_type=angang"

# 获取游戏状态
curl -X GET "http://localhost:8000/api/mahjong/game-state"

# 重置游戏
curl -X POST "http://localhost:8000/api/mahjong/reset"
```

## 📊 玩家映射

- `0` = 我
- `1` = 下家
- `2` = 对家  
- `3` = 上家

## 🎴 牌类型

- `wan` = 万
- `tiao` = 条  
- `tong` = 筒

## 🔧 操作类型

- `hand` = 添加手牌
- `discard` = 弃牌
- `peng` = 碰牌
- `angang` = 暗杠
- `zhigang` = 直杠
- `jiagang` = 加杠

## 🧪 测试示例

### 完整流程测试

```bash
# 1. 重置游戏
curl -X POST "http://localhost:8000/api/mahjong/reset"

# 2. 对家碰7万（从上家）
curl -X POST "http://localhost:8000/api/mahjong/peng?player_id=2&tile_type=wan&tile_value=7&source_player_id=3"

# 3. 下家直杠5筒（从对家）
curl -X POST "http://localhost:8000/api/mahjong/gang?player_id=1&tile_type=tong&tile_value=5&gang_type=zhigang&source_player_id=2"

# 4. 上家暗杠3万
curl -X POST "http://localhost:8000/api/mahjong/gang?player_id=3&tile_type=wan&tile_value=3&gang_type=angang"

# 5. 查看最终状态
curl -X GET "http://localhost:8000/api/mahjong/game-state"
```

## ✨ 智能特性

1. **自动手牌管理** - 其他玩家操作时自动补齐所需手牌
2. **状态同步** - 每次操作后返回最新游戏状态  
3. **操作历史** - 所有操作记录在 `actions_history` 中
4. **错误处理** - 完善的错误信息和状态码

## 🛠️ 使用工具

### 命令行测试
使用 `curl` 命令测试（如上面示例）

### Postman测试
导入API文档：http://localhost:8000/docs

### Python测试
```python
import requests

# 对家碰7万
response = requests.post("http://localhost:8000/api/mahjong/operation", json={
    "player_id": 2,
    "operation_type": "peng", 
    "tile": {"type": "wan", "value": 7},
    "source_player_id": 3
})

print(response.json())
```

## 🎊 现在您可以：

1. **完全通过API控制牌局** - 不再需要手动点击前端界面
2. **批量操作** - 可以快速执行多个操作
3. **自动化测试** - 编写脚本自动测试各种场景
4. **外部集成** - 其他系统可以调用这些API
5. **数据分析** - 获取游戏状态进行分析

您现在拥有了前端界面+后端API的完整解决方案！🚀 