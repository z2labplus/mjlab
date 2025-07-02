import axios from 'axios';
import { Tile, GameState } from '../types/mahjong';
import { useGameStore } from '../stores/gameStore';

// 错误处理工具函数
const getErrorMessage = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === 'string') {
    return error;
  }
  return '未知错误';
};

const getErrorCode = (error: unknown): string | null => {
  if (error && typeof error === 'object' && 'code' in error) {
    return (error as any).code;
  }
  return null;
};

const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/mahjong'
});

class MahjongApiClient {
  static async getGameState() {
    try {
      const response = await apiClient.get('/game-state');
      console.log('🔍 原始后端响应:', response.data);
      
      // 后端返回的是 GameOperationResponse 格式：{ success, message, game_state }
      if (response.data && response.data.success && response.data.game_state) {
        return response.data; // 返回完整的响应，让gameStore处理
      }
      
      // 如果后端返回失败或无数据，返回默认响应格式
      return {
        success: false,
        message: '获取游戏状态失败',
        game_state: {
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
          game_started: false
        }
      };
    } catch (error) {
      console.error('获取游戏状态失败:', error);
      // 返回错误响应格式
      return {
        success: false,
        message: `网络错误: ${getErrorMessage(error)}`,
        game_state: {
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
          game_started: false
        }
      };
    }
  }

  static async addTileToHand(playerId: number, tile: Tile) {
    try {
      const params = new URLSearchParams({
        player_id: playerId.toString(),
        tile_type: tile.type,
        tile_value: tile.value.toString()
      });
      const response = await apiClient.post(`/add-tile?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('添加手牌失败:', getErrorMessage(error));
      throw error;
    }
  }

  static async discardTile(playerId: number, tileType: string, tileValue: number) {
    try {
      const params = new URLSearchParams({
        player_id: playerId.toString(),
        tile_type: tileType,
        tile_value: tileValue.toString()
      });
      const response = await apiClient.post(`/discard-tile?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('弃牌失败:', getErrorMessage(error));
      throw error;
    }
  }

  static async setGameState(gameState: GameState) {
    try {
      // 详细日志输出，帮助调试
      console.log('📤 准备发送到后端的游戏状态:', JSON.stringify(gameState, null, 2));
      
      const requestData = {
        game_state: gameState
      };
      
      console.log('📤 完整请求数据:', JSON.stringify(requestData, null, 2));
      
      const response = await apiClient.post('/set-game-state', requestData);
      
      console.log('✅ 后端响应成功:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('❌ 设置游戏状态失败:', error);
      
      // 详细错误信息
      if (error.response) {
        console.error('状态码:', error.response.status);
        console.error('响应数据:', error.response.data);
        console.error('响应头:', error.response.headers);
      } else if (error.request) {
        console.error('请求失败:', error.request);
      } else {
        console.error('错误信息:', error.message);
      }
      
      throw error;
    }
  }

  static async checkHealth() {
    try {
      const response = await apiClient.get('/health', { timeout: 3000 });
      console.log('🔍 健康检查响应:', response.status, response.data);
      return response.status === 200;
    } catch (error) {
      console.warn('⚠️ 健康检查失败:', getErrorMessage(error));
      
      // 如果是网络连接错误，直接返回false
      const errorCode = getErrorCode(error);
      if (errorCode === 'NETWORK_ERROR' || errorCode === 'ECONNREFUSED') {
        console.warn('📡 后端服务未启动或网络不可达');
      }
      return false;
    }
  }

  // ============ 定缺相关 API ============

  static async setMissingSuit(playerId: number, missingSuit: 'wan' | 'tiao' | 'tong') {
    try {
      const response = await apiClient.post('/set-missing-suit', null, {
        params: {
          player_id: playerId,
          missing_suit: missingSuit
        }
      });
      return response.data;
    } catch (error) {
      console.error('设置定缺失败:', getErrorMessage(error));
      throw error;
    }
  }

  static async getMissingSuits() {
    try {
      const response = await apiClient.get('/missing-suits');
      return response.data;
    } catch (error) {
      console.error('获取定缺信息失败:', error);
      throw error;
    }
  }

  static async resetMissingSuits() {
    try {
      const response = await apiClient.post('/reset-missing-suits');
      return response.data;
    } catch (error) {
      console.error('重置定缺失败:', error);
      throw error;
    }
  }

  // ============ 游戏流程控制 API ============

  static async setCurrentPlayer(playerId: number) {
    try {
      const response = await apiClient.post('/set-current-player', null, {
        params: { player_id: playerId }
      });
      return response.data;
    } catch (error) {
      console.error('设置当前玩家失败:', getErrorMessage(error));
      throw error;
    }
  }

  static async nextPlayer() {
    try {
      const response = await apiClient.post('/next-player');
      return response.data;
    } catch (error) {
      console.error('切换下一个玩家失败:', getErrorMessage(error));
      throw error;
    }
  }
}

export default MahjongApiClient; 