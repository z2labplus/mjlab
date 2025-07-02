# WebSocket 迁移指南

本指南帮助您将现有的HTTP API调用迁移到WebSocket实时通信。

## 迁移概述

### 迁移前 (HTTP API)
```typescript
import MahjongApiClient from './services/MahjongApiClient';
import { useGameStore } from './stores/gameStore';

// 需要手动轮询获取状态
const gameState = await MahjongApiClient.getGameState();

// 每个操作都是独立的HTTP请求
await MahjongApiClient.addTileToHand(0, tile);
await MahjongApiClient.discardTile(0, 'wan', 1);
```

### 迁移后 (WebSocket)
```typescript
import { useWebSocketGameStore } from './stores/webSocketGameStore';

// 实时状态同步，无需轮询
const { gameState, addTileToHand, discardTile } = useWebSocketGameStore();

// 操作自动同步到所有客户端
await addTileToHand(0, tile);
await discardTile(0, tile);
```

## 详细迁移步骤

### 1. Store迁移

#### 旧版本 (gameStore.ts)
```typescript
import { useGameStore } from './stores/gameStore';

const {
  gameState,
  setGameState,
  addTileToHand,
  // ...其他方法
} = useGameStore();
```

#### 新版本 (webSocketGameStore.ts)
```typescript
import { useWebSocketGameStore } from './stores/webSocketGameStore';

const {
  gameState,
  setGameState,
  addTileToHand,
  // 新增的WebSocket相关状态
  connectionStatus,
  isConnected,
  lastError,
  
  // 连接控制
  initWebSocket,
  connect,
  disconnect,
} = useWebSocketGameStore();
```

### 2. 组件初始化

#### 在App.tsx中初始化WebSocket
```typescript
import { useWebSocketGameStore } from './stores/webSocketGameStore';

function App() {
  const { initWebSocket, connect } = useWebSocketGameStore();
  
  useEffect(() => {
    // 初始化WebSocket客户端
    const initWS = async () => {
      await initWebSocket('ws://localhost:8000/api/ws', 'default');
      // 自动连接
      await connect();
    };
    
    initWS().catch(console.error);
  }, []);

  // ...rest of component
}
```

### 3. API调用迁移

#### HTTP API调用
```typescript
// 旧方式：直接调用API客户端
import MahjongApiClient from './services/MahjongApiClient';

const handleAddTile = async () => {
  try {
    const response = await MahjongApiClient.addTileToHand(0, tile);
    // 手动更新状态
    setGameState(response.game_state);
  } catch (error) {
    console.error('操作失败:', error);
  }
};

const handleDiscardTile = async () => {
  const response = await MahjongApiClient.discardTile(0, 'wan', 1);
  setGameState(response.game_state);
};
```

#### WebSocket调用
```typescript
// 新方式：使用WebSocket store
const { addTileToHand, discardTile, isConnected } = useWebSocketGameStore();

const handleAddTile = async () => {
  if (!isConnected) return;
  
  try {
    // 状态会自动同步，无需手动设置
    await addTileToHand(0, tile);
  } catch (error) {
    console.error('操作失败:', error);
  }
};

const handleDiscardTile = async () => {
  if (!isConnected) return;
  await discardTile(0, tile);
};
```

### 4. 状态同步处理

#### HTTP API - 手动轮询
```typescript
// 需要定时轮询获取状态更新
useEffect(() => {
  const interval = setInterval(async () => {
    try {
      const response = await MahjongApiClient.getGameState();
      setGameState(response.game_state);
    } catch (error) {
      console.error('同步失败:', error);
    }
  }, 2000); // 每2秒轮询一次

  return () => clearInterval(interval);
}, []);
```

#### WebSocket - 自动实时同步
```typescript
// 无需轮询，状态自动实时同步
const { gameState } = useWebSocketGameStore();

// 可选：监听特定事件
useEffect(() => {
  const { addEventListener, removeEventListener } = useWebSocketGameStore.getState();
  
  const handlePlayerAction = (data: any) => {
    console.log('玩家操作:', data);
  };
  
  addEventListener('player_action_performed', handlePlayerAction);
  
  return () => {
    removeEventListener('player_action_performed', handlePlayerAction);
  };
}, []);
```

### 5. 连接状态处理

#### 新增连接状态管理
```typescript
import ConnectionStatus from './components/ConnectionStatus';

function App() {
  return (
    <div>
      {/* 显示WebSocket连接状态 */}
      <ConnectionStatus useWebSocket={true} />
      
      {/* 其他组件 */}
    </div>
  );
}
```

#### 处理连接错误
```typescript
const { lastError, connectionStatus, reconnectAttempts } = useWebSocketGameStore();

// 显示错误信息
{lastError && (
  <div className="error-message">
    连接错误: {lastError}
  </div>
)}

// 显示重连状态
{connectionStatus === ConnectionStatus.RECONNECTING && (
  <div className="reconnecting">
    正在重连... (尝试 {reconnectAttempts}/5)
  </div>
)}
```

### 6. 游戏操作API对照表

| 操作 | HTTP API | WebSocket API |
|------|----------|---------------|
| 获取游戏状态 | `MahjongApiClient.getGameState()` | 自动同步到 `gameState` |
| 设置游戏状态 | `MahjongApiClient.setGameState(state)` | `setGameState(state)` |
| 添加手牌 | `MahjongApiClient.addTileToHand(id, tile)` | `addTileToHand(id, tile)` |
| 弃牌 | `MahjongApiClient.discardTile(id, type, value)` | `discardTile(id, tile)` |
| 碰牌 | `MahjongApiClient.pengTile(...)` | `pengTile(id, tile, sourceId)` |
| 杠牌 | `MahjongApiClient.gangTile(...)` | `gangTile(id, tile, type, sourceId)` |
| 重置游戏 | `MahjongApiClient.resetGame()` | `resetGame()` |
| 设置当前玩家 | `MahjongApiClient.setCurrentPlayer(id)` | `setCurrentPlayer(id)` |
| 下一个玩家 | `MahjongApiClient.nextPlayer()` | `nextPlayer()` |
| 设置定缺 | `MahjongApiClient.setMissingSuit(...)` | `setMissingSuit(id, suit)` |
| 获取定缺 | `MahjongApiClient.getMissingSuits()` | `getMissingSuits()` |
| 导出牌谱 | `MahjongApiClient.exportGameRecord()` | `exportGameRecord()` |
| 导入牌谱 | `MahjongApiClient.importGameRecord(data)` | `importGameRecord(data)` |

### 7. 事件监听

WebSocket提供了丰富的事件监听能力：

```typescript
const { addEventListener, removeEventListener } = useWebSocketGameStore();

// 监听游戏状态更新
addEventListener('game_state_updated', (data) => {
  console.log('游戏状态更新:', data.game_state);
});

// 监听玩家操作
addEventListener('player_action_performed', (data) => {
  console.log('玩家操作:', data);
});

// 监听当前玩家变更
addEventListener('current_player_changed', (data) => {
  console.log('当前玩家变更:', data);
});

// 监听定缺设置
addEventListener('missing_suit_set', (data) => {
  console.log('定缺设置:', data);
});

// 监听游戏重置
addEventListener('game_reset', (data) => {
  console.log('游戏重置:', data);
});
```

### 8. 迁移检查清单

- [ ] 安装WebSocket依赖
- [ ] 创建WebSocket客户端服务
- [ ] 创建WebSocket Store
- [ ] 更新组件导入和状态管理
- [ ] 替换API调用为WebSocket方法
- [ ] 移除手动轮询代码
- [ ] 添加连接状态处理
- [ ] 添加错误处理和重连逻辑
- [ ] 测试所有功能
- [ ] 更新用户界面以显示实时状态

### 9. 兼容性考虑

如果需要同时支持HTTP和WebSocket：

```typescript
// 可以创建一个适配器组件
const useGameAPI = (useWebSocket: boolean = false) => {
  const httpStore = useGameStore();
  const wsStore = useWebSocketGameStore();
  
  return useWebSocket ? wsStore : httpStore;
};

// 在组件中使用
const gameAPI = useGameAPI(true); // 使用WebSocket
// 或
const gameAPI = useGameAPI(false); // 使用HTTP API
```

### 10. 性能优化

WebSocket相比HTTP API的优势：

1. **实时性**: 状态变化立即同步到所有客户端
2. **网络效率**: 减少HTTP请求开销
3. **用户体验**: 多人协作时状态同步无延迟
4. **服务器资源**: 减少轮询请求对服务器的压力

### 11. 调试和监控

启用WebSocket调试：

```typescript
// 在开发环境启用详细日志
if (process.env.NODE_ENV === 'development') {
  addEventListener('message', (data) => {
    console.log('WebSocket消息:', data);
  });
}
```

## 总结

迁移到WebSocket后，您将获得：
- 实时状态同步
- 更好的多人协作体验
- 减少网络请求
- 自动重连和错误处理
- 丰富的事件监听能力

遵循本指南逐步迁移，可以确保平滑过渡到WebSocket架构。