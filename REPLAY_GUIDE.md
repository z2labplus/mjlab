# 🎬 麻将牌谱回放系统使用指南

## 📋 功能概述

本系统是一个完整的腾讯欢乐麻将血战到底牌谱回放解决方案，类似雀魂的回放功能，支持：

- ✅ 完整的牌谱记录和导出
- ✅ 可视化回放界面
- ✅ 前进/后退/播放控制
- ✅ 多种播放速度
- ✅ 实时状态显示
- ✅ 牌谱导入/导出
- ✅ 操作历史追踪

## 🚀 快速开始

### 1. 启动后端服务
```bash
cd backend
python start_server.py
```

### 2. 启动前端服务
```bash
cd frontend
npm start
```

### 3. 创建示例牌谱
```bash
cd backend
python create_sample_replay.py
```

### 4. 使用回放功能
1. 打开前端页面
2. 点击顶部的 "🎬 牌谱回放" 切换到回放模式
3. 点击 "加载示例牌谱" 或上传JSON牌谱文件
4. 使用播放控制器观看回放

## 🎮 使用方法

### 模式切换
- **🎮 实时游戏**: WebSocket实时连接，可以进行实际的麻将游戏操作
- **🎬 牌谱回放**: 导入和回放历史牌谱，观看游戏过程

### 回放控制
- **▶️ 播放/暂停**: 自动播放牌谱
- **⏮️ 上一步/下一步 ⏭️**: 手动控制回放进度
- **重置**: 回到牌谱开始状态
- **播放速度**: 0.5x, 1x, 2x, 4x 多种速度选择
- **进度条**: 拖拽跳转到任意位置

### 牌谱导入
支持以下方式导入牌谱：
1. **拖拽上传**: 将JSON牌谱文件拖拽到上传区域
2. **文件选择**: 点击选择文件按钮
3. **示例牌谱**: 加载系统生成的示例牌谱
4. **API导入**: 从后端API获取已保存的牌谱

### 界面说明
- **麻将桌面**: 实时显示当前游戏状态
- **玩家信息**: 显示玩家详情、得分、定缺等
- **当前操作**: 高亮显示正在进行的操作
- **操作历史**: 显示最近的操作记录

## 🏗️ 系统架构

### 后端组件
```
backend/
├── app/models/game_record.py      # 牌谱数据模型
├── app/services/replay_service.py # 牌谱服务
├── app/api/v1/replay.py          # 牌谱API
├── create_sample_replay.py       # 示例牌谱生成器
└── start_server.py               # 服务启动脚本
```

### 前端组件
```
frontend/src/
├── components/
│   ├── ReplaySystem.tsx          # 主回放系统
│   ├── ReplayImporter.tsx        # 牌谱导入组件
│   └── MahjongTable.tsx          # 麻将桌面组件
├── stores/webSocketGameStore.ts   # WebSocket状态管理
└── App.tsx                       # 主应用入口
```

## 📊 牌谱格式

### JSON格式结构
```json
{
  "game_info": {
    "game_id": "游戏ID",
    "start_time": "开始时间",
    "end_time": "结束时间",
    "duration": "游戏时长(秒)",
    "player_count": 4,
    "game_mode": "xuezhan_daodi"
  },
  "players": [
    {
      "id": 0,
      "name": "玩家名称",
      "position": 0,
      "initial_hand": ["1万", "2万", ...],
      "missing_suit": "wan",
      "final_score": 100,
      "is_winner": true,
      "statistics": {
        "draw_count": 15,
        "discard_count": 14,
        "peng_count": 1,
        "gang_count": 2
      }
    }
  ],
  "actions": [
    {
      "sequence": 1,
      "timestamp": "操作时间",
      "player_id": 0,
      "action_type": "discard",
      "card": "5万",
      "target_player": null,
      "gang_type": null,
      "score_change": 0
    }
  ],
  "metadata": {
    "generated_at": "生成时间",
    "version": "1.0",
    "format": "xuezhan_mahjong"
  }
}
```

## 🔧 API接口

### 牌谱相关API
- `GET /api/v1/replay/{game_id}` - 获取牌谱
- `GET /api/v1/replay/{game_id}/export/json` - 导出JSON格式
- `GET /api/v1/replay/{game_id}/export/zip` - 导出ZIP格式
- `GET /api/v1/replay/list` - 获取牌谱列表
- `POST /api/v1/replay/{game_id}/share` - 创建分享链接
- `DELETE /api/v1/replay/{game_id}` - 删除牌谱

## 📈 扩展功能

### 已实现功能
- ✅ 基础回放控制
- ✅ 牌谱导入导出
- ✅ 可视化界面
- ✅ 操作历史
- ✅ 玩家信息显示

### 可扩展功能
- 🔄 牌谱分享和收藏
- 📱 移动端适配
- 🎵 音效和动画
- 📊 高级统计分析
- 🤖 AI分析和建议
- 🎥 视频导出

## 🐛 故障排除

### 常见问题

**Q: 前端显示"没有可用的示例牌谱"**
A: 需要先运行 `python create_sample_replay.py` 创建示例牌谱

**Q: WebSocket连接失败**
A: 确保后端服务正常运行，检查端口8000是否被占用

**Q: 牌谱导入失败**
A: 检查JSON文件格式是否正确，确保包含必要的字段

**Q: 回放界面显示异常**
A: 检查浏览器控制台错误信息，确保所有依赖正确安装

## 🎯 使用场景

1. **复盘分析**: 导入实际对局牌谱，分析决策和技巧
2. **教学演示**: 展示经典牌局，教授麻将技巧
3. **比赛回顾**: 回放重要比赛的精彩时刻
4. **数据分析**: 统计玩家表现和游戏模式
5. **分享交流**: 与朋友分享有趣的对局

## 📞 支持

如有问题或建议，请联系开发团队或提交Issue。

---

*🀄 享受血战到底的精彩回放体验！*