import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { 
  GameState, 
  AnalysisResult, 
  Tile, 
  HandTiles, 
  PlayerAction,
  TileInfo,
  MeldType,
  Meld,
  TileType,
  GangType,
  Winner
} from '../types/mahjong';
import { WebSocketClient, ConnectionStatus } from '../services/WebSocketClient';
import { useWebSocket } from '../hooks/useWebSocket';
import { MahjongAPI } from '../utils/api';

interface WebSocketGameStore {
  // WebSocket连接相关
  wsClient: WebSocketClient | null;
  connectionStatus: ConnectionStatus;
  isConnected: boolean;
  reconnectAttempts: number;
  roomId: string;
  clientId: string | null;
  lastError: string | null;
  
  // 游戏状态
  gameState: GameState;
  analysisResult: AnalysisResult | null;
  isAnalyzing: boolean;
  
  // 可用牌信息
  availableTiles: TileInfo[];
  
  // 实时更新状态
  lastSyncTime: Date | null;
  isLoading: boolean;
  
  // Actions - WebSocket连接管理
  initWebSocket: (url?: string, roomId?: string, clientId?: string) => Promise<void>;
  connect: () => Promise<void>;
  disconnect: () => void;
  setConnectionStatus: (status: ConnectionStatus, attempts?: number) => void;
  setLastError: (error: string | null) => void;
  
  // Actions - 游戏状态管理
  setGameState: (gameState: GameState) => void;
  syncGameStateFromWS: () => Promise<void>;
  syncGameStateFromAPI: () => Promise<void>;
  setAnalysisResult: (result: AnalysisResult) => void;
  setIsAnalyzing: (analyzing: boolean) => void;
  setAvailableTiles: (tiles: TileInfo[]) => void;
  setIsLoading: (loading: boolean) => void;
  
  // Actions - 智能分析
  triggerAutoAnalysis: () => Promise<void>;
  
  // Actions - 游戏操作（通过WebSocket）
  addTileToHand: (playerId: number, tile: Tile) => Promise<void>;
  discardTile: (playerId: number, tile: Tile) => Promise<void>;
  pengTile: (playerId: number, tile: Tile, sourcePlayerId?: number) => Promise<void>;
  gangTile: (playerId: number, tile: Tile, gangType: string, sourcePlayerId?: number) => Promise<void>;
  
  // Actions - 游戏控制
  resetGame: () => Promise<void>;
  setCurrentPlayer: (playerId: number) => Promise<void>;
  nextPlayer: () => Promise<void>;
  
  // Actions - 定缺操作
  setMissingSuit: (playerId: number, missingSuit: string) => Promise<void>;
  getMissingSuits: () => Promise<Record<string, string | null>>;
  resetMissingSuits: () => Promise<void>;
  
  // Actions - 牌谱操作
  exportGameRecord: () => Promise<any>;
  importGameRecord: (gameRecord: any) => Promise<void>;
  
  // Actions - 本地游戏状态操作（用于兼容现有代码）
  addTileToHandLocal: (playerId: number, tile: Tile) => void;
  removeTileFromHand: (playerId: number, tile: Tile) => void;
  reduceHandTilesCount: (playerId: number, count: number, preferredTile?: Tile) => void;
  addDiscardedTile: (tile: Tile, playerId: number) => void;
  addMeld: (playerId: number, meld: Meld) => void;
  reorderPlayerHand: (playerId: number, newTiles: Tile[]) => void;
  addAction: (action: PlayerAction) => void;
  setPlayerMissingSuit: (playerId: number, missingSuit: string | null) => void;
  setPlayerWinner: (playerId: number, isWinner: boolean, winType?: string, winTile?: Tile, dianpaoPlayerId?: number) => void;
  checkForWinners: () => Winner[];
}

// 默认游戏状态
const defaultGameState: GameState = {
  game_id: 'default',
  player_hands: {
    '0': { tiles: [], tile_count: 0, melds: [] },
    '1': { tiles: null, tile_count: 0, melds: [] },
    '2': { tiles: null, tile_count: 0, melds: [] },
    '3': { tiles: null, tile_count: 0, melds: [] }
  },
  player_discarded_tiles: {
    '0': [], '1': [], '2': [], '3': []
  },
  discarded_tiles: [],
  actions_history: [],
  current_player: 0,
  game_started: false,
  game_ended: false,
  show_all_hands: false
};

export const useWebSocketGameStore = create<WebSocketGameStore>()(
  subscribeWithSelector((set, get) => ({
    // WebSocket连接相关初始状态
    wsClient: null,
    connectionStatus: ConnectionStatus.DISCONNECTED,
    isConnected: false,
    reconnectAttempts: 0,
    roomId: 'default',
    clientId: null,
    lastError: null,
    
    // 游戏状态初始值
    gameState: defaultGameState,
    analysisResult: null,
    isAnalyzing: false,
    availableTiles: [],
    lastSyncTime: null,
    isLoading: false,
    
    // WebSocket连接管理
    initWebSocket: async (url = 'ws://localhost:8000/api/ws', roomId = 'default', clientId) => {
      const client = new WebSocketClient(url, roomId, clientId);
      
      // 设置事件监听器
      client.on('connectionStatusChange', (data) => {
        set({ 
          connectionStatus: data.status,
          isConnected: data.status === ConnectionStatus.CONNECTED,
          reconnectAttempts: data.reconnectAttempts 
        });
      });
      
      client.on('game_state_updated', (data) => {
        set({ 
          gameState: data.game_state,
          lastSyncTime: new Date()
        });
      });
      
      client.on('player_action_performed', (data) => {
        set({ 
          gameState: data.game_state,
          lastSyncTime: new Date()
        });
      });
      
      client.on('current_player_changed', (data) => {
        set({ 
          gameState: data.game_state,
          lastSyncTime: new Date()
        });
      });
      
      client.on('missing_suit_set', (data) => {
        set({ 
          gameState: data.game_state,
          lastSyncTime: new Date()
        });
      });
      
      client.on('missing_suits_reset', (data) => {
        set({ 
          gameState: data.game_state,
          lastSyncTime: new Date()
        });
      });
      
      client.on('game_reset', (data) => {
        set({ 
          gameState: data.game_state,
          lastSyncTime: new Date()
        });
      });
      
      client.on('game_record_imported', (data) => {
        set({ 
          gameState: data.game_state,
          lastSyncTime: new Date()
        });
      });
      
      client.on('error', (error) => {
        set({ lastError: error.message || '未知错误' });
      });
      
      set({ 
        wsClient: client,
        roomId,
        clientId: client.getClientId()
      });
    },
    
    connect: async () => {
      const { wsClient } = get();
      if (wsClient) {
        try {
          set({ isLoading: true, lastError: null });
          await wsClient.connect();
          
          // 连接成功后同步游戏状态
          await get().syncGameStateFromWS();
        } catch (error: any) {
          set({ lastError: error.message });
          throw error;
        } finally {
          set({ isLoading: false });
        }
      }
    },
    
    disconnect: () => {
      const { wsClient } = get();
      if (wsClient) {
        wsClient.disconnect();
      }
    },
    
    setConnectionStatus: (status, attempts = 0) => {
      set({ 
        connectionStatus: status,
        isConnected: status === ConnectionStatus.CONNECTED,
        reconnectAttempts: attempts
      });
    },
    
    setLastError: (error) => {
      set({ lastError: error });
    },
    
    // 游戏状态管理
    setGameState: (gameState) => {
      set({ 
        gameState,
        lastSyncTime: new Date()
      });
    },
    
    syncGameStateFromWS: async () => {
      const { wsClient } = get();
      if (wsClient && wsClient.isConnected()) {
        try {
          const gameState = await wsClient.getGameState();
          set({ 
            gameState,
            lastSyncTime: new Date()
          });
        } catch (error: any) {
          set({ lastError: error.message });
          throw error;
        }
      }
    },
    
    syncGameStateFromAPI: async () => {
      try {
        // 获取当前状态用于比较
        const currentState = get().gameState;
        const previousPlayer0TileCount = currentState.player_hands['0']?.tiles?.length || 0;
        
        // 通过HTTP API获取游戏状态
        const response = await fetch('http://localhost:8000/api/mahjong/game-state');
        const result = await response.json();
        
        if (result.success && result.game_state) {
          const newState = result.game_state;
          const newPlayer0TileCount = newState.player_hands['0']?.tiles?.length || 0;
          
          // 🎯 检测玩家0是否摸牌（手牌数量增加）
          const player0DrewTile = newPlayer0TileCount > previousPlayer0TileCount;
          
          set({ 
            gameState: newState,
            lastSyncTime: new Date()
          });
          
          console.log('🔄🔄🔄 从API同步游戏状态成功 🔄🔄🔄');
          console.log('📊📊📊 同步后的状态 📊📊📊', {
            show_all_hands: newState.show_all_hands,
            game_ended: newState.game_ended,
            player0_previous_tiles: previousPlayer0TileCount,
            player0_current_tiles: newPlayer0TileCount,
            player0_drew_tile: player0DrewTile,
            player1_tiles: newState.player_hands?.['1']?.tiles?.length || 'null',
            player2_tiles: newState.player_hands?.['2']?.tiles?.length || 'null',
            player3_tiles: newState.player_hands?.['3']?.tiles?.length || 'null'
          });
          
          // 🔧 关键修复：玩家0摸牌后自动分析
          if (player0DrewTile && !newState.game_ended) {
            console.log('🎯 检测到玩家0摸牌，自动开始分析...');
            // 延迟一点点执行，确保状态已更新
            setTimeout(() => {
              get().triggerAutoAnalysis();
            }, 100);
          } else {
            // 其他玩家操作时，保持现有的分析结果不变
            console.log('📊 其他玩家操作，保持当前分析结果');
          }
        } else {
          console.warn('⚠️ API返回状态异常:', result);
        }
      } catch (error: any) {
        console.error('❌ 从API同步游戏状态失败:', error);
        set({ lastError: error.message });
      }
    },
    
    setAnalysisResult: (result) => {
      set({ analysisResult: result });
    },
    
    setIsAnalyzing: (analyzing) => {
      set({ isAnalyzing: analyzing });
    },
    
    setAvailableTiles: (tiles) => {
      set({ availableTiles: tiles });
    },
    
    setIsLoading: (loading) => {
      set({ isLoading: loading });
    },
    
    // 游戏操作（通过WebSocket）
    addTileToHand: async (playerId, tile) => {
      const { wsClient } = get();
      if (wsClient && wsClient.isConnected()) {
        try {
          set({ isLoading: true });
          await wsClient.playerAction('hand', playerId, tile);
        } catch (error: any) {
          set({ lastError: error.message });
          throw error;
        } finally {
          set({ isLoading: false });
        }
      } else {
        throw new Error('WebSocket未连接');
      }
    },
    
    discardTile: async (playerId, tile) => {
      const { wsClient } = get();
      if (wsClient && wsClient.isConnected()) {
        try {
          set({ isLoading: true });
          await wsClient.playerAction('discard', playerId, tile);
        } catch (error: any) {
          set({ lastError: error.message });
          throw error;
        } finally {
          set({ isLoading: false });
        }
      } else {
        throw new Error('WebSocket未连接');
      }
    },
    
    pengTile: async (playerId, tile, sourcePlayerId) => {
      const { wsClient } = get();
      if (wsClient && wsClient.isConnected()) {
        try {
          set({ isLoading: true });
          await wsClient.playerAction('peng', playerId, tile, sourcePlayerId);
        } catch (error: any) {
          set({ lastError: error.message });
          throw error;
        } finally {
          set({ isLoading: false });
        }
      } else {
        throw new Error('WebSocket未连接');
      }
    },
    
    gangTile: async (playerId, tile, gangType, sourcePlayerId) => {
      const { wsClient } = get();
      if (wsClient && wsClient.isConnected()) {
        try {
          set({ isLoading: true });
          await wsClient.playerAction(gangType, playerId, tile, sourcePlayerId);
        } catch (error: any) {
          set({ lastError: error.message });
          throw error;
        } finally {
          set({ isLoading: false });
        }
      } else {
        throw new Error('WebSocket未连接');
      }
    },
    
    // 游戏控制
    resetGame: async () => {
      const { wsClient } = get();
      if (wsClient && wsClient.isConnected()) {
        try {
          set({ isLoading: true });
          await wsClient.resetGame();
        } catch (error: any) {
          set({ lastError: error.message });
          throw error;
        } finally {
          set({ isLoading: false });
        }
      } else {
        throw new Error('WebSocket未连接');
      }
    },
    
    setCurrentPlayer: async (playerId) => {
      const { wsClient } = get();
      if (wsClient && wsClient.isConnected()) {
        try {
          await wsClient.setCurrentPlayer(playerId);
        } catch (error: any) {
          set({ lastError: error.message });
          throw error;
        }
      } else {
        throw new Error('WebSocket未连接');
      }
    },
    
    nextPlayer: async () => {
      const { wsClient } = get();
      if (wsClient && wsClient.isConnected()) {
        try {
          await wsClient.nextPlayer();
        } catch (error: any) {
          set({ lastError: error.message });
          throw error;
        }
      } else {
        throw new Error('WebSocket未连接');
      }
    },
    
    // 定缺操作
    setMissingSuit: async (playerId, missingSuit) => {
      const { wsClient } = get();
      if (wsClient && wsClient.isConnected()) {
        try {
          await wsClient.setMissingSuit(playerId, missingSuit);
        } catch (error: any) {
          set({ lastError: error.message });
          throw error;
        }
      } else {
        throw new Error('WebSocket未连接');
      }
    },
    
    getMissingSuits: async () => {
      const { wsClient } = get();
      if (wsClient && wsClient.isConnected()) {
        try {
          return await wsClient.getMissingSuits();
        } catch (error: any) {
          set({ lastError: error.message });
          throw error;
        }
      } else {
        throw new Error('WebSocket未连接');
      }
    },
    
    resetMissingSuits: async () => {
      const { wsClient } = get();
      if (wsClient && wsClient.isConnected()) {
        try {
          await wsClient.resetMissingSuits();
        } catch (error: any) {
          set({ lastError: error.message });
          throw error;
        }
      } else {
        throw new Error('WebSocket未连接');
      }
    },
    
    // 牌谱操作
    exportGameRecord: async () => {
      const { wsClient } = get();
      if (wsClient && wsClient.isConnected()) {
        try {
          return await wsClient.exportGameRecord();
        } catch (error: any) {
          set({ lastError: error.message });
          throw error;
        }
      } else {
        throw new Error('WebSocket未连接');
      }
    },
    
    importGameRecord: async (gameRecord) => {
      const { wsClient } = get();
      if (wsClient && wsClient.isConnected()) {
        try {
          set({ isLoading: true });
          await wsClient.importGameRecord(gameRecord);
        } catch (error: any) {
          set({ lastError: error.message });
          throw error;
        } finally {
          set({ isLoading: false });
        }
      } else {
        throw new Error('WebSocket未连接');
      }
    },
    
    // 本地游戏状态操作（用于兼容现有代码）
    addTileToHandLocal: (playerId, tile) => {
      set((state) => {
        const newState = { ...state };
        const playerIdStr = playerId.toString();
        
        if (playerId === 0) {
          // 玩家0：添加具体牌面
          if (newState.gameState.player_hands[playerIdStr].tiles) {
            const tiles = [...(newState.gameState.player_hands[playerIdStr].tiles as Tile[])];
            tiles.push(tile);
            
            // 排序
            tiles.sort((a, b) => {
              if (a.type !== b.type) {
                const typeOrder = { 'wan': 0, 'tiao': 1, 'tong': 2, 'zi': 3 };
                return typeOrder[a.type as keyof typeof typeOrder] - typeOrder[b.type as keyof typeof typeOrder];
              }
              return a.value - b.value;
            });
            
            newState.gameState.player_hands[playerIdStr].tiles = tiles;
          }
        } else {
          // 其他玩家：只增加牌数
          newState.gameState.player_hands[playerIdStr].tile_count += 1;
        }
        
        return newState;
      });
    },
    
    removeTileFromHand: (playerId, tile) => {
      set((state) => {
        const newState = { ...state };
        const playerIdStr = playerId.toString();
        
        if (playerId === 0 && newState.gameState.player_hands[playerIdStr].tiles) {
          const tiles = [...(newState.gameState.player_hands[playerIdStr].tiles as Tile[])];
          const index = tiles.findIndex(t => t.type === tile.type && t.value === tile.value);
          if (index !== -1) {
            tiles.splice(index, 1);
            newState.gameState.player_hands[playerIdStr].tiles = tiles;
          }
        } else {
          // 其他玩家：减少牌数
          const currentCount = newState.gameState.player_hands[playerIdStr].tile_count;
          newState.gameState.player_hands[playerIdStr].tile_count = Math.max(0, currentCount - 1);
        }
        
        return newState;
      });
    },
    
    reduceHandTilesCount: (playerId, count, preferredTile) => {
      set((state) => {
        const newState = { ...state };
        const playerIdStr = playerId.toString();
        
        if (playerId === 0 && preferredTile && newState.gameState.player_hands[playerIdStr].tiles) {
          // 玩家0：尝试移除指定牌
          const tiles = [...(newState.gameState.player_hands[playerIdStr].tiles as Tile[])];
          for (let i = 0; i < count; i++) {
            const index = tiles.findIndex(t => t.type === preferredTile.type && t.value === preferredTile.value);
            if (index !== -1) {
              tiles.splice(index, 1);
            } else if (tiles.length > 0) {
              tiles.pop(); // 如果找不到指定牌，移除最后一张
            }
          }
          newState.gameState.player_hands[playerIdStr].tiles = tiles;
        } else {
          // 其他玩家：减少牌数
          const currentCount = newState.gameState.player_hands[playerIdStr].tile_count;
          newState.gameState.player_hands[playerIdStr].tile_count = Math.max(0, currentCount - count);
        }
        
        return newState;
      });
    },
    
    addDiscardedTile: (tile, playerId) => {
      set((state) => {
        const newState = { ...state };
        const playerIdStr = playerId.toString();
        
        // 添加到玩家弃牌
        newState.gameState.player_discarded_tiles[playerIdStr] = [
          ...newState.gameState.player_discarded_tiles[playerIdStr],
          tile
        ];
        
        // 添加到公共弃牌
        newState.gameState.discarded_tiles = [
          ...newState.gameState.discarded_tiles,
          tile
        ];
        
        return newState;
      });
    },
    
    addMeld: (playerId, meld) => {
      set((state) => {
        const newState = { ...state };
        const playerIdStr = playerId.toString();
        
        newState.gameState.player_hands[playerIdStr].melds = [
          ...newState.gameState.player_hands[playerIdStr].melds,
          meld
        ];
        
        return newState;
      });
    },
    
    reorderPlayerHand: (playerId, newTiles) => {
      if (playerId === 0) {
        set((state) => {
          const newState = { ...state };
          newState.gameState.player_hands['0'].tiles = newTiles;
          return newState;
        });
      }
    },
    
    addAction: (action) => {
      set((state) => {
        const newState = { ...state };
        newState.gameState.actions_history = [
          ...newState.gameState.actions_history,
          action
        ];
        return newState;
      });
    },
    
    setPlayerMissingSuit: (playerId, missingSuit) => {
      set((state) => {
        const newState = { ...state };
        const playerIdStr = playerId.toString();
        
        if (!newState.gameState.player_hands[playerIdStr]) {
          newState.gameState.player_hands[playerIdStr] = {
            tiles: playerId === 0 ? [] : null,
            tile_count: 0,
            melds: []
          };
        }
        
        (newState.gameState.player_hands[playerIdStr] as any).missing_suit = missingSuit;
        
        return newState;
      });
    },
    
    setPlayerWinner: (playerId, isWinner, winType, winTile, dianpaoPlayerId) => {
      set((state) => {
        const newState = { ...state };
        const playerIdStr = playerId.toString();
        
        if (!newState.gameState.player_hands[playerIdStr]) {
          newState.gameState.player_hands[playerIdStr] = {
            tiles: playerId === 0 ? [] : null,
            tile_count: 0,
            melds: []
          };
        }
        
        const playerHand = newState.gameState.player_hands[playerIdStr] as any;
        playerHand.is_winner = isWinner;
        
        if (isWinner) {
          playerHand.win_type = winType;
          if (winTile) {
            playerHand.win_tile = winTile;
          }
          if (dianpaoPlayerId !== undefined) {
            playerHand.dianpao_player_id = dianpaoPlayerId;
          }
        } else {
          delete playerHand.win_type;
          delete playerHand.win_tile;
          delete playerHand.dianpao_player_id;
        }
        
        return newState;
      });
    },
    
    checkForWinners: () => {
      const { gameState } = get();
      const winners: Winner[] = [];
      
      Object.entries(gameState.player_hands).forEach(([playerIdStr, hand]) => {
        const playerHand = hand as any;
        if (playerHand.is_winner) {
          winners.push({
            player_id: parseInt(playerIdStr),
            win_type: playerHand.win_type || 'unknown',
            win_tile: playerHand.win_tile,
            dianpao_player_id: playerHand.dianpao_player_id
          });
        }
      });
      
      return winners;
    },
    
    // 🔧 智能分析自动触发
    triggerAutoAnalysis: async () => {
      const { gameState, isAnalyzing, setIsAnalyzing, setAnalysisResult } = get();
      
      // 避免重复分析
      if (isAnalyzing) {
        console.log('⚠️ 分析正在进行中，跳过自动分析');
        return;
      }
      
      const myHand = gameState.player_hands['0'];
      if (!myHand || !myHand.tiles || myHand.tiles.length === 0) {
        console.log('⚠️ 玩家0手牌为空，跳过自动分析');
        return;
      }
      
      // 🎯 游戏结束时不分析
      if (gameState.game_ended) {
        console.log('🏁 游戏已结束，跳过自动分析');
        return;
      }
      
      setIsAnalyzing(true);
      
      try {
        // 准备分析请求数据
        const handTiles = myHand.tiles.map(tile => `${tile.value}${tile.type === 'wan' ? '万' : tile.type === 'tiao' ? '条' : '筒'}`);
        
        // 收集可见牌（弃牌等）
        const visibleTiles: string[] = [];
        if (gameState.discarded_tiles) {
          gameState.discarded_tiles.forEach(tile => {
            visibleTiles.push(`${tile.value}${tile.type === 'wan' ? '万' : tile.type === 'tiao' ? '条' : '筒'}`);
          });
        }
        
        // 获取定缺信息
        const missingSuit = myHand.missing_suit || gameState.player_hands['0']?.missing_suit || 'tong';
        const missingSuitChinese = missingSuit === 'wan' ? '万' : missingSuit === 'tiao' ? '条' : '筒';
        
        // 调用血战到底分析API
        const response = await MahjongAPI.analyzeUltimate({
          hand_tiles: handTiles,
          visible_tiles: visibleTiles,
          missing_suit: missingSuitChinese
        });
        
        if (response.success && response.results) {
          // 构建弃牌分数对象
          const discardScores: { [key: string]: number } = {};
          response.results.forEach(result => {
            discardScores[result.discard_tile] = result.expected_value;
          });

          // 转换推荐弃牌为Tile类型
          const recommendedDiscard = response.results[0] ? {
            type: response.results[0].discard_tile.includes('万') ? TileType.WAN : 
                  response.results[0].discard_tile.includes('条') ? TileType.TIAO : TileType.TONG,
            value: parseInt(response.results[0].discard_tile[0])
          } : undefined;

          // 转换为原有格式以保持兼容性
          const compatibleAnalysis: AnalysisResult = {
            win_probability: response.results[0]?.can_win ? 0.8 : 0.2,
            recommended_discard: recommendedDiscard,
            listen_tiles: [],
            suggestions: [
              `推荐打出：${response.results[0]?.discard_tile}（收益：${response.results[0]?.expected_value}）`,
              `进张：${response.results[0]?.jinzhang_types}种-${response.results[0]?.jinzhang_count}张`,
              response.results[0]?.jinzhang_detail || ''
            ],
            discard_scores: discardScores,
            remaining_tiles_count: {},
            ultimate_results: response.results
          };
          
          setAnalysisResult(compatibleAnalysis);
          console.log('✅ 自动分析完成:', compatibleAnalysis.suggestions[0]);
        } else {
          console.warn('⚠️ 自动分析失败:', response.message || '未知错误');
        }
      } catch (error: any) {
        console.error('❌ 自动分析异常:', error.message);
      } finally {
        setIsAnalyzing(false);
      }
    }
  }))
);

export default useWebSocketGameStore;