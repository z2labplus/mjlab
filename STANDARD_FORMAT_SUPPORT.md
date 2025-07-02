# 标准格式牌谱支持文档

## 📋 概述

系统现在完全支持新的标准化牌谱格式 (`model/first_hand/sample_mahjong_game_final.json`)，无需转换即可在前端和后端使用。

## 🎯 支持的格式

### 1. 标准格式 (推荐)
```json
{
  "game_info": {
    "game_id": "sample_game_008",
    "description": "游戏描述"
  },
  "initial_hands": {
    "0": {
      "tiles": ["1万", "2条", "3筒"],
      "count": 13,
      "source": "known"
    }
  },
  "actions": [
    {
      "sequence": 1,
      "player_id": 0,
      "type": "discard",
      "tile": "1万"
    }
  ],
  "final_hands": { ... },
  "mjtype": "xuezhan_daodi",
  "misssuit": {"0": "万"}
}
```

### 2. 传统格式 (兼容)
```json
{
  "game_info": { ... },
  "players": [
    {
      "id": 0,
      "name": "玩家1",
      "initial_hand": ["1万", "2条"]
    }
  ],
  "actions": [ ... ]
}
```

## 🚀 使用方式

### 前端导入
1. **拖拽导入**：直接拖拽 `.json` 文件到前端
2. **文件选择**：点击"选择文件"按钮选择牌谱文件
3. **示例加载**：点击"加载示例牌谱"自动使用标准格式

### 后端API
```bash
# 导入默认标准格式牌谱
curl -X POST "/api/v1/replay/standard/import/default"

# 导入自定义标准格式文件  
curl -X POST "/api/v1/replay/standard/import?file_path=/path/to/file.json"

# 获取标准格式支持状态
curl "/api/v1/replay/standard/status"
```

### 命令行工具
```bash
# 自动导入（推荐）
python import_standard_replay.py --action=auto

# 导入指定文件
python import_standard_replay.py --action=import --file=/path/to/file.json

# 运行完整测试
python test_standard_format_support.py
```

## 🔧 转换逻辑

### 前端自动转换
前端会自动检测文件格式：
- 如果是标准格式（含 `initial_hands`），自动转换为传统格式
- 如果是传统格式（含 `players`），直接使用
- 转换过程透明，用户无感知

### 转换示例
```javascript
// 标准格式输入
{
  "initial_hands": {
    "0": {"tiles": ["1万", "2条"]}
  }
}

// 自动转换为
{
  "players": [
    {
      "id": 0,
      "initial_hand": ["1万", "2条"]
    }
  ]
}
```

## 🛠️ 技术实现

### 后端组件
- `app/models/standard_replay.py` - 标准格式数据模型
- `app/services/standard_replay_service.py` - 标准格式解析服务  
- `app/api/v1/replay.py` - 扩展的API端点

### 前端组件
- `ReplayImporter.tsx` - 增强的导入组件，支持格式自动检测和转换

## ✅ 验证测试

运行以下测试确保系统正常：

```bash
# 1. 系统状态检查
python import_standard_replay.py --action=status

# 2. 前端导入测试  
python test_frontend_import.py

# 3. 完整功能测试
python test_standard_format_support.py
```

## 🎉 优势

1. **无缝兼容** - 支持新旧两种格式
2. **自动转换** - 前端智能检测和转换
3. **向后兼容** - 现有功能不受影响
4. **标准化数据** - 使用统一的 `initial_hands` 和 `final_hands`
5. **易于扩展** - 可轻松添加更多标准格式支持

## 📝 文件位置

- **标准格式文件**：`/root/claude/hmjai/model/first_hand/sample_mahjong_game_final.json`
- **管理脚本**：`/root/claude/hmjai/backend/import_standard_replay.py`
- **测试脚本**：`/root/claude/hmjai/backend/test_standard_format_support.py`
- **前端组件**：`/root/claude/hmjai/frontend/src/components/ReplayImporter.tsx`

---

**现在您可以直接在前端导入标准格式文件，系统会自动处理格式转换！** 🚀