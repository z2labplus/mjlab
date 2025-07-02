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
import MahjongApiClient from '../services/MahjongApiClient';

interface GameStore {
  // 游戏状态
  gameState: GameState;
  analysisResult: AnalysisResult | null;
  isAnalyzing: boolean;
  
  // 可用牌信息
  availableTiles: TileInfo[];
  
  // WebSocket连接状态
  isConnected: boolean;
  connectionId: string | null;
  
  // API连接状态
  isApiConnected: boolean;
  lastSyncTime: Date | null;
  
  // Actions
  setGameState: (gameState: GameState) => void;
  setAnalysisResult: (result: AnalysisResult) => void;
  setIsAnalyzing: (analyzing: boolean) => void;
  setAvailableTiles: (tiles: TileInfo[]) => void;
  setConnectionStatus: (connected: boolean, id?: string) => void;
  
  // 游戏操作
  addTileToHand: (playerId: number, tile: Tile) => void;
  removeTileFromHand: (playerId: number, tile: Tile) => void;
  reduceHandTilesCount: (playerId: number, count: number, preferredTile?: Tile) => void;
  addDiscardedTile: (tile: Tile, playerId: number) => void;
  addMeld: (playerId: number, meld: Meld) => void;
  reorderPlayerHand: (playerId: number, newTiles: Tile[]) => void;
  addAction: (action: PlayerAction) => void;
  
  // API同步功能
  syncFromBackend: () => Promise<void>;
  syncToBackend: () => Promise<void>;
  setApiConnectionStatus: (connected: boolean) => void;
  checkApiConnection: () => Promise<boolean>;
  
  // 胜利检测
  checkForWinners: () => Promise<Winner[]>;
  
  // 定缺相关功能
  setPlayerMissingSuit: (playerId: number, missingSuit: 'wan' | 'tiao' | 'tong' | null) => void;
  getMissingSuits: () => Promise<void>;

  // 当前玩家控制
  setCurrentPlayer: (playerId: number) => Promise<{ success: boolean; message: string }>;
  nextPlayer: () => Promise<{ success: boolean; message: string; previousPlayer?: number; currentPlayer?: number }>;
  
  // 重置功能
  resetGame: () => void;
  clearAnalysis: () => void;
}

// 初始游戏状态
const initialGameState: GameState = {
  game_id: 'default_game',
  player_hands: {
    '0': { tiles: [], tile_count: 0, melds: [] },      // 我的手牌：具体牌面
    '1': { tiles: null, tile_count: 0, melds: [] },    // 其他玩家：只有数量
    '2': { tiles: null, tile_count: 0, melds: [] },    // 其他玩家：只有数量
    '3': { tiles: null, tile_count: 0, melds: [] }     // 其他玩家：只有数量
  },
  current_player: 0,
  discarded_tiles: [],
  player_discarded_tiles: {
    '0': [],
    '1': [],
    '2': [],
    '3': []
  },
  actions_history: [],
  game_started: false
};

export const useGameStore = create<GameStore>()(
  subscribeWithSelector((set, get) => ({
    // 初始状态
    gameState: initialGameState,
    analysisResult: null,
    isAnalyzing: false,
    availableTiles: [],
    isConnected: false,
    connectionId: null,
    
    // API状态初始化
    isApiConnected: false,
    lastSyncTime: null,
    
    // Setters
    setGameState: (gameState) => set({ gameState }),
    
    setAnalysisResult: (result) => set({ analysisResult: result }),
    
    setIsAnalyzing: (analyzing) => set({ isAnalyzing: analyzing }),
    
    setAvailableTiles: (tiles) => set({ availableTiles: tiles }),
    
    setConnectionStatus: (connected, id) => 
      set({ isConnected: connected, connectionId: id || null }),
    
    // 游戏操作
    addTileToHand: (playerId, tile) => set((state) => {
      const newGameState = { ...state.gameState };
      const playerHand = { ...newGameState.player_hands[playerId] };
      
      if (playerId === 0) {
        // 玩家0：添加具体牌面
        if (!playerHand.tiles) {
          playerHand.tiles = [];
        }
        playerHand.tiles = [...playerHand.tiles, tile];
        playerHand.tile_count = playerHand.tiles.length;
      } else {
        // 其他玩家：只增加数量，tiles保持null
        playerHand.tile_count = (playerHand.tile_count || 0) + 1;
        playerHand.tiles = null;
      }
      
      newGameState.player_hands[playerId] = playerHand;
      
      return { gameState: newGameState };
    }),
    
    removeTileFromHand: (playerId, tileToRemove) => set((state) => {
      const newGameState = { ...state.gameState };
      const playerHand = { ...newGameState.player_hands[playerId] };
      
      // 安全处理tiles可能为null的情况
      if (!playerHand.tiles) {
        console.warn(`玩家${playerId}的手牌为null，无法移除牌`);
        return state;
      }
      
      // 找到第一个匹配的牌并移除
      const tileIndex = playerHand.tiles.findIndex(tile => 
        tile.type === tileToRemove.type && tile.value === tileToRemove.value
      );
      
      if (tileIndex !== -1) {
        playerHand.tiles = [
          ...playerHand.tiles.slice(0, tileIndex),
          ...playerHand.tiles.slice(tileIndex + 1)
        ];
        // 更新tile_count
        playerHand.tile_count = playerHand.tiles.length;
        newGameState.player_hands[playerId] = playerHand;
      }
      
      return { gameState: newGameState };
    }),

    reduceHandTilesCount: (playerId, count, preferredTile) => set((state) => {
      const newGameState = { ...state.gameState };
      const playerHand = { ...newGameState.player_hands[playerId] };
      
      if (!playerHand.tiles) {
        // 对于其他玩家，只减少tile_count
        const currentCount = playerHand.tile_count || 0;
        playerHand.tile_count = Math.max(0, currentCount - count);
        newGameState.player_hands[playerId] = playerHand;
        return { gameState: newGameState };
      }
      
      let tiles = [...playerHand.tiles];
      
      // 确保手牌足够
      while (tiles.length < count) {
        // 如果手牌不够，添加通用牌
        const genericTile = { type: 'wan' as TileType, value: 1 };
        tiles.push(genericTile);
      }
      
      // 减少指定数量的牌
      for (let i = 0; i < count && tiles.length > 0; i++) {
        if (preferredTile) {
          // 优先移除指定类型的牌
          const preferredIndex = tiles.findIndex(tile => 
            tile.type === preferredTile.type && tile.value === preferredTile.value
          );
          if (preferredIndex !== -1) {
            tiles.splice(preferredIndex, 1);
            continue;
          }
        }
        // 移除第一张牌
        tiles.shift();
      }
      
      playerHand.tiles = tiles;
      playerHand.tile_count = tiles.length;
      newGameState.player_hands[playerId] = playerHand;
      
      return { gameState: newGameState };
    }),
    
    addDiscardedTile: (tile, playerId = 0) => set((state) => {
      const newGameState = { ...state.gameState };
      
      // 添加到全局弃牌池（保持兼容性）
      newGameState.discarded_tiles = [...newGameState.discarded_tiles, tile];
      
      // 添加到指定玩家的弃牌池
      if (newGameState.player_discarded_tiles) {
        newGameState.player_discarded_tiles = {
          ...newGameState.player_discarded_tiles,
          [playerId]: [...(newGameState.player_discarded_tiles[playerId] || []), tile]
        };
      } else {
        newGameState.player_discarded_tiles = {
          0: playerId === 0 ? [tile] : [],
          1: playerId === 1 ? [tile] : [],
          2: playerId === 2 ? [tile] : [],
          3: playerId === 3 ? [tile] : []
        };
      }
      
      return { gameState: newGameState };
    }),
    
    addMeld: (playerId, meld) => set((state) => {
      const newGameState = { ...state.gameState };
      const playerIdStr = playerId.toString();
      const playerHand = { ...newGameState.player_hands[playerIdStr] } || { tiles: playerId === 0 ? [] : null, tile_count: 0, melds: [] };
      playerHand.melds = [...(playerHand.melds || []), meld];
      newGameState.player_hands[playerIdStr] = playerHand;
      
      return { gameState: newGameState };
    }),
    
    // 重新排序玩家手牌
    reorderPlayerHand: (playerId, newTiles) => set((state) => {
      const newGameState = { ...state.gameState };
      const playerIdStr = playerId.toString();
      newGameState.player_hands[playerIdStr] = {
        ...newGameState.player_hands[playerIdStr],
        tiles: newTiles
      };
      return { gameState: newGameState };
    }),
    
    addAction: (action) => set((state) => {
      const newGameState = { ...state.gameState };
      newGameState.actions_history = [...newGameState.actions_history, action];
      return { gameState: newGameState };
    }),
    
    // 重置功能
    resetGame: () => set({
      gameState: initialGameState,
      analysisResult: null,
      isAnalyzing: false
    }),
    
    clearAnalysis: () => set({ analysisResult: null }),
    
    // API同步功能实现
    syncFromBackend: async () => {
      try {
        // 先检查健康状态
        const isHealthy = await MahjongApiClient.checkHealth();
        if (!isHealthy) {
          console.warn('⚠️ 后端健康检查失败，使用默认状态');
          set({ isApiConnected: false });
          return; // 直接返回，不抛出错误
        }
        
        const response = await MahjongApiClient.getGameState();
        
        console.log('🔍 后端响应详情:', response);
        
        // 处理后端的响应格式 (GameOperationResponse)
        let backendGameState;
        let isSuccess = false;
        
        if (response && typeof response === 'object') {
          // 后端返回格式: { success, message, game_state }
          if (response.success === true && response.game_state) {
            backendGameState = response.game_state;
            isSuccess = true;
            console.log('✅ 后端返回成功:', response.message);
          }
          // 后端返回失败但有game_state
          else if (response.success === false && response.game_state) {
            backendGameState = response.game_state;
            isSuccess = true; // 虽然后端说失败，但有数据就算成功
            console.warn('⚠️ 后端返回失败，但使用返回的状态:', response.message);
          }
          // 检查是否有默认的game_state格式
          else if (response.game_state) {
            backendGameState = response.game_state;
            isSuccess = true;
            console.log('📋 使用后端返回的游戏状态');
          }
          // 没有有效数据，保持当前状态
          else {
            console.warn('⚠️ 后端返回无效数据，保持当前状态');
            backendGameState = get().gameState;
            isSuccess = false;
          }
        } else {
          console.error('❌ 后端返回数据格式无效');
          backendGameState = get().gameState;
          isSuccess = false;
        }
        
        // 确保关键字段存在，提供完整的默认值
        const defaultState = get().gameState || {
          game_id: 'default',
          player_hands: {
            '0': { tiles: [], tile_count: 0, melds: [], missing_suit: null },
            '1': { tiles: null, tile_count: 0, melds: [], missing_suit: null },
            '2': { tiles: null, tile_count: 0, melds: [], missing_suit: null },
            '3': { tiles: null, tile_count: 0, melds: [], missing_suit: null }
          },
          player_discarded_tiles: {
            '0': [], '1': [], '2': [], '3': []
          },
          discarded_tiles: [],
          actions_history: [],
          current_player: 0,
          game_started: false
        };
        
        const safeGameState = {
          ...defaultState, // 使用默认值作为基础
          ...backendGameState, // 覆盖后端数据
          // 确保player_hands格式正确
          player_hands: {
            '0': {
              ...defaultState.player_hands['0'],
              ...(backendGameState?.player_hands?.['0'] || {})
            },
            '1': {
              ...defaultState.player_hands['1'],
              ...(backendGameState?.player_hands?.['1'] || {})
            },
            '2': {
              ...defaultState.player_hands['2'],
              ...(backendGameState?.player_hands?.['2'] || {})
            },
            '3': {
              ...defaultState.player_hands['3'],
              ...(backendGameState?.player_hands?.['3'] || {})
            }
          }
        };
        
        set({
          gameState: safeGameState,
          isApiConnected: isSuccess,
          lastSyncTime: new Date()
        });
        
        if (isSuccess) {
          console.log('✅ 从后端同步状态成功', safeGameState);
        } else {
          console.log('⚠️ 从后端同步状态（使用缓存）', safeGameState);
        }
      } catch (error) {
        console.error('❌ 从后端同步状态失败:', error);
        
        // 确保有基本的游戏状态，即使出错也不崩溃
        const currentState = get().gameState;
        if (!currentState || !currentState.player_hands) {
          const fallbackState = {
            game_id: 'offline',
            player_hands: {
              '0': { tiles: [], tile_count: 0, melds: [], missing_suit: null },
              '1': { tiles: null, tile_count: 0, melds: [], missing_suit: null },
              '2': { tiles: null, tile_count: 0, melds: [], missing_suit: null },
              '3': { tiles: null, tile_count: 0, melds: [], missing_suit: null }
            },
            player_discarded_tiles: {
              '0': [], '1': [], '2': [], '3': []
            },
            discarded_tiles: [],
            actions_history: [],
            current_player: 0,
            game_started: false
          };
          set({ gameState: fallbackState });
        }
        
        set({ isApiConnected: false });
        // 不重新抛出错误，避免界面崩溃
      }
    },
    
    syncToBackend: async () => {
      try {
        // 先检查健康状态
        const isHealthy = await MahjongApiClient.checkHealth();
        if (!isHealthy) {
          throw new Error('后端服务不可用');
        }
        
        const currentState = get().gameState;
        await MahjongApiClient.setGameState(currentState);
        set({
          isApiConnected: true,
          lastSyncTime: new Date()
        });
        console.log('✅ 同步状态到后端成功');
      } catch (error) {
        console.error('❌ 同步状态到后端失败:', error);
        set({ isApiConnected: false });
        throw error; // 重新抛出错误以便UI处理
      }
    },
    
    setApiConnectionStatus: (connected: boolean) => {
      set({ isApiConnected: connected });
    },
    
    // 检查API连接状态
    checkApiConnection: async () => {
      try {
        const isHealthy = await MahjongApiClient.checkHealth();
        set({ isApiConnected: isHealthy });
        return isHealthy;
      } catch (error) {
        console.error('❌ API连接检查失败:', error);
        set({ isApiConnected: false });
        return false;
      }
    },

    // 检查胜利者
    checkForWinners: async (): Promise<Winner[]> => {
      try {
        const gameState = get().gameState;
        const winners: Winner[] = [];
        
        Object.entries(gameState.player_hands).forEach(([playerId, hand]) => {
          if (hand.is_winner && hand.win_type) {
            winners.push({
              player_id: parseInt(playerId),
              win_type: hand.win_type,
              win_tile: hand.win_tile,
              dianpao_player_id: hand.dianpao_player_id
            });
          }
        });
        
        return winners;
      } catch (error) {
        console.error('❌ 检查胜利者失败:', error);
        return [];
      }
    },

    // 定缺相关功能实现
    setPlayerMissingSuit: (playerId: number, missingSuit: 'wan' | 'tiao' | 'tong' | null) => 
      set((state) => {
        const newGameState = { ...state.gameState };
        const playerIdStr = playerId.toString();
        
        // 确保玩家存在
        if (!newGameState.player_hands[playerIdStr]) {
          newGameState.player_hands[playerIdStr] = {
            tiles: playerId === 0 ? [] : null,
            tile_count: 0,
            melds: []
          };
        }
        
        // 设置定缺
        newGameState.player_hands[playerIdStr] = {
          ...newGameState.player_hands[playerIdStr],
          missing_suit: missingSuit
        };
        
        return { gameState: newGameState };
      }),

    getMissingSuits: async () => {
      try {
        const response = await MahjongApiClient.getMissingSuits();
        if (response.success && response.data) {
          // 更新本地状态
          set((state) => {
            const newGameState = { ...state.gameState };
            
            Object.entries(response.data.missing_suits || {}).forEach(([playerId, missingSuit]) => {
              if (newGameState.player_hands[playerId]) {
                newGameState.player_hands[playerId] = {
                  ...newGameState.player_hands[playerId],
                  missing_suit: missingSuit as string | null
                };
              }
            });
            
            return { gameState: newGameState };
          });
        }
      } catch (error) {
        console.error('❌ 获取定缺信息失败:', error);
        throw error;
      }
    },

    // 当前玩家控制功能实现
    setCurrentPlayer: async (playerId: number) => {
      try {
        const response = await MahjongApiClient.setCurrentPlayer(playerId);
        if (response.success) {
          // 更新本地状态
          set((state) => ({
            gameState: {
              ...state.gameState,
              current_player: playerId
            }
          }));
          return { success: true, message: response.message };
        } else {
          return { success: false, message: response.message };
        }
      } catch (error) {
        console.error('❌ 设置当前玩家失败:', error);
        return { 
          success: false, 
          message: error instanceof Error ? error.message : '设置当前玩家失败' 
        };
      }
    },

    nextPlayer: async () => {
      try {
        const response = await MahjongApiClient.nextPlayer();
        if (response.success) {
          // 更新本地状态
          set((state) => ({
            gameState: {
              ...state.gameState,
              current_player: response.current_player
            }
          }));
          return { 
            success: true, 
            message: response.message,
            previousPlayer: response.previous_player,
            currentPlayer: response.current_player 
          };
        } else {
          return { success: false, message: response.message };
        }
      } catch (error) {
        console.error('❌ 切换玩家失败:', error);
        return { 
          success: false, 
          message: error instanceof Error ? error.message : '切换玩家失败' 
        };
      }
    }
  }))
);

// 选择器函数，用于获取特定数据
export const selectPlayerHand = (playerId: number) => (state: GameStore) => 
  state.gameState.player_hands?.[playerId] || { tiles: playerId === 0 ? [] : null, tile_count: 0, melds: [] };

export const selectMyHand = () => (state: GameStore) => 
  state.gameState.player_hands?.[0] || { tiles: [], tile_count: 0, melds: [] }; // 假设玩家ID为0

export const selectDiscardedTiles = () => (state: GameStore) => 
  state.gameState.discarded_tiles || [];

export const selectPlayerDiscardedTiles = (playerId: number) => (state: GameStore) => 
  state.gameState.player_discarded_tiles?.[playerId] || [];

export const selectAnalysis = () => (state: GameStore) => 
  state.analysisResult;

export const selectIsAnalyzing = () => (state: GameStore) => 
  state.isAnalyzing; 