import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useGameStore } from '../stores/gameStore';
import { Tile, TileType, MeldType, GangType } from '../types/mahjong';
import MahjongTile from './MahjongTile';

interface DirectKongOperatorProps {
  onClose?: () => void;
  className?: string;
}

type OperationStep = 'selectPlayer' | 'selectOperation' | 'selectSource' | 'selectTile' | 'completed';
type SourcePlayer = 0 | 1 | 2 | 3;

const DirectKongOperator: React.FC<DirectKongOperatorProps> = ({ onClose, className }) => {
  const [currentStep, setCurrentStep] = useState<OperationStep>('selectPlayer');
  const [selectedPlayer, setSelectedPlayer] = useState<number | null>(null);
  const [selectedOperation, setSelectedOperation] = useState<string | null>(null);
  const [selectedSource, setSelectedSource] = useState<SourcePlayer | null>(null);
  const [selectedTile, setSelectedTile] = useState<Tile | null>(null);

  const addMeld = useGameStore(state => state.addMeld);
  const resetGame = useGameStore(state => state.resetGame);

  const playerNames = ['我', '下家', '对家', '上家'];
  
  // 可选择的麻将牌
  const availableTiles: Tile[] = [
    { type: TileType.WAN, value: 1 },
    { type: TileType.WAN, value: 2 },
    { type: TileType.WAN, value: 3 },
    { type: TileType.WAN, value: 4 },
    { type: TileType.WAN, value: 5 },
    { type: TileType.TIAO, value: 1 },
    { type: TileType.TIAO, value: 2 },
    { type: TileType.TIAO, value: 3 },
    { type: TileType.TONG, value: 1 },
    { type: TileType.TONG, value: 2 },
    { type: TileType.TONG, value: 3 },
  ];

  // 获取被杠玩家选项 - 排除步骤1选择的玩家
  const getAvailableSourcePlayers = () => {
    console.log('getAvailableSourcePlayers: selectedPlayer =', selectedPlayer);
    
    if (selectedPlayer === null) {
      console.log('selectedPlayer为null，返回空数组');
      return [];
    }
    
    const allPlayers = ['我', '下家', '对家', '上家'];
    const result = allPlayers
      .map((name, index) => ({ name, index }))
      .filter(player => player.index !== selectedPlayer);
    
    console.log('可用的被杠玩家:', result);
    return result;
  };

  const handlePlayerSelect = (playerId: number) => {
    setSelectedPlayer(playerId);
    setCurrentStep('selectOperation');
  };

  const handleOperationSelect = (operation: string) => {
    console.log('选择操作:', operation);
    setSelectedOperation(operation);
    
    if (operation === '直杠') {
      // 选择直杠时保持在当前步骤，显示步骤2.1
      console.log('选择了直杠，保持在selectOperation步骤');
    } else {
      // 如果不是直杠，直接跳到选择牌
      console.log('选择了其他操作，跳转到selectTile步骤');
      setCurrentStep('selectTile');
    }
  };

  const handleSourceSelect = (sourcePlayerIndex: number) => {
    console.log('选择被杠玩家:', sourcePlayerIndex, playerNames[sourcePlayerIndex]);
    setSelectedSource(sourcePlayerIndex as SourcePlayer);
    setCurrentStep('selectTile');
  };

  const handleTileSelect = (tile: Tile) => {
    setSelectedTile(tile);
    
    // 创建直杠
    if (selectedPlayer !== null && selectedSource !== null) {
      const directKongMeld = {
        type: MeldType.GANG,
        gang_type: GangType.MING_GANG,
        tiles: [tile, tile, tile, tile],
        exposed: true,
        source_player: selectedSource
      };
      
      addMeld(selectedPlayer, directKongMeld);
      setCurrentStep('completed');
    }
  };

  const handleReset = () => {
    setCurrentStep('selectPlayer');
    setSelectedPlayer(null);
    setSelectedOperation(null);
    setSelectedSource(null);
    setSelectedTile(null);
  };

  const getStepTitle = () => {
    switch (currentStep) {
      case 'selectPlayer': return '步骤1：选择杠的玩家';
      case 'selectOperation': return '步骤2：选择操作';
      case 'selectSource': return '步骤2.1：选择被杠玩家';
      case 'selectTile': return '步骤3：选择麻将牌';
      case 'completed': return '操作完成';
      default: return '';
    }
  };

  return (
    <motion.div
      className={`bg-white rounded-2xl shadow-2xl border-2 border-gray-200 p-6 ${className}`}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* 标题栏 */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">直杠操作器</h2>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
          >
            ×
          </button>
        )}
      </div>

      {/* 步骤指示器 */}
      <div className="mb-6">
        <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
          <span className={currentStep === 'selectPlayer' ? 'text-blue-600 font-bold' : ''}>选择玩家</span>
          <span className={currentStep === 'selectOperation' ? 'text-blue-600 font-bold' : ''}>选择操作</span>
          <span className={currentStep === 'selectSource' ? 'text-blue-600 font-bold' : ''}>选择来源</span>
          <span className={currentStep === 'selectTile' ? 'text-blue-600 font-bold' : ''}>选择牌</span>
          <span className={currentStep === 'completed' ? 'text-green-600 font-bold' : ''}>完成</span>
        </div>
        <div className="flex">
          {['selectPlayer', 'selectOperation', 'selectSource', 'selectTile', 'completed'].map((step, index) => (
            <div key={step} className="flex-1">
              <div className={`h-2 rounded-full ${
                currentStep === step ? 'bg-blue-500' : 
                ['selectPlayer', 'selectOperation', 'selectSource', 'selectTile', 'completed'].indexOf(currentStep) > index ? 'bg-green-500' : 'bg-gray-200'
              }`} />
            </div>
          ))}
        </div>
      </div>

      {/* 当前步骤标题 */}
      <h3 className="text-xl font-semibold text-gray-700 mb-4">{getStepTitle()}</h3>

      {/* 步骤内容 */}
      <AnimatePresence mode="wait">
        {/* 步骤1：选择杠的玩家 */}
        {currentStep === 'selectPlayer' && (
          <motion.div
            key="selectPlayer"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="grid grid-cols-2 gap-4"
          >
            {playerNames.map((name, index) => (
              <button
                key={index}
                onClick={() => handlePlayerSelect(index)}
                className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-all duration-200 text-lg font-semibold"
              >
                {name}
              </button>
            ))}
          </motion.div>
        )}

        {/* 步骤2：选择操作 */}
        {currentStep === 'selectOperation' && (
          <motion.div
            key="selectOperation"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div className="text-gray-600 mb-4">
              为玩家 <span className="font-bold text-blue-600">{playerNames[selectedPlayer!]}</span> 选择操作：
            </div>
            
            {/* 操作选择 */}
            <div className="grid grid-cols-3 gap-4">
              {['直杠', '加杠', '暗杠'].map((operation) => (
                <button
                  key={operation}
                  onClick={() => handleOperationSelect(operation)}
                  className={`p-4 border-2 rounded-lg transition-all duration-200 text-lg font-semibold ${
                    selectedOperation === operation
                      ? 'border-blue-500 bg-blue-100 text-blue-700' 
                      : 'border-gray-200 hover:border-gray-400 hover:bg-gray-50'
                  }`}
                >
                  {operation}
                  {selectedOperation === operation && ' ✓'}
                </button>
              ))}
            </div>

            {/* 步骤2.1：选择被杠玩家 - 只有选择直杠时显示 */}
            {selectedOperation === '直杠' && (() => {
              console.log('渲染检查: selectedOperation =', selectedOperation, 'currentStep =', currentStep);
              return (
                <div className="border-t border-gray-200 pt-6 mt-6">
                  <div className="text-lg font-semibold text-gray-700 mb-4">
                    步骤2.1：选择被杠玩家
                  </div>
                  <div className="text-gray-600 mb-4">
                    选择被 <span className="font-bold text-blue-600">{playerNames[selectedPlayer!]}</span> 杠的玩家：
                  </div>
                  
                  {/* 调试信息 */}
                  <div className="text-xs text-gray-400 mb-2">
                    DEBUG: selectedPlayer = {selectedPlayer}, availablePlayers = {JSON.stringify(getAvailableSourcePlayers())}
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4">
                    {getAvailableSourcePlayers().map((player) => (
                      <button
                        key={player.index}
                        onClick={() => handleSourceSelect(player.index)}
                        className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-all duration-200 text-lg font-semibold flex items-center justify-center gap-2"
                      >
                        <span className="text-2xl">{['🏠', '👤', '👥', '👆'][player.index]}</span>
                        <span>{player.name}</span>
                      </button>
                    ))}
                  </div>
                </div>
              );
            })()}
          </motion.div>
        )}

        {/* 步骤3：选择麻将牌 */}
        {currentStep === 'selectTile' && (
          <motion.div
            key="selectTile"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-4"
          >
            <div className="text-gray-600 mb-4">
              选择 <span className="font-bold text-blue-600">{playerNames[selectedPlayer!]}</span> 
              {selectedOperation === '直杠' && selectedSource !== null && (
                <>从 <span className="font-bold text-green-600">{playerNames[selectedSource]}</span></>
              )} 杠的牌：
            </div>
            <div className="grid grid-cols-6 gap-3">
              {availableTiles.map((tile, index) => (
                <div key={index} className="flex justify-center">
                  <MahjongTile
                    tile={tile}
                    size="medium"
                    variant="default"
                    onClick={() => handleTileSelect(tile)}
                    className="hover:scale-105 cursor-pointer"
                  />
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* 完成步骤 */}
        {currentStep === 'completed' && (
          <motion.div
            key="completed"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center space-y-6"
          >
            <div className="text-6xl">✅</div>
            <div className="text-xl font-semibold text-green-600">
              直杠操作完成！
            </div>
            <div className="text-gray-600 space-y-2">
              <div>杠牌玩家：<span className="font-bold">{playerNames[selectedPlayer!]}</span></div>
              <div>操作：<span className="font-bold">直杠</span></div>
              <div>被杠玩家：<span className="font-bold">{playerNames[selectedSource!]}</span></div>
              <div className="flex items-center justify-center gap-2">
                <span>牌型：</span>
                <div className="flex">
                  {[1, 2, 3, 4].map((_, index) => (
                    <MahjongTile
                      key={index}
                      tile={selectedTile!}
                      size="small"
                      variant={index === 3 ? "selected" : "default"}
                      seamless={true}
                    />
                  ))}
                </div>
              </div>
              <div className="text-sm text-gray-500">
                第4张牌右上角将显示：<span className="font-bold text-red-600">{playerNames[selectedSource!]}</span>
              </div>
            </div>
            
            <div className="flex gap-4 justify-center">
              <button
                onClick={handleReset}
                className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                再次操作
              </button>
              {onClose && (
                <button
                  onClick={onClose}
                  className="px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                >
                  关闭
                </button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 操作按钮 */}
      {currentStep !== 'completed' && currentStep !== 'selectPlayer' && (
        <div className="flex gap-4 mt-6">
          <button
            onClick={handleReset}
            className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
          >
            重新开始
          </button>
        </div>
      )}
    </motion.div>
  );
};

export default DirectKongOperator; 