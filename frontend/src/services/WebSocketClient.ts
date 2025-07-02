import { GameState, Tile } from '../types/mahjong';

// WebSocket消息接口定义
export interface WSMessage {
  type: 'request' | 'response' | 'broadcast' | 'system' | 'error';
  action?: string;
  event?: string;
  data?: any;
  success?: boolean;
  message?: string;
  request_id?: string;
  timestamp?: string;
}

// 请求配置接口
export interface RequestOptions {
  timeout?: number;
  retries?: number;
}

// 事件回调函数类型
export type EventCallback = (data: any) => void;

// WebSocket连接状态
export enum ConnectionStatus {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting', 
  CONNECTED = 'connected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error'
}

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private roomId: string;
  private clientId: string;
  private connectionStatus: ConnectionStatus = ConnectionStatus.DISCONNECTED;
  
  // 事件监听器
  private eventListeners: Map<string, EventCallback[]> = new Map();
  
  // 请求响应管理
  private pendingRequests: Map<string, {
    resolve: (data: any) => void;
    reject: (error: any) => void;
    timeout: NodeJS.Timeout;
  }> = new Map();
  
  // 重连配置
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // 1秒
  private heartbeatInterval: NodeJS.Timeout | null = null;
  
  constructor(url: string = 'ws://localhost:8000/api/ws', roomId: string = 'default', clientId?: string) {
    this.url = url;
    this.roomId = roomId;
    this.clientId = clientId || `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  
  // ============ 连接管理 ============
  
  public async connect(): Promise<void> {
    if (this.connectionStatus === ConnectionStatus.CONNECTED) {
      console.log('WebSocket已连接');
      return;
    }
    
    this.connectionStatus = ConnectionStatus.CONNECTING;
    this.notifyStatusChange();
    
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = `${this.url}?room_id=${this.roomId}&client_id=${this.clientId}`;
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
          console.log('✅ WebSocket连接成功');
          this.connectionStatus = ConnectionStatus.CONNECTED;
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          this.notifyStatusChange();
          resolve();
        };
        
        this.ws.onmessage = (event) => {
          this.handleMessage(event.data);
        };
        
        this.ws.onclose = (event) => {
          console.log('❌ WebSocket连接关闭:', event.code, event.reason);
          this.connectionStatus = ConnectionStatus.DISCONNECTED;
          this.stopHeartbeat();
          this.notifyStatusChange();
          
          // 自动重连
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnect();
          }
        };
        
        this.ws.onerror = (error) => {
          console.error('❌ WebSocket连接错误:', error);
          this.connectionStatus = ConnectionStatus.ERROR;
          this.notifyStatusChange();
          reject(error);
        };
        
        // 连接超时
        setTimeout(() => {
          if (this.connectionStatus === ConnectionStatus.CONNECTING) {
            this.ws?.close();
            reject(new Error('WebSocket连接超时'));
          }
        }, 10000);
        
      } catch (error) {
        this.connectionStatus = ConnectionStatus.ERROR;
        this.notifyStatusChange();
        reject(error);
      }
    });
  }
  
  public disconnect(): void {
    if (this.ws) {
      this.connectionStatus = ConnectionStatus.DISCONNECTED;
      this.stopHeartbeat();
      this.ws.close();
      this.ws = null;
      
      // 清理待处理的请求
      this.pendingRequests.forEach(({ reject, timeout }) => {
        clearTimeout(timeout);
        reject(new Error('WebSocket连接已断开'));
      });
      this.pendingRequests.clear();
      
      this.notifyStatusChange();
      console.log('🔌 WebSocket连接已断开');
    }
  }
  
  private async reconnect(): Promise<void> {
    if (this.connectionStatus === ConnectionStatus.RECONNECTING) {
      return;
    }
    
    this.reconnectAttempts++;
    this.connectionStatus = ConnectionStatus.RECONNECTING;
    this.notifyStatusChange();
    
    console.log(`🔄 尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
    
    setTimeout(async () => {
      try {
        await this.connect();
      } catch (error) {
        console.error('重连失败:', error);
        
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
          console.error('❌ 重连次数已达上限，停止重连');
          this.connectionStatus = ConnectionStatus.ERROR;
          this.notifyStatusChange();
        }
      }
    }, this.reconnectDelay * this.reconnectAttempts);
  }
  
  // ============ 心跳检测 ============
  
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.connectionStatus === ConnectionStatus.CONNECTED) {
        this.sendRequest('health_check', {}).catch(() => {
          console.warn('⚠️ 心跳检测失败');
        });
      }
    }, 30000); // 30秒心跳
  }
  
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }
  
  // ============ 消息处理 ============
  
  private handleMessage(data: string): void {
    try {
      const message: WSMessage = JSON.parse(data);
      
      // 处理响应消息
      if (message.type === 'response' && message.request_id) {
        this.handleResponse(message);
        return;
      }
      
      // 处理广播消息
      if (message.type === 'broadcast' && message.event) {
        this.emit(message.event, message.data);
        return;
      }
      
      // 处理系统消息
      if (message.type === 'system') {
        this.emit('system', message);
        return;
      }
      
      // 处理错误消息
      if (message.type === 'error') {
        this.emit('error', message);
        return;
      }
      
    } catch (error) {
      console.error('解析WebSocket消息失败:', error, data);
    }
  }
  
  private handleResponse(message: WSMessage): void {
    const requestId = message.request_id!;
    const pendingRequest = this.pendingRequests.get(requestId);
    
    if (pendingRequest) {
      clearTimeout(pendingRequest.timeout);
      this.pendingRequests.delete(requestId);
      
      if (message.success) {
        pendingRequest.resolve(message.data);
      } else {
        pendingRequest.reject(new Error(message.message || '请求失败'));
      }
    }
  }
  
  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  
  // ============ 请求发送 ============
  
  public async sendRequest(action: string, data: any, options: RequestOptions = {}): Promise<any> {
    if (this.connectionStatus !== ConnectionStatus.CONNECTED || !this.ws) {
      throw new Error('WebSocket未连接');
    }
    
    const requestId = this.generateRequestId();
    const timeout = options.timeout || 10000; // 10秒超时
    
    const message: WSMessage = {
      type: 'request',
      action,
      data,
      request_id: requestId
    };
    
    return new Promise((resolve, reject) => {
      // 设置超时
      const timeoutHandle = setTimeout(() => {
        this.pendingRequests.delete(requestId);
        reject(new Error(`请求超时: ${action}`));
      }, timeout);
      
      // 存储请求
      this.pendingRequests.set(requestId, {
        resolve,
        reject,
        timeout: timeoutHandle
      });
      
      // 发送消息
      try {
        this.ws!.send(JSON.stringify(message));
      } catch (error) {
        clearTimeout(timeoutHandle);
        this.pendingRequests.delete(requestId);
        reject(error);
      }
    });
  }
  
  // ============ 事件系统 ============
  
  public on(event: string, callback: EventCallback): void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event)!.push(callback);
  }
  
  public off(event: string, callback?: EventCallback): void {
    if (!this.eventListeners.has(event)) return;
    
    if (callback) {
      const callbacks = this.eventListeners.get(event)!;
      const index = callbacks.indexOf(callback);
      if (index !== -1) {
        callbacks.splice(index, 1);
      }
    } else {
      this.eventListeners.delete(event);
    }
  }
  
  private emit(event: string, data: any): void {
    const callbacks = this.eventListeners.get(event);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`事件回调执行失败 ${event}:`, error);
        }
      });
    }
    
    // 同时触发通用的 message 事件
    const messageCallbacks = this.eventListeners.get('message');
    if (messageCallbacks) {
      messageCallbacks.forEach(callback => {
        try {
          callback({ event, data });
        } catch (error) {
          console.error('通用消息回调执行失败:', error);
        }
      });
    }
  }
  
  private notifyStatusChange(): void {
    this.emit('connectionStatusChange', {
      status: this.connectionStatus,
      reconnectAttempts: this.reconnectAttempts
    });
  }
  
  // ============ 游戏相关API ============
  
  public async getGameState(): Promise<GameState> {
    const response = await this.sendRequest('get_game_state', {});
    return response.game_state;
  }
  
  public async setGameState(gameState: GameState): Promise<GameState> {
    const response = await this.sendRequest('set_game_state', { game_state: gameState });
    return response.game_state;
  }
  
  public async playerAction(
    operationType: string,
    playerId: number,
    tile: Tile,
    sourcePlayerId?: number
  ): Promise<GameState> {
    const response = await this.sendRequest('player_action', {
      operation_type: operationType,
      player_id: playerId,
      tile: {
        type: tile.type,
        value: tile.value
      },
      source_player_id: sourcePlayerId
    });
    return response.game_state;
  }
  
  public async gameControl(controlType: string, data: any = {}): Promise<any> {
    return await this.sendRequest('game_control', {
      control_type: controlType,
      ...data
    });
  }
  
  public async setMissingSuit(playerId: number, missingSuit: string): Promise<GameState> {
    const response = await this.sendRequest('missing_suit', {
      action_type: 'set',
      player_id: playerId,
      missing_suit: missingSuit
    });
    return response.game_state;
  }
  
  public async getMissingSuits(): Promise<Record<string, string | null>> {
    const response = await this.sendRequest('missing_suit', {
      action_type: 'get'
    });
    return response.missing_suits;
  }
  
  public async resetMissingSuits(): Promise<GameState> {
    const response = await this.sendRequest('missing_suit', {
      action_type: 'reset'
    });
    return response.game_state;
  }
  
  public async exportGameRecord(): Promise<any> {
    const response = await this.sendRequest('export_record', {});
    return response.game_record;
  }
  
  public async importGameRecord(gameRecord: any): Promise<GameState> {
    const response = await this.sendRequest('import_record', { game_record: gameRecord });
    return response.game_state;
  }
  
  public async resetGame(): Promise<GameState> {
    const response = await this.gameControl('reset');
    return response.game_state;
  }
  
  public async setCurrentPlayer(playerId: number): Promise<GameState> {
    const response = await this.gameControl('set_current_player', { player_id: playerId });
    return response.game_state;
  }
  
  public async nextPlayer(): Promise<{ previous_player: number; current_player: number; game_state: GameState }> {
    return await this.gameControl('next_player');
  }
  
  public async getConnections(): Promise<any> {
    return await this.sendRequest('get_connections', {});
  }
  
  // ============ 状态获取 ============
  
  public getConnectionStatus(): ConnectionStatus {
    return this.connectionStatus;
  }
  
  public isConnected(): boolean {
    return this.connectionStatus === ConnectionStatus.CONNECTED;
  }
  
  public getClientId(): string {
    return this.clientId;
  }
  
  public getRoomId(): string {
    return this.roomId;
  }
}