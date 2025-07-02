import React, { useState, useRef, useEffect } from 'react';
import { AnimatePresence } from 'framer-motion';
import { useWebSocketGameStore } from '../stores/webSocketGameStore';
import { Tile, TileType, createTile, tileToString, tilesEqual, Meld, MeldType, GangType, calculateRemainingTilesByType } from '../types/mahjong';
import MahjongTile from './MahjongTile';
import MahjongTable from './MahjongTable';
import { CardBackStyle } from './MahjongTile';

interface GameBoardProps {
  className?: string;
  cardBackStyle?: CardBackStyle;
}

const GameBoard: React.FC<GameBoardProps> = ({ className, cardBackStyle = 'elegant' }) => {
  const { 
    gameState,
    isConnected,
    lastSyncTime,
    addTileToHand,
    discardTile,
    pengTile,
    gangTile,
    setMissingSuit,
    nextPlayer,
    resetGame,
    syncGameStateFromWS,
    // 本地操作方法（用于兼容）
    addTileToHandLocal,
    removeTileFromHand,
    addDiscardedTile,
    addMeld,
    reduceHandTilesCount,
    setPlayerMissingSuit
  } = useWebSocketGameStore();
  
  // 从游戏状态中获取我的手牌和弃牌
  const myHand = gameState.player_hands['0']?.tiles || [];
  const discardedTiles = gameState.discarded_tiles || [];
  
  const [selectedTiles, setSelectedTiles] = useState<Tile[]>([]);
  const [selectedPlayer, setSelectedPlayer] = useState<number>(1); // 默认选择我（显示索引1，对应Player ID 0）
  const [operationType, setOperationType] = useState<'hand' | 'discard' | 'peng' | 'angang' | 'zhigang' | 'jiagang'>('hand');
  const [selectedSourcePlayer, setSelectedSourcePlayer] = useState<number | null>(null); // 新增：被杠玩家选择
  const [autoSync, setAutoSync] = useState(false);
  const autoSyncTimer = useRef<NodeJS.Timeout | null>(null);
  
  // 计算每种牌的剩余数量
  const remainingTilesByType = calculateRemainingTilesByType(gameState);
  
  // 调试信息：打印游戏状态和计算结果
  React.useEffect(() => {
    console.log('🎮 当前游戏状态:', gameState);
    console.log('📊 剩余牌数统计:', remainingTilesByType);
    
    // 打印每个玩家的详细信息
    Object.entries(gameState.player_hands).forEach(([playerId, hand]) => {
      const handTileCount = hand.tile_count !== undefined ? hand.tile_count : (hand.tiles?.length || 0);
      console.log(`玩家${playerId}:`, {
        手牌数量: handTileCount,
        碰杠数量: hand.melds.length,
        碰杠详情: hand.melds.map(meld => ({
          类型: meld.type,
          牌: meld.tiles.map(t => `${t.value}${t.type}`),
          数量: meld.tiles.length
        }))
      });
    });
  }, [gameState, remainingTilesByType]);
  
  // 自动同步副作用
  useEffect(() => {
    if (autoSync) {
      autoSyncTimer.current = setInterval(() => {
        syncGameStateFromWS();
      }, 500);
    } else if (autoSyncTimer.current) {
      clearInterval(autoSyncTimer.current);
      autoSyncTimer.current = null;
    }
    // 清理定时器
    return () => {
      if (autoSyncTimer.current) {
        clearInterval(autoSyncTimer.current);
        autoSyncTimer.current = null;
      }
    };
  }, [autoSync, syncGameStateFromWS]);
  
  // 所有可选的牌
  const availableTiles: Tile[] = [];
  
  // 万 1-9
  for (let i = 1; i <= 9; i++) {
    availableTiles.push(createTile(TileType.WAN, i));
  }
  
  // 条 1-9
  for (let i = 1; i <= 9; i++) {
    availableTiles.push(createTile(TileType.TIAO, i));
  }
  
  // 筒 1-9
  for (let i = 1; i <= 9; i++) {
    availableTiles.push(createTile(TileType.TONG, i));
  }

  // 用于界面显示的玩家顺序：上家、我、下家、对家
  const displayOrder = [3, 0, 1, 2]; // 对应Player ID：上家=3，我=0，下家=1，对家=2
  const playerNames = ['我', '下家', '对家', '上家']; // Player ID映射：0=我，1=下家，2=对家，3=上家
  const playerColors = ['text-blue-600', 'text-green-600', 'text-red-600', 'text-yellow-600'];
  const displayNames = displayOrder.map(id => playerNames[id]);
  const displayColors = displayOrder.map(id => playerColors[id]);

  const handleTileClick = async (tile: Tile) => {
    const actualPlayerId = displayOrder[selectedPlayer]; // 转换显示索引为实际Player ID
    
    try {
      if (operationType === 'hand') {
        // 为当前选中的玩家添加手牌 - 使用WebSocket方法
        await addTileToHand(actualPlayerId, tile);
        console.log(`✅ 玩家${actualPlayerId}添加手牌成功: ${tile.value}${tile.type}`);
      } else if (operationType === 'discard') {
        // 弃牌 - 使用WebSocket方法
        await discardTile(actualPlayerId, tile);
        console.log(`✅ 玩家${actualPlayerId}弃牌成功: ${tile.value}${tile.type}`);
      } else if (operationType === 'peng') {
        // 碰牌 - 使用WebSocket方法
        const sourcePlayerId = selectedSourcePlayer !== null ? displayOrder[selectedSourcePlayer] : undefined;
        await pengTile(actualPlayerId, tile, sourcePlayerId);
        console.log(`✅ 玩家${actualPlayerId}碰牌成功: ${tile.value}${tile.type}`);
      } else if (operationType === 'angang') {
        // 暗杠 - 使用WebSocket方法
        await gangTile(actualPlayerId, tile, 'angang');
        console.log(`✅ 玩家${actualPlayerId}暗杠成功: ${tile.value}${tile.type}`);
      } else if (operationType === 'zhigang') {
        // 直杠 - 使用WebSocket方法
        const sourcePlayerId = selectedSourcePlayer !== null ? displayOrder[selectedSourcePlayer] : undefined;
        await gangTile(actualPlayerId, tile, 'zhigang', sourcePlayerId);
        console.log(`✅ 玩家${actualPlayerId}直杠成功: ${tile.value}${tile.type}`);
      } else if (operationType === 'jiagang') {
        // 加杠 - 使用WebSocket方法
        await gangTile(actualPlayerId, tile, 'jiagang');
        console.log(`✅ 玩家${actualPlayerId}加杠成功: ${tile.value}${tile.type}`);
      }
    } catch (error) {
      console.error('操作失败:', error);
    }
  };
  
  const handleHandTileClick = (tile: Tile) => {
    const isSelected = selectedTiles.some(t => tilesEqual(t, tile));
    
    if (isSelected) {
      setSelectedTiles(prev => prev.filter(t => !tilesEqual(t, tile)));
    } else {
      setSelectedTiles(prev => [...prev, tile]);
    }
  };
  
  const handleDiscardSelected = () => {
    selectedTiles.forEach(tile => {
      removeTileFromHand(0, tile);
      addDiscardedTile(tile, 0);
    });
    setSelectedTiles([]);
  };
  
  const handleClearHand = async () => {
    try {
      await resetGame();
      setSelectedTiles([]);
      console.log('✅ 游戏重置成功');
    } catch (error) {
      console.error('❌ 重置游戏失败:', error);
    }
  };

  // 处理操作类型改变
  const handleOperationTypeChange = (newOperationType: 'hand' | 'discard' | 'peng' | 'angang' | 'zhigang' | 'jiagang') => {
    setOperationType(newOperationType);
    // 如果不是直杠或碰牌操作，清除被杠/被碰玩家的选择
    if (newOperationType !== 'zhigang' && newOperationType !== 'peng') {
      setSelectedSourcePlayer(null);
    }
  };



  // 获取可选择的被杠玩家（排除当前杠牌的玩家）
  const getAvailableSourcePlayers = () => {
    return displayNames
      .map((name, index) => ({ name, index }))
      .filter(player => player.index !== selectedPlayer);
  };

  // 获取操作类型的中文名称
  const getOperationName = (type: 'hand' | 'discard' | 'peng' | 'angang' | 'zhigang' | 'jiagang'): string => {
          const operationMap = {
        'hand': '添加手牌',
        'discard': '弃牌',
        'peng': '碰牌',
        'angang': '暗杠',
        'zhigang': '直杠',
        'jiagang': '加杠'
      };
    return operationMap[type] || type;
  };

  // 获取指定牌的剩余数量
  const getTileRemainingCount = (tile: Tile): number => {
    const key = `${tile.type}-${tile.value}`;
    return remainingTilesByType[key] || 0;
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* 麻将桌面区域 - 与牌谱回放布局一致 */}
      <div className="bg-white rounded-lg shadow-lg p-4">
        <MahjongTable cardBackStyle={cardBackStyle} />
      </div>
      
      {/* 所有麻将牌显示区域 - 与牌谱回放布局一致 */}
      <div className="bg-white rounded-lg shadow-lg p-4">
        <div className="flex items-center gap-3 mb-3">
          <div className="text-base font-semibold text-gray-800">🀄 所有麻将牌</div>
          <div className="text-xs text-gray-500">剩余数量实时显示</div>
        </div>
        
        <div className="space-y-2">
          <div>
            <div className="flex gap-0.5 flex-wrap">
              {/* 万子 */}
              {availableTiles
                .filter(tile => tile.type === TileType.WAN)
                .map((tile, index) => {
                  const remainingCount = getTileRemainingCount(tile);
                  return (
                    <div key={`wan-${tile.value}`} className="relative">
                      <MahjongTile
                        tile={tile}
                        size="tiny"
                        variant="default"
                        cardBackStyle={cardBackStyle}
                        remainingCount={remainingCount}
                        animationDelay={index * 0.01}
                      />
                    </div>
                  );
                })}

              {/* 条子 */}
              {availableTiles
                .filter(tile => tile.type === TileType.TIAO)
                .map((tile, index) => {
                  const remainingCount = getTileRemainingCount(tile);
                  return (
                    <div key={`tiao-${tile.value}`} className="relative">
                      <MahjongTile
                        tile={tile}
                        size="tiny"
                        variant="default"
                        cardBackStyle={cardBackStyle}
                        remainingCount={remainingCount}
                        animationDelay={index * 0.01}
                      />
                    </div>
                  );
                })}

              {/* 筒子 */}
              {availableTiles
                .filter(tile => tile.type === TileType.TONG)
                .map((tile, index) => {
                  const remainingCount = getTileRemainingCount(tile);
                  return (
                    <div key={`tong-${tile.value}`} className="relative">
                      <MahjongTile
                        tile={tile}
                        size="tiny"
                        variant="default"
                        cardBackStyle={cardBackStyle}
                        remainingCount={remainingCount}
                        animationDelay={index * 0.01}
                      />
                    </div>
                  );
                })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GameBoard; 