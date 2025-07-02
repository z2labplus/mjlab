import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useWebSocketGameStore } from '../stores/webSocketGameStore';
import { calculateRemainingTiles, calculateRemainingTilesByType, TileType } from '../types/mahjong';
import { Tile, MeldType, GangType, HandTiles } from '../types/mahjong';
import MahjongTile from './MahjongTile';
import SimpleSourceIndicator from './SimpleSourceIndicator';
import { CardBackStyle } from './MahjongTile';

interface MahjongTableProps {
  className?: string;
  cardBackStyle?: CardBackStyle;
  gameState?: any; // 可选的游戏状态，用于回放模式
}

const MahjongTable: React.FC<MahjongTableProps> = ({ className, cardBackStyle = 'elegant', gameState: propGameState }) => {
  const webSocketGameState = useWebSocketGameStore(state => state.gameState);
  const { reorderPlayerHand, removeTileFromHand, addDiscardedTile, syncGameStateFromAPI } = useWebSocketGameStore(state => ({
    reorderPlayerHand: state.reorderPlayerHand,
    removeTileFromHand: state.removeTileFromHand,
    addDiscardedTile: state.addDiscardedTile,
    syncGameStateFromAPI: state.syncGameStateFromAPI
  }));
  
  // 使用传入的gameState或默认的WebSocket gameState
  const gameState = propGameState || webSocketGameState;
  
  // 🔧 只在实时模式下自动同步游戏状态（没有传入gameState时）
  useEffect(() => {
    if (propGameState) return; // 如果有传入的gameState，不进行自动同步
    
    const interval = setInterval(() => {
      syncGameStateFromAPI();
    }, 1000); // 每秒同步一次
    return () => clearInterval(interval);
  }, [syncGameStateFromAPI, propGameState]);
  
  // 获取玩家手牌，如果不存在则返回空数组
  const getPlayerHand = (playerId: number): HandTiles => {
    const playerIdStr = playerId.toString();
    const hand = gameState.player_hands[playerIdStr];
    if (!hand) {
      return { 
        tiles: [], 
        tile_count: 0, 
        melds: [],
        missing_suit: null,
        is_winner: false,
        win_type: undefined,
        win_tile: undefined,
        dianpao_player_id: undefined
      };
    }
    return {
      tiles: hand.tiles || [],
      tile_count: hand.tile_count || (hand.tiles?.length || 0),
      melds: hand.melds || [],
      missing_suit: hand.missing_suit || null,
      is_winner: hand.is_winner || false,
      win_type: hand.win_type,
      win_tile: hand.win_tile,
      dianpao_player_id: hand.dianpao_player_id
    };
  };
  
  const player0Hand = getPlayerHand(0);
  const player1Hand = getPlayerHand(1);
  const player2Hand = getPlayerHand(2);
  const player3Hand = getPlayerHand(3);
  
  // 获取玩家弃牌，如果不存在则返回空数组
  const getPlayerDiscards = (playerId: number) => {
    const playerIdStr = playerId.toString();
    return gameState.player_discarded_tiles?.[playerIdStr] || [];
  };
  
  const player0Discards = getPlayerDiscards(0);
  const player1Discards = getPlayerDiscards(1);
  const player2Discards = getPlayerDiscards(2);
  const player3Discards = getPlayerDiscards(3);

  // 拖拽状态管理
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);

  // 剩余牌数：使用原有逻辑（108 - 所有已使用的牌）
  const remainingTiles = calculateRemainingTiles(gameState);
  
  // 计算未出牌数：所有可见麻将牌的剩余数量之和（基于可见牌逻辑）
  const calculateUnplayedTiles = (): number => {
    const remainingTilesByType = calculateRemainingTilesByType(gameState);
    let unplayedTotal = 0;
    
    // 万子 1-9
    for (let i = 1; i <= 9; i++) {
      const count = remainingTilesByType[`${TileType.WAN}-${i}`] || 0;
      if (count > 0) {
        unplayedTotal += count;
      }
    }
    
    // 条子 1-9
    for (let i = 1; i <= 9; i++) {
      const count = remainingTilesByType[`${TileType.TIAO}-${i}`] || 0;
      if (count > 0) {
        unplayedTotal += count;
      }
    }
    
    // 筒子 1-9
    for (let i = 1; i <= 9; i++) {
      const count = remainingTilesByType[`${TileType.TONG}-${i}`] || 0;
      if (count > 0) {
        unplayedTotal += count;
      }
    }
    
    return unplayedTotal;
  };
  
  // 计算碰杠牌数量
  const calculateMeldTilesCount = (melds: any[] | undefined): number => {
    if (!melds) return 0;
    return melds.reduce((total, meld) => total + (meld.tiles?.length || 0), 0);
  };
  
  // 计算玩家区域需要的宽度
  const calculatePlayerAreaWidth = () => {
    // 获取所有玩家的手牌数量
    const playerHandCounts = [
      player0Hand.tile_count || (player0Hand.tiles?.length || 0),
      player1Hand.tile_count || (player1Hand.tiles?.length || 0),
      player2Hand.tile_count || (player2Hand.tiles?.length || 0),
      player3Hand.tile_count || (player3Hand.tiles?.length || 0)
    ];
    
    // 获取所有玩家的碰杠牌数量
    const playerMeldCounts = [
      calculateMeldTilesCount(player0Hand.melds),
      calculateMeldTilesCount(player1Hand.melds),
      calculateMeldTilesCount(player2Hand.melds),
      calculateMeldTilesCount(player3Hand.melds)
    ];
    
    // 计算每个玩家的总牌数（手牌 + 碰杠牌）
    const totalTileCounts = playerHandCounts.map((handCount, index) => handCount + playerMeldCounts[index]);
    
    // 找出最大的牌数
    const maxTileCount = Math.max(...totalTileCounts);
    
    // 确保牌数在13-20之间
    const clampedTileCount = Math.min(Math.max(maxTileCount, 13), 20);
    
    // 计算宽度（每个麻将牌32px）
    return `${clampedTileCount * 34}px`;
  };
  
  // 获取动态宽度
  const playerAreaWidth = calculatePlayerAreaWidth();
  
  // 未出牌数：等于选择区域中显示的所有牌的右上角数字之和
  const unplayedTiles = calculateUnplayedTiles();
  
  const playerNames = ['玩家0(我)', '玩家1(下家)', '玩家2(对家)', '玩家3(上家)'];
  const playerColors = ['bg-blue-50 border-blue-200', 'bg-green-50 border-green-200', 'bg-red-50 border-red-200', 'bg-yellow-50 border-yellow-200'];
  
  // 展示顺序：对家、上家下家、我
  const displayOrder = [2, 3, 1, 0];

  // 拖拽事件处理函数
  const handleDragStart = (e: React.DragEvent, index: number, playerId: number) => {
    // 只允许"我"（playerId=0）的手牌拖拽
    if (playerId !== 0) {
      e.preventDefault();
      return;
    }
    
    setDraggedIndex(index);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', index.toString());
  };

  const handleDragOver = (e: React.DragEvent, index: number, playerId: number) => {
    if (playerId !== 0 || draggedIndex === null) {
      return;
    }
    
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverIndex(index);
  };

  const handleDragEnter = (e: React.DragEvent, index: number, playerId: number) => {
    if (playerId !== 0) {
      return;
    }
    
    e.preventDefault();
    setDragOverIndex(index);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    // 只有当鼠标真正离开组件时才清除dragOverIndex
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX;
    const y = e.clientY;
    
    if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) {
      setDragOverIndex(null);
    }
  };

  const handleDrop = (e: React.DragEvent, targetIndex: number, playerId: number) => {
    if (playerId !== 0 || draggedIndex === null) {
      return;
    }
    
    e.preventDefault();
    
    const playerHand = [player0Hand, player1Hand, player2Hand, player3Hand][playerId];
    const newTiles = [...(playerHand.tiles || [])];
    
    // 移动牌到新位置
    const draggedTile = newTiles[draggedIndex];
    newTiles.splice(draggedIndex, 1);
    newTiles.splice(targetIndex, 0, draggedTile);
    
    // 更新游戏状态
    reorderPlayerHand(playerId, newTiles);
    
    // 重置拖拽状态
    setDraggedIndex(null);
    setDragOverIndex(null);
  };

  const handleDragEnd = () => {
    setDraggedIndex(null);
    setDragOverIndex(null);
  };

  // 双击事件处理函数 - 弃牌
  const handleTileDoubleClick = (tile: Tile, index: number, playerId: number) => {
    // 只允许"我"（playerId=0）的手牌双击弃牌
    if (playerId !== 0) {
      return;
    }
    
    // 从手牌中移除
    removeTileFromHand(playerId, tile);
    
    // 添加到弃牌堆
    addDiscardedTile(tile, playerId);
  };

  // 渲染弃牌组（不换行，一行显示）
  const renderDiscardGroup = (tiles: Tile[], prefix: string) => {
    if (tiles.length === 0) return null;
    
    return (
      <div className="flex gap-0">
        {tiles.map((tile: Tile, index: number) => (
          <MahjongTile
            key={`${prefix}-discard-${index}`}
            tile={tile}
            size="tiny"
            variant="disabled"
            seamless={true}
            animationDelay={index * 0.01}
            cardBackStyle={cardBackStyle}
          />
        ))}
      </div>
    );
  };

  // 渲染单个玩家区域
  const renderPlayerArea = (playerId: number) => {
    const hand = [player0Hand, player1Hand, player2Hand, player3Hand][playerId];
    const discards = [player0Discards, player1Discards, player2Discards, player3Discards][playerId];
    
    // 🔧 调试：输出玩家手牌状态
    if (playerId !== 0) {
      console.log(`🎮 玩家${playerId}状态:`, {
        tiles: hand.tiles,
        tiles_type: typeof hand.tiles,
        tiles_length: hand.tiles ? hand.tiles.length : 'null',
        tile_count: hand.tile_count,
        show_all_hands: gameState.show_all_hands,
        game_ended: gameState.game_ended,
        condition_result: (playerId === 0 || gameState.game_ended || gameState.show_all_hands) && hand.tiles && Array.isArray(hand.tiles) && hand.tiles.length > 0
      });
    }
    
    // 检查是否是当前玩家（需要闪亮边框）
    const isCurrentPlayer = gameState.current_player === playerId;
    
    // 动态类名：当前玩家有闪亮动画
    const playerAreaClassName = `border-2 rounded-lg p-4 ${playerColors[playerId]} transition-all duration-200 hover:shadow-md ${
      isCurrentPlayer 
        ? 'current-player-glow' 
        : ''
    }`;
    
    return (
      <div className={playerAreaClassName} style={{ height: '160px', }}>
        {/* 玩家名称和统计信息 */}
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold text-gray-800">{playerNames[playerId]}</h3>
            {/* 定缺显示 */}
            {(() => {
              try {
                const playerIdStr = playerId.toString();
                const playerHand = gameState?.player_hands?.[playerIdStr];
                const missingSuit = playerHand?.missing_suit;
                
                if (missingSuit && missingSuit !== null && missingSuit !== '') {
                  const suitDisplayNames = {
                    'wan': '万',
                    'tiao': '条', 
                    'tong': '筒'
                  };
                  
                  const displayName = suitDisplayNames[missingSuit as keyof typeof suitDisplayNames] || missingSuit;
                  
                  return (
                    <span className="text-sm font-bold text-yellow-500 bg-yellow-50 px-2 py-1 rounded-md border border-yellow-300">
                      {displayName}
                    </span>
                  );
                }
                return null;
              } catch (error) {
                console.warn('定缺显示错误:', error);
                return null;
              }
            })()}
            <div className="text-sm text-gray-600">
              (手牌: {hand.tile_count || (hand.tiles?.length || 0)} | 碰杠: {calculateMeldTilesCount(hand.melds)} | 弃牌: {discards.length})
            </div>
          </div>
              {/* 胜利信息显示 */}
              {hand.is_winner && (
                <div className="flex items-center gap-2 ml-4">
                  <motion.div
                    initial={{ scale: 0, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ 
                      type: "spring", 
                      stiffness: 300, 
                      damping: 20,
                      delay: 0.2 
                    }}
                    className="flex items-center gap-2 bg-gradient-to-r from-yellow-400 to-orange-500 text-white px-3 py-1 rounded-full shadow-lg border-2 border-yellow-300"
                  >
                    {/* 胜利图标 */}
                    <motion.span
                      animate={{ 
                        rotate: [0, 10, -10, 0],
                        scale: [1, 1.1, 1]
                      }}
                      transition={{ 
                        duration: 1.5, 
                        repeat: Infinity, 
                        ease: "easeInOut" 
                      }}
                      className="text-lg"
                    >
                      🏆
                    </motion.span>
                    
                    {/* 胜利牌面 */}
                    {hand.win_tile && (
                      <div className="flex items-center gap-1">
                                                 <span className="text-sm font-bold">
                           {hand.win_tile.value}
                           {hand.win_tile.type === TileType.WAN ? '万' : 
                            hand.win_tile.type === TileType.TIAO ? '条' : 
                            hand.win_tile.type === TileType.TONG ? '筒' : ''}
                         </span>
                      </div>
                    )}
                    
                    {/* 胜利类型 */}
                    <span className="text-sm font-bold">
                      {hand.win_type === 'zimo' ? '自摸' : '点炮'}
                    </span>
                    
                    {/* 点炮者信息 */}
                    {hand.win_type === 'dianpao' && hand.dianpao_player_id !== undefined && (
                      <span className="text-xs opacity-90">
                        (点炮者: {playerNames[hand.dianpao_player_id]})
                      </span>
                    )}
                  </motion.div>
                </div>
              )}
        </div>

        {/* 内容区域 */}
        <div style={{ height: '80px', }}>
          {/* 手牌和碰杠牌 - 分开显示，手牌与碰杠牌间有较大间距(gap-4) */}
          <div className="mb-1">
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: '20px'}}>
              {/* 手牌区域 */}
              {(() => {
                // 🔧 修复手牌数量计算：优先使用实际tiles长度，否则使用tile_count
                const actualTilesCount = hand.tiles && Array.isArray(hand.tiles) ? hand.tiles.length : 0;
                const handTileCount = actualTilesCount > 0 ? actualTilesCount : (hand.tile_count || 0);
                
                console.log(`🎮 玩家${playerId}手牌计算:`, {
                  actualTilesCount,
                  tile_count: hand.tile_count,
                  handTileCount,
                  tiles_is_array: Array.isArray(hand.tiles),
                  tiles_length: hand.tiles?.length
                });
                
                if (handTileCount > 0) {
                  return (
                    <div style={{ display: 'flex' }}>
                      {/* 玩家0（我）或牌局结束时或设置显示所有手牌时：显示具体牌面 */}
                      {(() => {
                        const shouldShowTiles = (playerId === 0 || gameState.game_ended || gameState.show_all_hands);
                        const hasTiles = hand.tiles && Array.isArray(hand.tiles) && hand.tiles.length > 0;
                        console.log(`🔍🔍🔍 玩家${playerId}显示判断 🔍🔍🔍`, { 
                          shouldShowTiles, 
                          hasTiles, 
                          show_all_hands: gameState.show_all_hands,
                          game_ended: gameState.game_ended,
                          tiles_count: hand.tiles?.length,
                          tiles_data: hand.tiles ? hand.tiles.slice(0, 3) : 'null'
                        });
                        console.warn(`⚠️⚠️⚠️ 玩家${playerId}条件检查 ⚠️⚠️⚠️`, {
                          playerId,
                          'hand.tiles存在': !!hand.tiles,
                          'hand.tiles是数组': Array.isArray(hand.tiles),
                          'hand.tiles长度': hand.tiles?.length || 0,
                          '强制显示条件': playerId !== 0 && hand.tiles && hand.tiles.length > 0
                        });
                        
                        // 🔧 强化显示逻辑：多重条件确保显示
                        if (playerId !== 0) {
                          // 条件1：有实际手牌数据就显示
                          if (hand.tiles && hand.tiles.length > 0) {
                            console.log(`🎯 条件1满足：玩家${playerId}有手牌数据，强制显示`);
                            return true;
                          }
                          // 条件2：如果有tile_count但没有tiles，可能是数据同步问题
                          if (hand.tile_count > 0) {
                            console.log(`⚠️ 玩家${playerId}有tile_count(${hand.tile_count})但没有tiles数据`);
                          }
                        }
                        
                        const finalResult = shouldShowTiles && hasTiles;
                        console.error(`🚨🚨🚨 玩家${playerId}最终显示决定 🚨🚨🚨`, {
                          finalResult,
                          shouldShowTiles,
                          hasTiles,
                          将显示: finalResult ? '具体牌面' : '背面牌'
                        });
                        return finalResult;
                      })() ? (
                        hand.tiles && Array.isArray(hand.tiles) ? hand.tiles.map((tile: Tile, index: number) => {
                          const isDragging = draggedIndex === index && playerId === 0;
                          const isDragOver = dragOverIndex === index && playerId === 0;
                          
                          // 检查是否是胡牌
                          const isWinTile = hand.is_winner && hand.win_tile && 
                            tile.type === hand.win_tile.type && 
                            tile.value === hand.win_tile.value;
                          
                          return (
                            <div
                              key={`player-${playerId}-hand-${index}`}
                              draggable={playerId === 0 && !gameState.game_ended} // 只有"我"的手牌且游戏未结束时可以拖拽
                              onDragStart={playerId === 0 ? (e) => handleDragStart(e, index, playerId) : undefined}
                              onDragOver={playerId === 0 ? (e) => handleDragOver(e, index, playerId) : undefined}
                              onDragEnter={playerId === 0 ? (e) => handleDragEnter(e, index, playerId) : undefined}
                              onDragLeave={playerId === 0 ? handleDragLeave : undefined}
                              onDrop={playerId === 0 ? (e) => handleDrop(e, index, playerId) : undefined}
                              onDragEnd={playerId === 0 ? handleDragEnd : undefined}
                              onDoubleClick={playerId === 0 && !gameState.game_ended ? () => handleTileDoubleClick(tile, index, playerId) : undefined} // 只有"我"的手牌且游戏未结束时可以双击
                              className={`relative transition-all duration-200 ${
                                playerId === 0 && !gameState.game_ended ? 'cursor-grab active:cursor-grabbing hover:cursor-pointer' : 'cursor-default'
                              } ${
                                isDragging ? 'opacity-50 scale-105' : ''
                              } ${
                                isDragOver ? 'transform scale-110' : ''
                              } ${
                                gameState.game_ended && playerId !== 0 ? 'opacity-90' : ''
                              }`}
                              style={{
                                transform: isDragOver ? 'translateY(-4px)' : 'none',
                                filter: isDragging ? 'brightness(1.1)' : 'none',
                                ...(isWinTile ? {
                                  backgroundColor: hand.win_type === 'zimo' ? 'rgba(255, 215, 0, 0.3)' : 'rgba(255, 69, 58, 0.3)', 
                                  padding: '2px', 
                                  borderRadius: '6px', 
                                  border: hand.win_type === 'zimo' ? '2px solid gold' : '2px solid #ff453a',
                                  boxShadow: hand.win_type === 'zimo' ? '0 0 8px rgba(255, 215, 0, 0.5)' : '0 0 8px rgba(255, 69, 58, 0.5)'
                                } : {})
                              }}
                              title={
                                gameState.game_ended 
                                  ? `玩家${playerNames[playerId]}的最终手牌` 
                                  : gameState.show_all_hands && playerId !== 0
                                    ? `玩家${playerNames[playerId]}的手牌（已显示）`
                                  : playerId === 0 
                                    ? "拖拽重排 | 双击弃牌"
                                    : `玩家${playerNames[playerId]}的手牌`
                              }
                            >
                              <motion.div
                                className="relative"
                                animate={isWinTile ? { 
                                  scale: [1, 1.05, 1],
                                  rotateY: [0, 5, 0]
                                } : {}}
                                transition={isWinTile ? { 
                                  duration: 2,
                                  repeat: Infinity,
                                  ease: "easeInOut"
                                } : {}}
                              >
                                <MahjongTile
                                  tile={tile}
                                  size="small"
                                  variant="default"
                                  seamless={true}
                                  cardBackStyle={cardBackStyle}
                                />
                                
                                {/* 胡牌类型指示器 */}
                                {isWinTile && (
                                  <motion.div 
                                    className={`absolute -top-2 -left-2 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center shadow-lg ${
                                      hand.win_type === 'zimo' ? 'bg-gradient-to-br from-yellow-400 to-yellow-600' : 'bg-gradient-to-br from-red-500 to-red-700'
                                    }`}
                                    animate={{ 
                                      rotate: [0, 360],
                                      scale: [1, 1.1, 1]
                                    }}
                                    transition={{ 
                                      duration: 3,
                                      repeat: Infinity,
                                      ease: "linear"
                                    }}
                                  >
                                    {hand.win_type === 'zimo' ? '自' : '胡'}
                                  </motion.div>
                                )}
                                
                                {/* 点炮者指示器 */}
                                {isWinTile && hand.win_type === 'dianpao' && hand.dianpao_player_id !== undefined && (
                                  <motion.div 
                                    className="absolute -top-1 -right-1 bg-gradient-to-br from-orange-500 to-orange-700 text-white text-xs font-bold rounded-full w-4 h-4 flex items-center justify-center shadow-sm"
                                    animate={{ 
                                      scale: [1, 1.2, 1],
                                      opacity: [0.8, 1, 0.8]
                                    }}
                                    transition={{ 
                                      duration: 1.5,
                                      repeat: Infinity,
                                      ease: "easeInOut"
                                    }}
                                  >
                                    {hand.dianpao_player_id === 0 ? '我' : 
                                     hand.dianpao_player_id === 1 ? '下' : 
                                     hand.dianpao_player_id === 2 ? '对' : '上'}
                                  </motion.div>
                                )}
                              </motion.div>
                            </div>
                          );
                        }) : (
                          <div className="text-red-500 text-sm">
                            ⚠️ 玩家{playerId}手牌数据格式错误: {typeof hand.tiles}
                          </div>
                        )
                      ) : (
                        /* 其他玩家：显示对应数量的背面牌 */
                        console.error(`🔒🔒🔒 玩家${playerId}显示背面牌 🔒🔒🔒`, { handTileCount }),
                        Array.from({ length: handTileCount }, (_, index) => (
                          <div
                            key={`player-${playerId}-back-${index}`}
                            className="transition-all duration-200"
                            title={`玩家${playerNames[playerId]}的手牌`}
                          >
                            <MahjongTile
                              tile={{ type: 'wan' as any, value: 1 }} // 虚拟牌，不会显示具体内容
                              size="small"
                              variant="back"
                              seamless={true}
                              cardBackStyle={cardBackStyle}
                            />
                          </div>
                        ))
                      )}
                    </div>
                  );
                }
                return null;
              })()}
                            
              {/* 碰牌杠牌区域 - 组间有小间隙(gap-2) */}
              {hand.melds.length > 0 && (
                <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                  {hand.melds.map((meld, index) => (
                    <div key={`meld-${index}`} className="relative" style={{ 
                      display: 'flex', 
                      alignItems: 'flex-end',
                      backgroundColor: 'rgba(255,255,255,0.8)', 
                      padding: '0px 2px', 
                      borderRadius: '1px', 
                      border: '0px solid rgba(0,0,0,0.1)' 
                    }}>
                      {meld.tiles.map((tile: Tile, tileIndex: number) => {
                        // 暗杠显示逻辑
                        let variant: 'default' | 'selected' | 'selectedHorizontal' | 'recommended' | 'disabled' | 'disabledHorizontal' | 'back' = 'default';
                        let additionalClassName = '';
                        
                        if (meld.type === MeldType.GANG && meld.gang_type === GangType.AN_GANG) {
                          if (playerId === 0) {
                            // 我的暗杠：所有4张牌都显示为disabled样式
                            variant = 'disabled';
                          } else {
                            // 其他玩家的暗杠：全部显示背面
                            variant = 'back';
                          }
                        } else if (meld.type === MeldType.GANG && meld.gang_type === GangType.JIA_GANG) {
                          // 加杠显示逻辑：所有4张都正常显示
                          variant = 'default';
                        } else if (meld.type === MeldType.GANG && meld.gang_type === GangType.MING_GANG) {
                          // 直杠显示逻辑：前3张正常显示，第4张使用横向选中样式
                          if (tileIndex === 3) {
                            variant = 'selected';
                          } else {
                            variant = 'default';
                          }
                        }
                        
                        return (
                          <div key={`meld-tile-${index}-${tileIndex}`} className="relative">
                            <MahjongTile
                              tile={tile}
                              size="small"
                              variant={variant}
                              seamless={true}
                              className={additionalClassName}
                              cardBackStyle={cardBackStyle}
                            />
                            
                            {/* 明杠来源指示器 - 只在第4张牌上显示 */}
                            {meld.type === MeldType.GANG && 
                             meld.gang_type === GangType.MING_GANG && 
                             tileIndex === 3 && 
                             meld.source_player !== undefined && (
                              <SimpleSourceIndicator
                                sourcePlayer={meld.source_player}
                                currentPlayer={playerId}
                                className="absolute -top-1 -right-1"
                              />
                            )}
                            
                            {/* 暗杠标识器 - 在第4张牌上显示"暗"字 */}
                            {meld.type === MeldType.GANG && 
                             meld.gang_type === GangType.AN_GANG && 
                             tileIndex === 3 && (
                              <div className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full w-4 h-4 flex items-center justify-center shadow-sm">
                                暗
                              </div>
                            )}
                            
                            {/* 加杠原碰牌来源指示器 - 在第3张牌上显示"上"字 */}
                            {meld.type === MeldType.GANG && 
                             meld.gang_type === GangType.JIA_GANG && 
                             tileIndex === 2 && 
                             meld.source_player !== undefined && (
                              <SimpleSourceIndicator
                                sourcePlayer={meld.source_player}
                                currentPlayer={playerId}
                                className="absolute -top-1 -right-1"
                              />
                            )}
                            
                            {/* 加杠标识器 - 在第4张牌上显示"加"字 */}
                            {meld.type === MeldType.GANG && 
                             meld.gang_type === GangType.JIA_GANG && 
                             tileIndex === 3 && (
                              <div className="absolute -top-1 -right-1 bg-orange-500 text-white text-xs font-bold rounded-full w-4 h-4 flex items-center justify-center shadow-sm">
                                加
                              </div>
                            )}
                            
                            {/* 碰牌来源指示器 - 只在第3张牌上显示 */}
                            {meld.type === MeldType.PENG && 
                             tileIndex === 2 && 
                             meld.source_player !== undefined && (
                              <SimpleSourceIndicator
                                sourcePlayer={meld.source_player}
                                currentPlayer={playerId}
                                className="absolute -top-1 -right-1"
                              />
                            )}
                          </div>
                        );
                      })}
                    </div>
                  ))}
                </div>
              )}

              
            </div>
          </div>

          {/* 弃牌 */}
          <div>
            {renderDiscardGroup(discards, `player-${playerId}`)}
          </div>
        </div>

      </div>
    );
  };

  return (
    <div className={`bg-gradient-to-br from-green-50 to-green-100 rounded-2xl p-2 ${className}`}>
      {/* 标题和统计信息 - 同一行显示 */}
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-2xl font-bold text-gray-800">血战到底</h2>
        <div className="flex flex-col items-end gap-1">
          <div className="flex items-center gap-4">
            {/* 未出牌数 */}
            <div className="flex items-center gap-2 bg-white rounded-full px-4 py-2 shadow-sm border">
              <span className="text-sm text-gray-600">未知牌数:</span>
              <motion.div
                animate={{ scale: [1, 1.05, 1] }}
                transition={{ duration: 3, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
                className="text-xl font-bold text-blue-600"
              >
                {unplayedTiles}
              </motion.div>
            </div>
            {/* 剩余牌数 */}
            <div className="flex items-center gap-2 bg-white rounded-full px-4 py-2 shadow-sm border">
              <span className="text-sm text-gray-600">剩余牌数:</span>
              <motion.div
                animate={{ scale: [1, 1.05, 1] }}
                transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                className="text-xl font-bold text-green-600"
              >
                {remainingTiles}
              </motion.div>
            </div>
          </div>
        </div>
      </div>

      {/* 玩家区域 - 三行布局 */}
      <div className="flex flex-col gap-4 w-fit">
        {/* 第一行：对家（居中） */}
        <div className="flex justify-center">
          <div>
            {renderPlayerArea(2)}
          </div>
        </div>
        
        {/* 第二行：上家和下家（左右分布）以及中间的剩余牌数 */}
        <div className="flex items-center justify-center gap-4">
          <div>
            {renderPlayerArea(3)}
          </div>
          {/* 中间剩余牌数显示区域 */}
          <div className="flex items-center justify-center bg-white rounded-lg p-2 shadow-md border border-gray-200 w-24 h-24 aspect-square">
            <motion.div
              animate={{ scale: [1, 1.05, 1] }}
              transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
              className="text-2xl font-bold text-green-600"
            >
              {remainingTiles}
            </motion.div>
          </div>
          <div>
            {renderPlayerArea(1)}
          </div>
        </div>
        
        {/* 第三行：我（居中） */}
        <div className="flex justify-center">
          <div>
            {renderPlayerArea(0)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MahjongTable;
