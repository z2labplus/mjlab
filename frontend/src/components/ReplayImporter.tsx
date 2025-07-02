import React, { useState, useCallback } from 'react';
import { motion } from 'framer-motion';

// 转换标准格式为前端期望格式的函数
function convertStandardToFrontendFormat(standardData: any): any {
  const players = [];
  
  // 从 initial_hands 构建 players 数组
  for (const [playerId, handData] of Object.entries(standardData.initial_hands || {})) {
    const playerIdNum = parseInt(playerId);
    const tiles = Array.isArray(handData) ? handData : (handData as any)?.tiles || [];
    
    players.push({
      id: playerIdNum,
      name: playerIdNum === 0 ? `玩家${playerIdNum}(我)` : 
             playerIdNum === 1 ? `玩家${playerIdNum}(下家)` : 
             playerIdNum === 2 ? `玩家${playerIdNum}(对家)` : 
             `玩家${playerIdNum}(上家)`,
      position: playerIdNum,
      initial_hand: tiles,
      missing_suit: standardData.misssuit?.[playerId] || null,
      final_score: 0,
      is_winner: false,
      statistics: {
        draw_count: 0,
        discard_count: 0,
        peng_count: 0,
        gang_count: 0
      }
    });
  }
  
  // 统计每个玩家的操作数量
  for (const action of standardData.actions || []) {
    const player = players.find(p => p.id === action.player_id);
    if (player) {
      switch (action.type) {
        case 'draw':
          player.statistics.draw_count++;
          break;
        case 'discard':
          player.statistics.discard_count++;
          break;
        case 'peng':
          player.statistics.peng_count++;
          break;
        case 'gang':
        case 'jiagang':
          player.statistics.gang_count++;
          break;
      }
    }
  }
  
  // 转换动作格式
  const actions = (standardData.actions || []).map((action: any) => ({
    sequence: action.sequence,
    timestamp: new Date().toISOString(), // 使用当前时间，因为标准格式可能没有时间戳
    player_id: action.player_id,
    action_type: action.type,
    card: action.tile || null,
    target_player: action.target_player !== undefined ? action.target_player : null,
    gang_type: action.gang_type || null,
    score_change: 0
  }));
  
  return {
    game_info: {
      game_id: standardData.game_info?.game_id || 'converted_game',
      start_time: new Date().toISOString(),
      end_time: new Date().toISOString(),
      duration: 1800, // 30分钟
      player_count: players.length,
      game_mode: standardData.mjtype || 'xuezhan_daodi'
    },
    players: players,
    actions: actions,
    final_hands: standardData.final_hands || null, // 传递final_hands数据
    metadata: {
      source: 'standard_format_converted',
      original_format: 'standard',
      converted_at: new Date().toISOString(),
      mjtype: standardData.mjtype,
      misssuit: standardData.misssuit,
      dong: standardData.dong
    }
  };
}

interface ReplayImporterProps {
  onImport: (replayData: any) => void;
  className?: string;
}

const ReplayImporter: React.FC<ReplayImporterProps> = ({ onImport, className }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileUpload = useCallback(async (file: File) => {
    setIsLoading(true);
    setError(null);

    try {
      const text = await file.text();
      let replayData = JSON.parse(text);
      
      // 验证牌谱格式 - 支持两种格式
      const isStandardFormat = replayData.game_info && replayData.initial_hands && replayData.actions;
      const isLegacyFormat = replayData.game_info && replayData.players && replayData.actions;
      
      if (!isStandardFormat && !isLegacyFormat) {
        throw new Error('无效的牌谱格式');
      }
      
      // 如果是标准格式，转换为前端期望的格式
      if (isStandardFormat && !replayData.players) {
        console.log('检测到标准格式文件，正在转换...');
        replayData = convertStandardToFrontendFormat(replayData);
        console.log('转换完成，新格式:', replayData);
      }

      onImport(replayData);
    } catch (err: any) {
      setError(err.message || '导入失败');
    } finally {
      setIsLoading(false);
    }
  }, [onImport]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file && (file.type === 'application/json' || file.name.endsWith('.json'))) {
      handleFileUpload(file);
    } else {
      setError('请选择JSON格式的牌谱文件');
    }
  }, [handleFileUpload]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileUpload(file);
    }
  }, [handleFileUpload]);

  const loadSampleReplay = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // 优先尝试加载标准格式牌谱
      let gameId = 'standard_format_default';
      let replayResponse = await fetch(`/api/v1/replay/${gameId}`);
      let replayResult = await replayResponse.json();
      
      // 如果标准格式牌谱不存在，则尝试导入默认标准格式牌谱
      if (!replayResult.success) {
        console.log('标准格式牌谱不存在，尝试导入...');
        try {
          const importResponse = await fetch('/api/v1/replay/standard/import/default', {
            method: 'POST'
          });
          const importResult = await importResponse.json();
          
          if (importResult.success) {
            gameId = importResult.data.game_id;
            console.log(`标准格式牌谱导入成功: ${gameId}`);
            // 重新获取牌谱
            replayResponse = await fetch(`/api/v1/replay/${gameId}`);
            replayResult = await replayResponse.json();
          }
        } catch (importErr) {
          console.warn('导入标准格式牌谱失败，回退到获取最新牌谱', importErr);
        }
      }
      
      // 如果标准格式牌谱仍然失败，回退到获取最新的游戏列表
      if (!replayResult.success) {
        const listResponse = await fetch('/api/v1/replay/list?limit=1');
        const listResult = await listResponse.json();
        
        if (listResult.success && listResult.data.length > 0) {
          gameId = listResult.data[0].game_id;
          replayResponse = await fetch(`/api/v1/replay/${gameId}`);
          replayResult = await replayResponse.json();
        } else {
          throw new Error('没有可用的示例牌谱');
        }
      }
      
      if (replayResult.success) {
        // 转换为导出格式
        const exportResponse = await fetch(`/api/v1/replay/${gameId}/export/json`);
        const replayData = await exportResponse.text();
        const parsedData = JSON.parse(replayData);
        
        console.log(`成功加载牌谱: ${gameId}, 数据格式:`, parsedData.metadata?.source || 'unknown');
        onImport(parsedData);
      } else {
        throw new Error('获取牌谱失败');
      }
    } catch (err: any) {
      console.error('加载示例牌谱失败:', err);
      setError(err.message || '加载示例失败');
    } finally {
      setIsLoading(false);
    }
  }, [onImport]);

  return (
    <div className={`replay-importer ${className}`}>
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">导入牌谱</h3>
        
        {/* 拖拽上传区域 */}
        <motion.div
          className={`
            border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all
            ${isDragging 
              ? 'border-blue-500 bg-blue-50' 
              : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
            }
          `}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          animate={{
            scale: isDragging ? 1.02 : 1,
            borderColor: isDragging ? '#3B82F6' : '#D1D5DB'
          }}
        >
          <input
            type="file"
            accept=".json"
            onChange={handleFileSelect}
            className="hidden"
            id="replay-file-input"
          />
          
          {isLoading ? (
            <div className="py-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
              <p className="text-gray-600">处理中...</p>
            </div>
          ) : (
            <>
              <div className="text-4xl mb-4">📁</div>
              <p className="text-lg text-gray-700 mb-2">
                拖拽JSON牌谱文件到这里
              </p>
              <p className="text-sm text-gray-500 mb-4">
                或点击选择文件
              </p>
              <label
                htmlFor="replay-file-input"
                className="inline-block px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 cursor-pointer"
              >
                选择文件
              </label>
            </>
          )}
        </motion.div>

        {/* 错误提示 */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg"
          >
            <p className="text-red-600 text-sm">❌ {error}</p>
          </motion.div>
        )}
      </div>

      {/* 示例牌谱 */}
      <div className="border-t pt-6">
        <h4 className="text-md font-medium text-gray-700 mb-3">快速开始</h4>
        <div className="flex gap-3">
          <button
            onClick={loadSampleReplay}
            disabled={isLoading}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? '加载中...' : '加载示例牌谱'}
          </button>
          
          <a
            href="/api/v1/replay/list"
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            查看所有牌谱
          </a>
        </div>
        
        <p className="text-xs text-gray-500 mt-2">
          💡 提示：你也可以先运行 <code className="bg-gray-100 px-1 rounded">python create_sample_replay.py</code> 创建示例牌谱
        </p>
      </div>
    </div>
  );
};

export default ReplayImporter;