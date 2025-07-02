import { useState, useEffect, useRef, useCallback } from 'react';
import { WebSocketClient, ConnectionStatus, EventCallback } from '../services/WebSocketClient';
import { GameState, Tile } from '../types/mahjong';

export interface UseWebSocketOptions {
  url?: string;
  roomId?: string;
  clientId?: string;
  autoConnect?: boolean;
  onGameStateUpdate?: (gameState: GameState) => void;
  onPlayerAction?: (data: any) => void;
  onCurrentPlayerChange?: (data: any) => void;
  onMissingSuitSet?: (data: any) => void;
  onConnectionStatusChange?: (status: ConnectionStatus) => void;
}

export interface UseWebSocketReturn {
  // WebSocket客户端实例
  client: WebSocketClient | null;
  
  // 连接状态
  connectionStatus: ConnectionStatus;
  isConnected: boolean;
  reconnectAttempts: number;
  
  // 连接控制
  connect: () => Promise<void>;
  disconnect: () => void;
  
  // 游戏API方法
  getGameState: () => Promise<GameState>;
  setGameState: (gameState: GameState) => Promise<GameState>;
  playerAction: (operationType: string, playerId: number, tile: Tile, sourcePlayerId?: number) => Promise<GameState>;
  resetGame: () => Promise<GameState>;
  setCurrentPlayer: (playerId: number) => Promise<GameState>;
  nextPlayer: () => Promise<{ previous_player: number; current_player: number; game_state: GameState }>;
  
  // 定缺相关
  setMissingSuit: (playerId: number, missingSuit: string) => Promise<GameState>;
  getMissingSuits: () => Promise<Record<string, string | null>>;
  resetMissingSuits: () => Promise<GameState>;
  
  // 牌谱相关
  exportGameRecord: () => Promise<any>;
  importGameRecord: (gameRecord: any) => Promise<GameState>;
  
  // 事件监听
  addEventListener: (event: string, callback: EventCallback) => void;
  removeEventListener: (event: string, callback?: EventCallback) => void;
  
  // 错误信息
  lastError: string | null;
}

export const useWebSocket = (options: UseWebSocketOptions = {}): UseWebSocketReturn => {
  const {
    url = 'ws://localhost:8000/api/ws',
    roomId = 'default',
    clientId,
    autoConnect = false,
    onGameStateUpdate,
    onPlayerAction,
    onCurrentPlayerChange,
    onMissingSuitSet,
    onConnectionStatusChange
  } = options;
  
  const [client, setClient] = useState<WebSocketClient | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>(ConnectionStatus.DISCONNECTED);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [lastError, setLastError] = useState<string | null>(null);
  
  const clientRef = useRef<WebSocketClient | null>(null);
  
  // 初始化WebSocket客户端
  useEffect(() => {
    const wsClient = new WebSocketClient(url, roomId, clientId);
    clientRef.current = wsClient;
    setClient(wsClient);
    
    // 设置事件监听器
    wsClient.on('connectionStatusChange', (data) => {
      setConnectionStatus(data.status);
      setReconnectAttempts(data.reconnectAttempts);
      onConnectionStatusChange?.(data.status);
    });
    
    wsClient.on('game_state_updated', (data) => {
      onGameStateUpdate?.(data.game_state);
    });
    
    wsClient.on('player_action_performed', (data) => {
      onPlayerAction?.(data);
      onGameStateUpdate?.(data.game_state);
    });
    
    wsClient.on('current_player_changed', (data) => {
      onCurrentPlayerChange?.(data);
      onGameStateUpdate?.(data.game_state);
    });
    
    wsClient.on('missing_suit_set', (data) => {
      onMissingSuitSet?.(data);
      onGameStateUpdate?.(data.game_state);
    });
    
    wsClient.on('missing_suits_reset', (data) => {
      onGameStateUpdate?.(data.game_state);
    });
    
    wsClient.on('game_reset', (data) => {
      onGameStateUpdate?.(data.game_state);
    });
    
    wsClient.on('game_record_imported', (data) => {
      onGameStateUpdate?.(data.game_state);
    });
    
    wsClient.on('error', (error) => {
      setLastError(error.message || '未知错误');
      console.error('WebSocket错误:', error);
    });
    
    wsClient.on('system', (message) => {
      console.log('系统消息:', message);
    });
    
    // 自动连接
    if (autoConnect) {
      wsClient.connect().catch((error) => {
        setLastError(error.message);
        console.error('自动连接失败:', error);
      });
    }
    
    return () => {
      wsClient.disconnect();
    };
  }, [url, roomId, clientId, autoConnect]);
  
  // 连接方法
  const connect = useCallback(async () => {
    if (clientRef.current) {
      try {
        await clientRef.current.connect();
        setLastError(null);
      } catch (error: any) {
        setLastError(error.message);
        throw error;
      }
    }
  }, []);
  
  // 断开连接方法
  const disconnect = useCallback(() => {
    if (clientRef.current) {
      clientRef.current.disconnect();
    }
  }, []);
  
  // 游戏API方法
  const getGameState = useCallback(async () => {
    if (!clientRef.current) throw new Error('WebSocket客户端未初始化');
    try {
      const result = await clientRef.current.getGameState();
      setLastError(null);
      return result;
    } catch (error: any) {
      setLastError(error.message);
      throw error;
    }
  }, []);
  
  const setGameState = useCallback(async (gameState: GameState) => {
    if (!clientRef.current) throw new Error('WebSocket客户端未初始化');
    try {
      const result = await clientRef.current.setGameState(gameState);
      setLastError(null);
      return result;
    } catch (error: any) {
      setLastError(error.message);
      throw error;
    }
  }, []);
  
  const playerAction = useCallback(async (
    operationType: string,
    playerId: number,
    tile: Tile,
    sourcePlayerId?: number
  ) => {
    if (!clientRef.current) throw new Error('WebSocket客户端未初始化');
    try {
      const result = await clientRef.current.playerAction(operationType, playerId, tile, sourcePlayerId);
      setLastError(null);
      return result;
    } catch (error: any) {
      setLastError(error.message);
      throw error;
    }
  }, []);
  
  const resetGame = useCallback(async () => {
    if (!clientRef.current) throw new Error('WebSocket客户端未初始化');
    try {
      const result = await clientRef.current.resetGame();
      setLastError(null);
      return result;
    } catch (error: any) {
      setLastError(error.message);
      throw error;
    }
  }, []);
  
  const setCurrentPlayer = useCallback(async (playerId: number) => {
    if (!clientRef.current) throw new Error('WebSocket客户端未初始化');
    try {
      const result = await clientRef.current.setCurrentPlayer(playerId);
      setLastError(null);
      return result;
    } catch (error: any) {
      setLastError(error.message);
      throw error;
    }
  }, []);
  
  const nextPlayer = useCallback(async () => {
    if (!clientRef.current) throw new Error('WebSocket客户端未初始化');
    try {
      const result = await clientRef.current.nextPlayer();
      setLastError(null);
      return result;
    } catch (error: any) {
      setLastError(error.message);
      throw error;
    }
  }, []);
  
  const setMissingSuit = useCallback(async (playerId: number, missingSuit: string) => {
    if (!clientRef.current) throw new Error('WebSocket客户端未初始化');
    try {
      const result = await clientRef.current.setMissingSuit(playerId, missingSuit);
      setLastError(null);
      return result;
    } catch (error: any) {
      setLastError(error.message);
      throw error;
    }
  }, []);
  
  const getMissingSuits = useCallback(async () => {
    if (!clientRef.current) throw new Error('WebSocket客户端未初始化');
    try {
      const result = await clientRef.current.getMissingSuits();
      setLastError(null);
      return result;
    } catch (error: any) {
      setLastError(error.message);
      throw error;
    }
  }, []);
  
  const resetMissingSuits = useCallback(async () => {
    if (!clientRef.current) throw new Error('WebSocket客户端未初始化');
    try {
      const result = await clientRef.current.resetMissingSuits();
      setLastError(null);
      return result;
    } catch (error: any) {
      setLastError(error.message);
      throw error;
    }
  }, []);
  
  const exportGameRecord = useCallback(async () => {
    if (!clientRef.current) throw new Error('WebSocket客户端未初始化');
    try {
      const result = await clientRef.current.exportGameRecord();
      setLastError(null);
      return result;
    } catch (error: any) {
      setLastError(error.message);
      throw error;
    }
  }, []);
  
  const importGameRecord = useCallback(async (gameRecord: any) => {
    if (!clientRef.current) throw new Error('WebSocket客户端未初始化');
    try {
      const result = await clientRef.current.importGameRecord(gameRecord);
      setLastError(null);
      return result;
    } catch (error: any) {
      setLastError(error.message);
      throw error;
    }
  }, []);
  
  const addEventListener = useCallback((event: string, callback: EventCallback) => {
    if (clientRef.current) {
      clientRef.current.on(event, callback);
    }
  }, []);
  
  const removeEventListener = useCallback((event: string, callback?: EventCallback) => {
    if (clientRef.current) {
      clientRef.current.off(event, callback);
    }
  }, []);
  
  return {
    client,
    connectionStatus,
    isConnected: connectionStatus === ConnectionStatus.CONNECTED,
    reconnectAttempts,
    connect,
    disconnect,
    getGameState,
    setGameState,
    playerAction,
    resetGame,
    setCurrentPlayer,
    nextPlayer,
    setMissingSuit,
    getMissingSuits,
    resetMissingSuits,
    exportGameRecord,
    importGameRecord,
    addEventListener,
    removeEventListener,
    lastError
  };
};