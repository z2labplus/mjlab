# 血战麻将项目 - 架构设计文档

## 项目概述

血战麻将辅助分析工具是一个智能化的麻将游戏助手，采用现代化的前后端分离架构，为玩家提供实时的游戏分析、智能弃牌建议和胡牌概率计算服务。

## 系统架构

### 整体架构图

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端应用       │    │   后端API服务    │    │   数据存储层     │
│  (React+TS)     │◄──►│  (FastAPI)      │◄──►│   (Redis)      │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ 游戏界面    │ │    │ │ API路由     │ │    │ │ 游戏状态    │ │
│ │ 牌型显示    │ │    │ │ WebSocket   │ │    │ │ 缓存数据    │ │
│ │ 操作控制    │ │    │ │ 业务逻辑    │ │    │ │ 会话管理    │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │                 │
│ │ 状态管理    │ │    │ │ 麻将引擎    │ │    │                 │
│ │ 实时通信    │ │    │ │ 概率计算    │ │    │                 │
│ │ 动画效果    │ │    │ │ 决策算法    │ │    │                 │
│ └─────────────┘ │    │ └─────────────┘ │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 技术选型原则

#### 前端技术选型
- **React 18**: 提供现代化的组件化开发体验，支持并发特性
- **TypeScript**: 确保代码类型安全，提高开发效率和代码质量
- **Tailwind CSS**: 原子化CSS框架，快速构建响应式界面
- **Zustand**: 轻量级状态管理，替代复杂的Redux
- **Framer Motion**: 提供流畅的动画效果，增强用户体验

#### 后端技术选型
- **FastAPI**: 高性能异步Web框架，自动生成API文档
- **Python 3.11+**: 利用最新语言特性，提高开发效率
- **Pydantic**: 数据验证和序列化，确保API数据质量
- **Redis**: 高性能内存数据库，适合游戏状态存储

## 核心模块设计

### 1. 前端架构设计

#### 组件层次结构
```
App
├── GameLayout
│   ├── GameBoard
│   │   ├── PlayerHand
│   │   ├── DiscardPile
│   │   ├── DeckDisplay
│   │   └── ActionButtons
│   ├── AnalysisPanel
│   │   ├── SuggestedDiscard
│   │   ├── ProbabilityDisplay
│   │   ├── RemainingCards
│   │   └── AvailableActions
│   └── ControlPanel
│       ├── GameSettings
│       ├── PlayerSettings
│       └── GameHistory
└── ErrorBoundary
```

#### 状态管理架构
```typescript
// 游戏状态存储
interface GameStore {
  // 游戏基础状态
  gameId: string;
  players: Player[];
  currentPlayer: number;
  gamePhase: GamePhase;
  
  // 牌局状态
  deck: MahjongCard[];
  discardPile: MahjongCard[];
  
  // 分析结果
  analysis: GameAnalysis;
  
  // 操作方法
  actions: {
    createGame: () => Promise<void>;
    drawCard: () => Promise<void>;
    discardCard: (card: MahjongCard) => Promise<void>;
    analyzeCurrent: () => Promise<void>;
  }
}
```

### 2. 后端架构设计

#### 分层架构
```
┌─────────────────────────────────────────────────┐
│                 API层 (FastAPI)                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │   游戏API   │ │   玩家API   │ │  WebSocket  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│                业务逻辑层 (Services)             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │  游戏服务   │ │  玩家服务   │ │  分析服务   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│              算法引擎层 (Algorithms)             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │  麻将引擎   │ │  概率计算   │ │  决策算法   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│                数据层 (Redis)                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │  游戏状态   │ │  缓存数据   │ │  会话管理   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ │
└─────────────────────────────────────────────────┘
```

#### 数据流设计
```
用户操作 → API接口 → 数据验证 → 业务逻辑 → 算法计算 → 状态更新 → 响应返回
    ↓         ↓         ↓         ↓         ↓         ↓         ↓
  React     FastAPI   Pydantic  Services  Algorithms  Redis   WebSocket
```

### 3. 麻将算法引擎设计

#### 核心算法模块
```python
class MahjongEngine:
    """麻将规则引擎核心类"""
    
    # 胡牌检测模块
    def can_win(self, hand_cards: List[MahjongCard]) -> bool
    
    # 听牌分析模块
    def analyze_ready_hand(self, hand_cards: List[MahjongCard]) -> ReadyHandInfo
    
    # 弃牌建议模块
    def suggest_discard(self, hand_cards: List[MahjongCard]) -> MahjongCard
    
    # 操作检测模块
    def get_available_actions(self, hand_cards: List[MahjongCard]) -> List[Action]
```

#### 概率计算引擎
```python
class ProbabilityCalculator:
    """概率计算引擎"""
    
    # 蒙特卡洛模拟
    def monte_carlo_simulation(self, scenarios: int = 10000) -> float
    
    # 胡牌概率计算
    def calculate_win_probability(self, hand_cards, remaining_cards) -> float
    
    # 摸牌概率分析
    def analyze_draw_probability(self, needed_cards, remaining_cards) -> dict
```

## 数据模型设计

### 1. 核心数据结构

#### 麻将牌模型
```typescript
interface MahjongCard {
  id: number;              // 牌的唯一标识 (1-29)
  suit: 'wan' | 'tiao' | 'tong';  // 花色：万、条、筒
  value: number;           // 牌面值 (1-9)
  isSelected?: boolean;    // 是否被选中
}
```

#### 玩家手牌模型
```typescript
interface PlayerHand {
  cards: MahjongCard[];    // 手牌
  melds: Meld[];          // 明刻/明杠
  missing_suit: CardSuit; // 缺的花色
  is_ready: boolean;      // 是否听牌
}
```

#### 游戏状态模型
```typescript
interface GameState {
  gameId: string;         // 游戏ID
  players: Player[];      // 玩家列表
  currentPlayer: number;  // 当前玩家索引
  deck: MahjongCard[];   // 剩余牌库
  discardPile: MahjongCard[]; // 弃牌堆
  round: number;         // 当前局数
  phase: GamePhase;      // 游戏阶段
}
```

### 2. API接口设计

#### RESTful API规范
```
POST   /api/v1/game/create          # 创建游戏
GET    /api/v1/game/{game_id}       # 获取游戏状态
POST   /api/v1/game/{game_id}/draw  # 摸牌
POST   /api/v1/game/{game_id}/discard # 弃牌
POST   /api/v1/game/{game_id}/analyze # 游戏分析
GET    /api/v1/game/{game_id}/players # 获取玩家列表
```

#### WebSocket消息格式
```typescript
interface WebSocketMessage {
  type: 'game_action' | 'game_update' | 'error' | 'chat';
  data: any;
  timestamp: number;
  playerId?: string;
}
```

## 性能优化设计

### 1. 前端性能优化

#### 组件优化策略
- **React.memo**: 避免不必要的组件重渲染
- **useMemo/useCallback**: 缓存计算结果和函数引用
- **代码分割**: 按路由和功能模块进行代码分割
- **虚拟滚动**: 大量数据列表使用虚拟滚动

#### 状态管理优化
- **选择性订阅**: 仅订阅需要的状态变化
- **数据标准化**: 避免深层嵌套的状态结构
- **批量更新**: 合并多个状态更新操作

### 2. 后端性能优化

#### 异步处理策略
- **异步I/O**: 所有数据库和网络操作使用异步
- **并发处理**: 使用asyncio并发处理多个请求
- **后台任务**: 耗时操作放到后台异步处理

#### 缓存策略
- **Redis缓存**: 游戏状态和计算结果缓存
- **内存缓存**: 常用数据的内存缓存
- **CDN缓存**: 静态资源CDN分发

### 3. 算法性能优化

#### 计算优化
- **预计算**: 常用牌型组合预计算
- **动态规划**: 复杂胡牌判断使用动态规划
- **并行计算**: 概率计算使用多进程并行

#### 数据结构优化
- **位运算**: 牌型表示使用位运算优化
- **哈希表**: 快速查找使用哈希表
- **堆栈优化**: 递归算法优化为迭代

## 安全性设计

### 1. 数据安全
- **输入验证**: 所有用户输入严格验证
- **SQL注入防护**: 使用参数化查询
- **XSS防护**: 前端输出转义
- **CSRF防护**: 使用CSRF令牌

### 2. 通信安全
- **HTTPS加密**: 生产环境强制HTTPS
- **WebSocket安全**: WSS加密连接
- **API限流**: 防止恶意调用
- **身份验证**: JWT令牌验证

### 3. 游戏安全
- **作弊检测**: 异常操作检测
- **状态验证**: 游戏状态一致性验证
- **操作记录**: 详细的操作日志
- **回滚机制**: 异常状态回滚

## 监控和运维

### 1. 日志系统
- **结构化日志**: JSON格式日志
- **分级日志**: DEBUG/INFO/WARN/ERROR
- **集中收集**: ELK或类似方案
- **实时监控**: 关键指标实时监控

### 2. 性能监控
- **响应时间**: API响应时间监控
- **错误率**: 错误率统计和告警
- **资源使用**: CPU/内存/网络监控
- **用户行为**: 用户操作路径分析

### 3. 部署策略
- **容器化**: Docker容器部署
- **负载均衡**: Nginx负载均衡
- **自动扩容**: 基于负载自动扩容
- **灰度发布**: 渐进式功能发布

## 扩展性设计

### 1. 功能扩展
- **插件架构**: 支持算法插件扩展
- **规则引擎**: 支持不同麻将规则
- **多语言**: 国际化支持
- **主题定制**: 界面主题系统

### 2. 技术扩展
- **微服务**: 服务拆分和独立部署
- **消息队列**: 异步消息处理
- **数据库**: 支持多种数据库
- **云原生**: 支持云平台部署

### 3. 业务扩展
- **多人对战**: 支持在线多人游戏
- **比赛系统**: 支持比赛和排行榜
- **社交功能**: 好友系统和聊天
- **AI训练**: 机器学习模型训练 