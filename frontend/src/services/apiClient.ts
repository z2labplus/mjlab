import axios from 'axios';
import { GameState } from '../types/mahjong';

// 从环境变量获取API地址，默认使用本地开发地址
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/mahjong';

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API响应类型
interface ApiResponse<T> {
  success: boolean;
  message: string;
  data?: T;
}

interface GameStateResponse extends ApiResponse<GameState> {
  game_state: GameState;
}

interface OperationRequest {
  player_id: number;
  operation_type: 'hand' | 'discard' | 'peng' | 'angang' | 'zhigang' | 'jiagang';
  tile: {
    type: 'wan' | 'tiao' | 'tong';
    value: number;
  };
  source_player_id?: number;
}

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    console.log('API请求:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('API请求错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 404) {
      console.error('API路由不存在:', error.config.url);
    } else {
      console.error('API响应错误:', error);
    }
    return Promise.reject(error);
  }
);

export class MahjongApiClient {
  
  // 获取游戏状态
  static async getGameState(): Promise<GameState> {
    try {
      const response = await apiClient.get<GameStateResponse>('/game-state');
      console.log('从后端获取的游戏状态:', response.data);
      
      if (response.data.success) {
        // 确保返回的状态包含 game_id
        const gameState = response.data.data || response.data.game_state;
        if (!gameState.game_id) {
          console.warn('后端返回的游戏状态中没有 game_id');
        }
        return gameState;
      } else {
        throw new Error(response.data.message || '获取游戏状态失败');
      }
    } catch (error) {
      console.error('获取游戏状态失败:', error);
      throw error;
    }
  }

  // 设置游戏状态
  static async setGameState(gameState: GameState): Promise<GameState> {
    try {
      const response = await apiClient.post<GameStateResponse>('/set-game-state', {
        game_state: gameState
      });
      if (response.data.success) {
        return response.data.game_state;
      } else {
        throw new Error(response.data.message);
      }
    } catch (error) {
      console.error('设置游戏状态失败:', error);
      throw error;
    }
  }

  // 重置游戏
  static async resetGame(): Promise<GameState> {
    try {
      const response = await apiClient.post<GameStateResponse>('/reset');
      if (response.data.success) {
        return response.data.game_state;
      } else {
        throw new Error(response.data.message);
      }
    } catch (error) {
      console.error('重置游戏失败:', error);
      throw error;
    }
  }

  // 执行操作
  static async performOperation(request: OperationRequest): Promise<GameState> {
    try {
      const response = await apiClient.post<GameStateResponse>('/operation', request);
      if (response.data.success) {
        return response.data.game_state;
      } else {
        throw new Error(response.data.message);
      }
    } catch (error) {
      console.error('执行操作失败:', error);
      throw error;
    }
  }

  // 便捷方法：碰牌
  static async pengTile(
    playerId: number, 
    tileType: 'wan' | 'tiao' | 'tong', 
    tileValue: number, 
    sourcePlayerId?: number
  ): Promise<any> {
    try {
      const params = new URLSearchParams({
        player_id: playerId.toString(),
        tile_type: tileType,
        tile_value: tileValue.toString(),
      });
      
      if (sourcePlayerId !== undefined) {
        params.append('source_player_id', sourcePlayerId.toString());
      }
      
      const response = await apiClient.post(`/peng?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('碰牌失败:', error);
      throw error;
    }
  }

  // 便捷方法：杠牌
  static async gangTile(
    playerId: number,
    tileType: 'wan' | 'tiao' | 'tong',
    tileValue: number,
    gangType: 'angang' | 'zhigang' | 'jiagang',
    sourcePlayerId?: number
  ): Promise<any> {
    try {
      const params = new URLSearchParams({
        player_id: playerId.toString(),
        tile_type: tileType,
        tile_value: tileValue.toString(),
        gang_type: gangType,
      });
      
      if (sourcePlayerId !== undefined) {
        params.append('source_player_id', sourcePlayerId.toString());
      }
      
      const response = await apiClient.post(`/gang?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('杠牌失败:', error);
      throw error;
    }
  }

  // 便捷方法：添加手牌
  static async addHandTile(
    playerId: number,
    tileType: 'wan' | 'tiao' | 'tong',
    tileValue: number
  ): Promise<any> {
    try {
      const params = new URLSearchParams({
        player_id: playerId.toString(),
        tile_type: tileType,
        tile_value: tileValue.toString(),
      });
      
      const response = await apiClient.post(`/add-hand-tile?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('添加手牌失败:', error);
      throw error;
    }
  }

  // 便捷方法：弃牌
  static async discardTile(
    playerId: number,
    tileType: 'wan' | 'tiao' | 'tong',
    tileValue: number
  ): Promise<any> {
    try {
      const params = new URLSearchParams({
        player_id: playerId.toString(),
        tile_type: tileType,
        tile_value: tileValue.toString(),
      });
      
      const response = await apiClient.post(`/discard-tile?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('弃牌失败:', error);
      throw error;
    }
  }

  // 检查服务器连接
  static async checkHealth(): Promise<boolean> {
    try {
      const response = await apiClient.get('/health');
      return response.status === 200;
    } catch (error) {
      return false;
    }
  }
}

export default MahjongApiClient; 