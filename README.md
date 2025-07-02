# 欢乐麻将辅助工具

一个智能的麻将游戏辅助分析工具，帮助玩家做出最优的牌局决策。

## 功能特性

### 核心功能
- 🎯 **智能弃牌建议** - 基于当前牌面和剩余牌分析最优弃牌
- 📊 **剩余牌计算** - 实时计算场上剩余的所有牌型
- 🎲 **胡牌概率分析** - 计算不同弃牌选择下的胡牌概率
- 🔍 **听牌检测** - 自动检测当前是否听牌及听牌类型
- 📈 **牌局统计** - 详细的牌局进度和统计分析

### 界面特性
- 🎨 **直观的麻将牌面显示** - 高保真的麻将牌视觉界面
- 📱 **响应式布局** - 支持桌面和移动设备
- ⚡ **实时更新** - 牌局状态实时同步和分析
- 🎯 **智能提示** - 高亮显示推荐操作

## 技术架构

### 前端技术栈
- **React 18** - 现代化UI框架
- **TypeScript** - 类型安全的JavaScript
- **Tailwind CSS** - 实用优先的CSS框架
- **Zustand** - 轻量级状态管理
- **Framer Motion** - 流畅的动画效果
- **React Query** - 数据获取和缓存

### 后端技术栈
- **Python 3.11+** - 主要编程语言
- **FastAPI** - 高性能Web框架
- **Redis** - 内存数据库和缓存
- **Pydantic** - 数据验证和序列化
- **WebSocket** - 实时通信

### 算法引擎
- **麻将规则引擎** - 完整的麻将游戏规则实现
- **概率计算模块** - 基于蒙特卡洛方法的概率计算
- **AI决策树** - 智能的弃牌决策算法
- **牌型分析器** - 自动识别和分析牌型组合

## 项目结构

```
mahjong-assistant/
├── frontend/                 # 前端React应用
│   ├── src/
│   │   ├── components/      # React组件
│   │   ├── hooks/           # 自定义Hooks
│   │   ├── stores/          # Zustand状态管理
│   │   ├── types/           # TypeScript类型定义
│   │   ├── utils/           # 工具函数
│   │   └── assets/          # 静态资源
│   ├── public/
│   └── package.json
├── backend/                  # 后端Python应用
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务逻辑
│   │   └── algorithms/     # 麻将算法
│   ├── tests/
│   └── requirements.txt
├── docs/                    # 项目文档
└── README.md
```

## 核心算法设计

### 1. 牌面表示
- 使用数字编码表示麻将牌
- 万：1-9 (1-9)
- 条：1-9 (11-19)  
- 筒：1-9 (21-29)
- 字牌：东南西北中发白 (31-37)

### 2. 弃牌算法
- 计算每张牌的价值分数
- 考虑听牌概率、胡牌概率
- 结合剩余牌数量进行权重计算

### 3. 概率计算
- 蒙特卡洛模拟
- 基于当前牌面状态计算胡牌概率
- 考虑其他玩家的弃牌信息

## 安装和运行

### 环境要求
- Node.js 18+
- Python 3.11+
- Redis 6+

### 安装步骤

1. 克隆项目
```bash
git clone <repository-url>
cd mahjong-assistant
```

2. 安装前端依赖
```bash
cd frontend
npm install
```

3. 安装后端依赖
```bash
cd backend
pip install -r requirements.txt
```

4. 启动Redis服务
```bash
redis-server
```

5. 启动后端服务
```bash
cd backend
uvicorn app.main:app --reload
```

6. 启动前端服务
```bash
cd frontend
$env:PATH = ".\node_modules\.bin;$env:PATH"
react-scripts start
npm run start
```

## 使用说明

1. **输入手牌** - 在左侧输入区域选择您的手牌
2. **记录牌局** - 依次输入摸牌、碰牌、杠牌、弃牌信息
3. **获取建议** - 右侧将显示智能弃牌建议和概率分析
4. **查看剩余牌** - 实时查看场上剩余的所有牌型

## 贡献指南

欢迎提交Issue和Pull Request来帮助改进这个项目。

## 许可证

MIT License 
