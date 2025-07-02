import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import classNames from 'classnames';

interface MahjongCard {
  id: number;
  suit: string;
  value: number;
}

interface GameAction {
  sequence: number;
  timestamp: string;
  player_id: number;
  action_type: string;
  card?: string;
  target_player?: number;
  gang_type?: string;
  missing_suit?: string;
  score_change: number;
}

interface PlayerRecord {
  player_id: number;
  player_name: string;
  position: number;
  initial_hand: string[];
  missing_suit?: string;
  final_score: number;
  is_winner: boolean;
  draw_count: number;
  discard_count: number;
  peng_count: number;
  gang_count: number;
}

interface GameReplay {
  game_info: {
    game_id: string;
    start_time: string;
    end_time?: string;
    duration?: number;
    player_count: number;
    game_mode: string;
  };
  players: PlayerRecord[];
  actions: GameAction[];
  metadata: any;
}

interface ReplayViewerProps {
  gameId: string;
  onClose?: () => void;
}

const ReplayViewer: React.FC<ReplayViewerProps> = ({ gameId, onClose }) => {
  const [replayData, setReplayData] = useState<GameReplay | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playSpeed, setPlaySpeed] = useState(1000); // 毫秒
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 加载牌谱数据
  useEffect(() => {
    const loadReplay = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/v1/replay/${gameId}`);
        const result = await response.json();
        
        if (result.success) {
          setReplayData(result.data.game_record);
        } else {
          setError('加载牌谱失败');
        }
      } catch (err) {
        setError('网络错误');
      } finally {
        setLoading(false);
      }
    };

    loadReplay();
  }, [gameId]);

  // 自动播放控制
  useEffect(() => {
    if (!isPlaying || !replayData) return;

    const timer = setInterval(() => {
      setCurrentStep(prev => {
        if (prev >= replayData.actions.length - 1) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, playSpeed);

    return () => clearInterval(timer);
  }, [isPlaying, playSpeed, replayData]);

  const handlePlayPause = useCallback(() => {
    setIsPlaying(prev => !prev);
  }, []);

  const handleStepForward = useCallback(() => {
    if (!replayData) return;
    setCurrentStep(prev => Math.min(prev + 1, replayData.actions.length - 1));
  }, [replayData]);

  const handleStepBackward = useCallback(() => {
    setCurrentStep(prev => Math.max(prev - 1, 0));
  }, []);

  const handleReset = useCallback(() => {
    setCurrentStep(0);
    setIsPlaying(false);
  }, []);

  const handleExport = useCallback(async (format: 'json' | 'zip') => {
    try {
      const response = await fetch(`/api/v1/replay/${gameId}/export/${format}`);
      const blob = await response.blob();
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `replay_${gameId}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('导出失败:', err);
    }
  }, [gameId]);

  const getCurrentAction = () => {
    if (!replayData || currentStep < 0) return null;
    return replayData.actions[currentStep];
  };

  const getActionDescription = (action: GameAction) => {
    const playerName = replayData?.players[action.player_id]?.player_name || `玩家${action.player_id}`;
    
    switch (action.action_type) {
      case 'draw':
        return `${playerName} 摸牌`;
      case 'discard':
        return `${playerName} 弃牌 ${action.card}`;
      case 'peng':
        return `${playerName} 碰牌 ${action.card}`;
      case 'gang':
        return `${playerName} ${action.gang_type === 'an_gang' ? '暗杠' : '明杠'} ${action.card}`;
      case 'hu':
        return `${playerName} 胡牌！`;
      case 'missing_suit':
        return `${playerName} 定缺 ${action.missing_suit}`;
      default:
        return `${playerName} ${action.action_type}`;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-gray-600">加载牌谱中...</span>
      </div>
    );
  }

  if (error || !replayData) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="text-red-500 text-lg mb-2">😕</div>
          <div className="text-gray-600">{error || '牌谱不存在'}</div>
          {onClose && (
            <button 
              onClick={onClose}
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              返回
            </button>
          )}
        </div>
      </div>
    );
  }

  const currentAction = getCurrentAction();

  return (
    <div className="replay-viewer bg-white rounded-lg shadow-lg p-6">
      {/* 头部信息 */}
      <div className="header mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold text-gray-800">
            牌谱回放 - {replayData.game_info.game_id}
          </h2>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          )}
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-500">开始时间:</span>
            <div>{new Date(replayData.game_info.start_time).toLocaleString()}</div>
          </div>
          <div>
            <span className="text-gray-500">游戏时长:</span>
            <div>{Math.floor((replayData.game_info.duration || 0) / 60)}分钟</div>
          </div>
          <div>
            <span className="text-gray-500">总操作数:</span>
            <div>{replayData.actions.length}</div>
          </div>
          <div>
            <span className="text-gray-500">胜利者:</span>
            <div>
              {replayData.players
                .filter(p => p.is_winner)
                .map(p => p.player_name)
                .join(', ') || '无'}
            </div>
          </div>
        </div>
      </div>

      {/* 玩家信息 */}
      <div className="players-info mb-6">
        <h3 className="text-lg font-semibold mb-3">玩家信息</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {replayData.players.map((player) => (
            <motion.div
              key={player.player_id}
              className={classNames(
                'player-card p-4 rounded-lg border-2 transition-all',
                {
                  'border-green-500 bg-green-50': player.is_winner,
                  'border-gray-300 bg-gray-50': !player.is_winner,
                  'ring-2 ring-blue-500': currentAction?.player_id === player.player_id
                }
              )}
              animate={{
                scale: currentAction?.player_id === player.player_id ? 1.05 : 1
              }}
            >
              <div className="font-medium text-gray-800">{player.player_name}</div>
              <div className="text-sm text-gray-600">座位 {player.position}</div>
              <div className="text-sm text-gray-600">
                定缺: {player.missing_suit || '未定'}
              </div>
              <div className="mt-2">
                <div className="text-sm">
                  <span className="text-gray-500">得分:</span>
                  <span className={classNames('ml-1 font-medium', {
                    'text-green-600': player.final_score > 0,
                    'text-red-600': player.final_score < 0,
                    'text-gray-600': player.final_score === 0
                  })}>
                    {player.final_score}
                  </span>
                </div>
                {player.is_winner && (
                  <div className="text-xs text-green-600 font-medium">🎉 胜利</div>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* 当前操作显示 */}
      <div className="current-action mb-6">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex justify-between items-center">
            <div>
              <span className="text-sm text-gray-500">
                步骤 {currentStep + 1} / {replayData.actions.length}
              </span>
              <div className="text-lg font-medium text-gray-800">
                {currentAction ? getActionDescription(currentAction) : '游戏开始'}
              </div>
              {currentAction && (
                <div className="text-sm text-gray-600">
                  {new Date(currentAction.timestamp).toLocaleTimeString()}
                  {currentAction.score_change !== 0 && (
                    <span className={classNames('ml-2', {
                      'text-green-600': currentAction.score_change > 0,
                      'text-red-600': currentAction.score_change < 0
                    })}>
                      ({currentAction.score_change > 0 ? '+' : ''}{currentAction.score_change}分)
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 控制面板 */}
      <div className="controls bg-gray-50 rounded-lg p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <button
              onClick={handleReset}
              className="px-3 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
            >
              重置
            </button>
            <button
              onClick={handleStepBackward}
              className="px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              disabled={currentStep <= 0}
            >
              上一步
            </button>
            <button
              onClick={handlePlayPause}
              className={classNames('px-4 py-2 text-white rounded', {
                'bg-green-500 hover:bg-green-600': !isPlaying,
                'bg-red-500 hover:bg-red-600': isPlaying
              })}
            >
              {isPlaying ? '暂停' : '播放'}
            </button>
            <button
              onClick={handleStepForward}
              className="px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              disabled={currentStep >= replayData.actions.length - 1}
            >
              下一步
            </button>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <label className="text-sm text-gray-600">播放速度:</label>
              <select
                value={playSpeed}
                onChange={(e) => setPlaySpeed(Number(e.target.value))}
                className="px-2 py-1 border border-gray-300 rounded"
              >
                <option value={2000}>0.5x</option>
                <option value={1000}>1x</option>
                <option value={500}>2x</option>
                <option value={250}>4x</option>
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleExport('json')}
                className="px-3 py-2 bg-indigo-500 text-white rounded hover:bg-indigo-600 text-sm"
              >
                导出JSON
              </button>
              <button
                onClick={() => handleExport('zip')}
                className="px-3 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 text-sm"
              >
                导出ZIP
              </button>
            </div>
          </div>
        </div>

        {/* 进度条 */}
        <div className="progress-bar">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>游戏开始</span>
            <span>游戏结束</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ 
                width: `${((currentStep + 1) / replayData.actions.length) * 100}%` 
              }}
            />
          </div>
          <input
            type="range"
            min="0"
            max={replayData.actions.length - 1}
            value={currentStep}
            onChange={(e) => setCurrentStep(Number(e.target.value))}
            className="w-full mt-2 opacity-0 cursor-pointer absolute"
          />
        </div>
      </div>
    </div>
  );
};

export default ReplayViewer; 