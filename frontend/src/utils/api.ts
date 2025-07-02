import axios from 'axios';
import { GameRequest, GameResponse, TileInfo } from '../types/mahjong';

// 从环境变量获取API地址，默认使用本地开发地址
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/mahjong';

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
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
api.interceptors.response.use(
  (response) => {
    console.log('API响应:', response.status, response.config.url);
    return response;
  },
  (error) => {
    if (error.response?.status === 404) {
      console.error('API路由不存在:', error.config.url);
    } else {
    console.error('API响应错误:', error.response?.status, error.response?.data);
    }
    return Promise.reject(error);
  }
);

// API服务类
export class MahjongAPI {
  /**
   * 分析游戏状态
   */
  static async analyzeGame(request: GameRequest): Promise<GameResponse> {
    try {
      const response = await api.post<GameResponse>('/analyze', request);
      return response.data;
    } catch (error) {
      console.error('分析游戏失败:', error);
      throw new Error('分析游戏失败，请稍后重试');
    }
  }

  /**
   * 使用血战到底分析器分析最优出牌
   */
  static async analyzeUltimate(request: {
    hand_tiles: string[];
    visible_tiles: string[];
    missing_suit: string;
  }): Promise<{
    success: boolean;
    message: string;
    results: Array<{
      discard_tile: string;
      expected_value: number;
      jinzhang_types: number;
      jinzhang_count: number;
      jinzhang_detail: string;
      shanten: number;
      can_win: boolean;
      is_forced: boolean;
      patterns: string[];
    }>;
  }> {
    try {
      const response = await api.post('/analyze-ultimate', request);
      return response.data;
    } catch (error) {
      console.error('血战到底分析失败:', error);
      throw new Error('血战到底分析失败，请稍后重试');
    }
  }

  /**
   * 获取所有麻将牌信息
   */
  static async getTileCodes(): Promise<TileInfo[]> {
    try {
      const response = await api.get<{ tiles: TileInfo[] }>('/tile-codes');
      return response.data.tiles;
    } catch (error) {
      console.error('获取麻将牌信息失败:', error);
      throw new Error('获取麻将牌信息失败');
    }
  }

  /**
   * 健康检查
   */
  static async healthCheck(): Promise<boolean> {
    try {
      const response = await api.get('/health');
      return response.data.success === true;
    } catch (error) {
      console.error('健康检查失败:', error);
      return false;
    }
  }

  /**
   * 获取API信息
   */
  static async getApiInfo(): Promise<any> {
    try {
      const response = await api.get('/');
      return response.data;
    } catch (error) {
      console.error('获取API信息失败:', error);
      throw new Error('获取API信息失败');
    }
  }
}

export default api; 