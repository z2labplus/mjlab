import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Tile, GameState, createTile, MeldType, GangType, TileType, Meld, calculateRemainingTilesByType, UltimateAnalysisResult } from '../types/mahjong';
import MahjongTable from './MahjongTable';
import MahjongTile, { TileSize } from './MahjongTile';
import ReplayImporter from './ReplayImporter';
import { MahjongAPI } from '../utils/api';
import classNames from 'classnames';

interface ReplayAction {
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

interface ReplayData {
  game_info: {
    game_id: string;
    start_time: string;
    end_time?: string;
    duration?: number;
    player_count: number;
    game_mode: string;
  };
  players: Array<{
    id: number;
    name: string;
    position: number;
    initial_hand: string[];
    missing_suit?: string;
    final_score: number;
    is_winner: boolean;
    statistics: {
      draw_count: number;
      discard_count: number;
      peng_count: number;
      gang_count: number;
    };
  }>;
  actions: ReplayAction[];
  metadata: any;
  final_hands?: {
    [key: string]: {
      hand: string[];
      melds: Array<{
        type: string;
        tile: string[];
        target_player?: number;
      }>;
      self_win_tile?: {
        tile: string;
      };
      pao_tile?: {
        tile: string;
        target_player: number;
      };
    };
  };
}

// 创建默认的游戏状态（独立于实时游戏状态）
const createDefaultReplayGameState = (): GameState => ({
  game_id: 'replay',
  player_hands: {
    '0': { tiles: [], tile_count: 0, melds: [] },
    '1': { tiles: [], tile_count: 0, melds: [] },
    '2': { tiles: [], tile_count: 0, melds: [] },
    '3': { tiles: [], tile_count: 0, melds: [] }
  },
  player_discarded_tiles: {
    '0': [], '1': [], '2': [], '3': []
  },
  discarded_tiles: [],
  actions_history: [],
  current_player: 0,
  game_started: false,
  game_ended: false,
  show_all_hands: false
});

const ReplaySystem: React.FC = () => {
  // 使用独立的本地状态，不依赖于实时游戏的WebSocket store
  const [replayGameState, setReplayGameState] = useState<GameState>(createDefaultReplayGameState);
  
  const [replayData, setReplayData] = useState<ReplayData | null>(null);
  const [currentStep, setCurrentStep] = useState(-1); // -1 表示初始状态
  const [isPlaying, setIsPlaying] = useState(false);
  const [playSpeed, setPlaySpeed] = useState(1000);
  const [showImporter, setShowImporter] = useState(true);
  const [actionHistory, setActionHistory] = useState<string[]>([]);

  // 生成所有麻将牌用于显示
  const allMahjongTiles = useMemo(() => {
    const tiles: Tile[] = [];
    // 万、条、筒，每种花色1-9各4张
    [TileType.WAN, TileType.TIAO, TileType.TONG].forEach(suit => {
      for (let value = 1; value <= 9; value++) {
        for (let count = 0; count < 4; count++) {
          tiles.push(createTile(suit, value));
        }
      }
    });
    return tiles;
  }, []);

  // 获取牌的剩余数量（用于显示）
  const getTileRemainingCount = useCallback((tile: Tile): number => {
    if (!replayGameState) return 4;
    
    let usedCount = 0;
    
    // 统计所有玩家手牌中的使用数量
    Object.values(replayGameState.player_hands).forEach(hand => {
      if (hand.tiles) {
        usedCount += hand.tiles.filter(t => 
          t.type === tile.type && t.value === tile.value
        ).length;
      }
      
      // 统计明牌中的使用数量
      hand.melds.forEach(meld => {
        usedCount += meld.tiles.filter(t => 
          t.type === tile.type && t.value === tile.value
        ).length;
      });
    });
    
    // 统计弃牌中的使用数量
    if (replayGameState.discarded_tiles) {
      usedCount += replayGameState.discarded_tiles.filter(t => 
        t.type === tile.type && t.value === tile.value
      ).length;
    }
    
    return Math.max(0, 4 - usedCount);
  }, [replayGameState]);

  // 获取去重的麻将牌（用于显示）
  const uniqueTiles = useMemo(() => {
    const seen = new Set<string>();
    return allMahjongTiles.filter(tile => {
      const key = `${tile.type}-${tile.value}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, [allMahjongTiles]);

  // 解析牌的字符串格式 (如 "1万", "5条")
  const parseCardString = useCallback((cardStr: string): Tile | null => {
    if (!cardStr || cardStr.length < 2) return null;
    
    const value = parseInt(cardStr[0]);
    const suitChar = cardStr.slice(1);
    
    let suit: TileType;
    switch (suitChar) {
      case '万': suit = TileType.WAN; break;
      case '条': suit = TileType.TIAO; break;
      case '筒': suit = TileType.TONG; break;
      default: return null;
    }
    
    if (value >= 1 && value <= 9) {
      return createTile(suit, value);
    }
    
    return null;
  }, []);

  // 构建初始游戏状态
  const buildInitialGameState = useCallback((data: ReplayData): GameState => {
    const newGameState: GameState = {
      game_id: data.game_info.game_id,
      player_hands: {},
      player_discarded_tiles: { '0': [], '1': [], '2': [], '3': [] },
      discarded_tiles: [],
      actions_history: [],
      current_player: 0,
      game_started: true
    };

    // 初始化玩家手牌
    data.players.forEach((player) => {
      const playerId = player.position.toString();
      const initialTiles = player.initial_hand
        .map(cardStr => parseCardString(cardStr))
        .filter(tile => tile !== null) as Tile[];

      newGameState.player_hands[playerId] = {
        tiles: player.position === 0 ? initialTiles : null, // 只显示自己的手牌
        tile_count: initialTiles.length,
        melds: [],
        missing_suit: player.missing_suit || null
      };
    });

    return newGameState;
  }, [parseCardString]);

  // 应用单个操作到游戏状态
  const applyAction = useCallback((state: GameState, action: ReplayAction, actionIndex?: number, allActions?: ReplayAction[]): GameState => {
    const newState = JSON.parse(JSON.stringify(state)); // 深拷贝
    const playerIdStr = action.player_id.toString();
    
    // 解析操作中的牌
    const actionTile = action.card ? parseCardString(action.card) : null;
    
    switch (action.action_type) {
      case 'draw':
        // 摸牌
        if (actionTile) {
          if (action.player_id === 0) {
            // 玩家0的手牌可见
            newState.player_hands[playerIdStr].tiles?.push(actionTile);
          } else {
            // 其他玩家只增加牌数
            newState.player_hands[playerIdStr].tile_count += 1;
          }
        }
        break;

      case 'discard':
        // 弃牌
        if (actionTile) {
          // 添加到弃牌区
          newState.player_discarded_tiles[playerIdStr].push(actionTile);
          newState.discarded_tiles.push(actionTile);
          
          // 判断是否需要减少手牌数量
          let shouldReduceHandTiles = action.player_id === 0; // 玩家0总是减少手牌
          
          // 检查该玩家的前一个操作是否是碰牌/杠牌
          if (!shouldReduceHandTiles && actionIndex !== undefined && allActions) {
            // 从当前位置往前找该玩家的最后一个操作
            for (let i = actionIndex - 1; i >= 0; i--) {
              if (allActions[i].player_id === action.player_id) {
                const lastAction = allActions[i].action_type;
                if (lastAction === 'peng' || lastAction === 'gang' || lastAction === 'jiagang') {
                  shouldReduceHandTiles = true;
                }
                break; // 找到该玩家的最后一个操作就停止
              }
            }
          }
          
          if (shouldReduceHandTiles) {
            if (action.player_id === 0 && newState.player_hands[playerIdStr].tiles) {
              // 玩家0有具体牌面，从具体牌中移除
              const tiles = newState.player_hands[playerIdStr].tiles!;
              const index = tiles.findIndex((t: Tile) => t.type === actionTile.type && t.value === actionTile.value);
              if (index !== -1) {
                tiles.splice(index, 1);
              }
            }
            // 减少手牌数量
            newState.player_hands[playerIdStr].tile_count -= 1;
            console.log(`🎯 牌谱回放：玩家${action.player_id} 弃牌 ${actionTile.value}${actionTile.type}，减少手牌数量，剩余：${newState.player_hands[playerIdStr].tile_count}`);
          } else {
            console.log(`🎯 牌谱回放：玩家${action.player_id} 弃牌 ${actionTile.value}${actionTile.type}，不减少手牌数量（假设弃刚摸到的牌），手牌数量：${newState.player_hands[playerIdStr].tile_count}`);
          }
        }
        break;

      case 'peng':
        // 碰牌
        if (actionTile && action.target_player !== undefined && action.target_player !== null) {
          const meld = {
            type: MeldType.PENG,
            tiles: [actionTile, actionTile, actionTile],
            exposed: true,
            source_player: action.target_player
          };
          newState.player_hands[playerIdStr].melds.push(meld);
          
          // 🔧 修复：从被碰玩家的弃牌区移除被碰的牌
          const targetPlayerIdStr = action.target_player.toString();
          const targetPlayerDiscards = newState.player_discarded_tiles[targetPlayerIdStr];
          
          // 确保弃牌区存在
          if (targetPlayerDiscards) {
            // 从目标玩家的弃牌区中移除最后一张相同的牌（通常是最新弃出的）
            for (let i = targetPlayerDiscards.length - 1; i >= 0; i--) {
              const discardedTile = targetPlayerDiscards[i];
              if (discardedTile && discardedTile.type === actionTile.type && discardedTile.value === actionTile.value) {
                targetPlayerDiscards.splice(i, 1);
                console.log(`🗑️ 重放：从玩家${action.target_player}弃牌区移除被碰的 ${actionTile.value}${actionTile.type}`);
                break;
              }
            }
          }
          
          // 同时从全局弃牌区中移除被碰的牌
          const globalDiscards = newState.discarded_tiles;
          if (globalDiscards) {
            for (let i = globalDiscards.length - 1; i >= 0; i--) {
              const globalTile = globalDiscards[i];
              if (globalTile && globalTile.type === actionTile.type && globalTile.value === actionTile.value) {
                globalDiscards.splice(i, 1);
                console.log(`🌍 重放：从全局弃牌区移除被碰的 ${actionTile.value}${actionTile.type}`);
                break;
              }
            }
          }
          
          // 减少手牌数量
          if (action.player_id === 0) {
            // 玩家0减少2张（第3张是碰来的）
            const tiles = newState.player_hands[playerIdStr].tiles!;
            for (let i = 0; i < 2; i++) {
              const index = tiles.findIndex((t: Tile) => t.type === actionTile.type && t.value === actionTile.value);
              if (index !== -1) tiles.splice(index, 1);
            }
          } else {
            newState.player_hands[playerIdStr].tile_count -= 2;
          }
        }
        break;

      case 'gang':
      case 'jiagang':
        // 杠牌
        if (actionTile) {
          if (action.action_type === 'jiagang') {
            // 加杠：在已有的碰牌基础上添加第4张牌
            const melds = newState.player_hands[playerIdStr].melds;
            console.log(`🔍 加杠调试：玩家${action.player_id} 尝试加杠 ${actionTile.value}${actionTile.type}`);
            console.log(`🔍 当前碰杠牌组：`, melds.map((m: Meld) => ({
              type: m.type,
              tiles: m.tiles.map((t: Tile) => `${t.value}${t.type}`),
              source_player: m.source_player
            })));
            
            const pengIndex = melds.findIndex((meld: Meld) => 
              meld.type === MeldType.PENG && 
              meld.tiles[0].type === actionTile.type && 
              meld.tiles[0].value === actionTile.value
            );
            
            console.log(`🔍 查找碰牌结果：pengIndex = ${pengIndex}`);
            
            if (pengIndex !== -1) {
              // 找到对应的碰牌，将其转换为加杠
              const originalPeng = melds[pengIndex];
              console.log(`✅ 找到原始碰牌：`, {
                type: originalPeng.type,
                tiles: originalPeng.tiles.map((t: Tile) => `${t.value}${t.type}`),
                source_player: originalPeng.source_player
              });
              
              const jiaGangMeld = {
                type: MeldType.GANG,
                tiles: [actionTile, actionTile, actionTile, actionTile],
                exposed: true,
                gang_type: GangType.JIA_GANG,
                source_player: originalPeng.source_player, // 保留原来碰牌的来源
                original_meld_type: MeldType.PENG // 记录原来是碰牌
              };
              
              console.log(`🔧 创建加杠牌组：`, {
                type: jiaGangMeld.type,
                gang_type: jiaGangMeld.gang_type,
                source_player: jiaGangMeld.source_player,
                tiles: jiaGangMeld.tiles.map((t: Tile) => `${t.value}${t.type}`)
              });
              
              // 🐛 临时修复：如果原始碰牌的source_player为undefined，尝试从历史记录查找
              if (jiaGangMeld.source_player === undefined) {
                console.warn(`⚠️ 原始碰牌的source_player为undefined，尝试从历史记录查找`);
                if (allActions && actionIndex !== undefined) {
                  for (let i = actionIndex - 1; i >= 0; i--) {
                    const pastAction = allActions[i];
                    if (pastAction.player_id === action.player_id && 
                        pastAction.action_type === 'peng' && 
                        pastAction.card === action.card) {
                      jiaGangMeld.source_player = pastAction.target_player;
                      console.log(`🔍 从历史记录中找到原始碰牌来源：玩家${pastAction.target_player}`);
                      break;
                    }
                  }
                }
              }
              
              // 替换碰牌为加杠
              melds[pengIndex] = jiaGangMeld;
              console.log(`🔧 重放：玩家${action.player_id} 加杠 ${actionTile.value}${actionTile.type}，最终来源：玩家${jiaGangMeld.source_player}`);
            } else {
              console.warn(`⚠️ 找不到对应的碰牌来进行加杠: ${actionTile.value}${actionTile.type}，这可能是数据问题`);
              // 如果找不到对应的碰牌，说明数据有问题，但仍要创建加杠牌组
              // 对于加杠，target_player通常是undefined，所以我们不应该使用它作为source_player
              // 此时应该尝试从历史操作中找到原始碰牌的来源
              let originalSource = undefined;
              
              // 尝试从历史记录中找到原始碰牌操作的来源
              if (allActions && actionIndex !== undefined) {
                for (let i = actionIndex - 1; i >= 0; i--) {
                  const pastAction = allActions[i];
                  if (pastAction.player_id === action.player_id && 
                      pastAction.action_type === 'peng' && 
                      pastAction.card === action.card) {
                    originalSource = pastAction.target_player;
                    console.log(`🔍 从历史记录中找到原始碰牌来源：玩家${originalSource}`);
                    break;
                  }
                }
              }
              
              const meld = {
                type: MeldType.GANG,
                tiles: [actionTile, actionTile, actionTile, actionTile],
                exposed: true,
                gang_type: GangType.JIA_GANG,
                source_player: originalSource // 使用从历史记录中找到的来源，如果找不到就是undefined
              };
              newState.player_hands[playerIdStr].melds.push(meld);
            }
          } else {
            // 普通杠牌（明杠、暗杠）
            const meld = {
              type: MeldType.GANG,
              tiles: [actionTile, actionTile, actionTile, actionTile],
              exposed: action.gang_type !== 'an_gang',
              gang_type: action.gang_type === 'an_gang' ? GangType.AN_GANG : 
                         action.gang_type === 'jia_gang' ? GangType.JIA_GANG : GangType.MING_GANG,
              source_player: action.target_player
            };
            newState.player_hands[playerIdStr].melds.push(meld);
          }
          
          // 🔧 修复：对于明杠，从被杠玩家的弃牌区移除被杠的牌
          if (action.gang_type === 'ming_gang' && action.target_player !== undefined && action.target_player !== null) {
            const targetPlayerIdStr = action.target_player.toString();
            const targetPlayerDiscards = newState.player_discarded_tiles[targetPlayerIdStr];
            
            // 确保弃牌区存在
            if (targetPlayerDiscards) {
              // 从目标玩家的弃牌区中移除最后一张相同的牌
              for (let i = targetPlayerDiscards.length - 1; i >= 0; i--) {
                const discardedTile = targetPlayerDiscards[i];
                if (discardedTile && discardedTile.type === actionTile.type && discardedTile.value === actionTile.value) {
                  targetPlayerDiscards.splice(i, 1);
                  console.log(`🗑️ 重放：从玩家${action.target_player}弃牌区移除被明杠的 ${actionTile.value}${actionTile.type}`);
                  break;
                }
              }
            }
            
            // 同时从全局弃牌区中移除被杠的牌
            const globalDiscards = newState.discarded_tiles;
            if (globalDiscards) {
              for (let i = globalDiscards.length - 1; i >= 0; i--) {
                const globalTile = globalDiscards[i];
                if (globalTile && globalTile.type === actionTile.type && globalTile.value === actionTile.value) {
                  globalDiscards.splice(i, 1);
                  console.log(`🌍 重放：从全局弃牌区移除被明杠的 ${actionTile.value}${actionTile.type}`);
                  break;
                }
              }
            }
          }
          
          // 减少手牌数量
          const reduceCount = action.gang_type === 'an_gang' ? 4 : 
                            action.gang_type === 'jia_gang' ? 1 : 3;
          
          if (action.player_id === 0) {
            const tiles = newState.player_hands[playerIdStr].tiles!;
            for (let i = 0; i < reduceCount; i++) {
              const index = tiles.findIndex((t: Tile) => t.type === actionTile.type && t.value === actionTile.value);
              if (index !== -1) tiles.splice(index, 1);
            }
          } else {
            newState.player_hands[playerIdStr].tile_count -= reduceCount;
          }
        }
        break;

      case 'missing_suit':
        // 定缺
        if (action.missing_suit) {
          newState.player_hands[playerIdStr].missing_suit = action.missing_suit;
        }
        break;

      case 'zimo':
        // 自摸胡牌
        newState.player_hands[playerIdStr].is_winner = true;
        newState.player_hands[playerIdStr].win_type = 'zimo';
        if (actionTile) {
          newState.player_hands[playerIdStr].win_tile = actionTile;
          
          // 将胜利牌加入到手牌中（自摸需要将摸到的牌加入手牌）
          if (action.player_id === 0) {
            const tiles = newState.player_hands[playerIdStr].tiles!;
            tiles.push(actionTile);
          } else {
            newState.player_hands[playerIdStr].tile_count += 1;
          }
          
          console.log(`🎉 自摸胡牌：玩家${action.player_id} 自摸 ${actionTile.value}${actionTile.type}`);
        }
        break;

      case 'hu':
        // 胡牌
        newState.player_hands[playerIdStr].is_winner = true;
        if (actionTile) {
          newState.player_hands[playerIdStr].win_tile = actionTile;
          
          // 判断是自摸还是点炮
          if (action.target_player !== undefined && action.target_player !== null) {
            // 点炮胡牌
            newState.player_hands[playerIdStr].win_type = 'dianpao';
            newState.player_hands[playerIdStr].dianpao_player_id = action.target_player;
            
            // 将胜利牌加入到胜利者的手牌中（点炮胡牌也需要将胜利牌加入手牌）
            if (action.player_id === 0) {
              const tiles = newState.player_hands[playerIdStr].tiles!;
              tiles.push(actionTile);
            } else {
              newState.player_hands[playerIdStr].tile_count += 1;
            }
            
            // 从点炮者的弃牌区移除被胡的牌
            const targetPlayerIdStr = action.target_player.toString();
            const targetPlayerDiscards = newState.player_discarded_tiles[targetPlayerIdStr];
            
            if (targetPlayerDiscards) {
              // 从弃牌区移除最后一张相同的牌
              for (let i = targetPlayerDiscards.length - 1; i >= 0; i--) {
                const discardedTile = targetPlayerDiscards[i];
                if (discardedTile && discardedTile.type === actionTile.type && discardedTile.value === actionTile.value) {
                  targetPlayerDiscards.splice(i, 1);
                  console.log(`🎯 胡牌：从玩家${action.target_player}弃牌区移除被胡的 ${actionTile.value}${actionTile.type}`);
                  break;
                }
              }
            }
            
            // 同时从全局弃牌区移除
            const globalDiscards = newState.discarded_tiles;
            if (globalDiscards) {
              for (let i = globalDiscards.length - 1; i >= 0; i--) {
                const globalTile = globalDiscards[i];
                if (globalTile && globalTile.type === actionTile.type && globalTile.value === actionTile.value) {
                  globalDiscards.splice(i, 1);
                  console.log(`🌍 胡牌：从全局弃牌区移除被胡的 ${actionTile.value}${actionTile.type}`);
                  break;
                }
              }
            }
          } else {
            // 自摸胡牌
            newState.player_hands[playerIdStr].win_type = 'zimo';
            
            // 将胜利牌加入到手牌中（自摸需要将摸到的牌加入手牌）
            if (action.player_id === 0) {
              const tiles = newState.player_hands[playerIdStr].tiles!;
              tiles.push(actionTile);
            } else {
              newState.player_hands[playerIdStr].tile_count += 1;
            }
            
            console.log(`🎉 自摸胡牌：玩家${action.player_id} 自摸 ${actionTile.value}${actionTile.type}`);
          }
        }
        break;
    }

    // 当前玩家就是执行操作的玩家
    newState.current_player = action.player_id;

    return newState;
  }, [parseCardString]);

  // 计算指定步骤的游戏状态
  const getStateAtStep = useMemo(() => {
    if (!replayData) return null;
    
    let state = buildInitialGameState(replayData);
    
    // 应用到当前步骤为止的所有操作
    for (let i = 0; i <= currentStep; i++) {
      if (i < replayData.actions.length) {
        state = applyAction(state, replayData.actions[i], i, replayData.actions);
      }
    }
    
    // 检查牌局是否结束，如果是最后一步且有final_hands数据，显示所有玩家手牌
    const isGameEnd = currentStep >= replayData.actions.length - 1;
    if (isGameEnd && replayData.final_hands) {
      console.log('🎉 牌局结束，显示所有玩家手牌');
      state.game_ended = true;
      
      // 为所有玩家设置最终手牌
      Object.entries(replayData.final_hands).forEach(([playerIdStr, finalHand]) => {
        if (state.player_hands[playerIdStr]) {
          // 解析最终手牌
          const finalTiles = finalHand.hand
            .map(cardStr => parseCardString(cardStr))
            .filter(tile => tile !== null) as Tile[];
          
          // 处理胡牌信息并将胜利牌加入手牌
          let winTile = null;
          if (finalHand.self_win_tile) {
            // 自摸胡牌
            winTile = parseCardString(finalHand.self_win_tile.tile);
            if (winTile) {
              state.player_hands[playerIdStr].is_winner = true;
              state.player_hands[playerIdStr].win_type = 'zimo';
              state.player_hands[playerIdStr].win_tile = winTile;
              finalTiles.push(winTile); // 将胜利牌加入最终手牌
              console.log(`🎉 玩家${playerIdStr} 自摸胡牌:`, winTile);
            }
          } else if (finalHand.pao_tile) {
            // 点炮胡牌
            winTile = parseCardString(finalHand.pao_tile.tile);
            if (winTile) {
              state.player_hands[playerIdStr].is_winner = true;
              state.player_hands[playerIdStr].win_type = 'dianpao';
              state.player_hands[playerIdStr].win_tile = winTile;
              state.player_hands[playerIdStr].dianpao_player_id = finalHand.pao_tile.target_player;
              finalTiles.push(winTile); // 将胜利牌加入最终手牌
              console.log(`🎉 玩家${playerIdStr} 胡了玩家${finalHand.pao_tile.target_player}的牌:`, winTile);
            }
          }
          
          // 设置手牌可见（包含胜利牌）
          state.player_hands[playerIdStr].tiles = finalTiles;
          state.player_hands[playerIdStr].tile_count = finalTiles.length;
          
          console.log(`👁️ 显示玩家${playerIdStr}的最终手牌:`, finalTiles.map(t => `${t.value}${t.type}`));
        }
      });
    }
    
    return state;
  }, [replayData, currentStep, buildInitialGameState, applyAction]);

  // 更新游戏状态
  useEffect(() => {
    const state = getStateAtStep;
    if (state) {
      setReplayGameState(state);
    }
  }, [getStateAtStep]);

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

  // 更新操作历史
  useEffect(() => {
    if (!replayData) return;
    
    const history = [];
    for (let i = 0; i <= currentStep; i++) {
      if (i < replayData.actions.length) {
        const action = replayData.actions[i];
        const playerName = replayData.players[action.player_id]?.name || `玩家${action.player_id}`;
        history.push(getActionDescription(action, playerName));
      }
    }
    setActionHistory(history);
  }, [replayData, currentStep]);

  const getActionDescription = (action: ReplayAction, playerName: string): string => {
    switch (action.action_type) {
      case 'draw': return `${playerName} 摸牌`;
      case 'discard': return `${playerName} 弃牌 ${action.card}`;
      case 'peng': return `${playerName} 碰牌 ${action.card}`;
      case 'gang': 
        const gangTypeMap = {
          'an_gang': '暗杠',
          'ming_gang': '明杠', 
          'jia_gang': '加杠'
        };
        return `${playerName} ${gangTypeMap[action.gang_type as keyof typeof gangTypeMap] || '杠'} ${action.card}`;
      case 'zimo': return `🎉 ${playerName} 自摸胡牌！`;
      case 'hu': return `🎉 ${playerName} 胡牌！`;
      case 'missing_suit': 
        const suitMap = { 'wan': '万', 'tiao': '条', 'tong': '筒' };
        return `${playerName} 定缺${suitMap[action.missing_suit as keyof typeof suitMap]}`;
      default: return `${playerName} ${action.action_type}`;
    }
  };

  // 牌谱分析功能 - 使用血战到底分析API
  const [currentAnalysis, setCurrentAnalysis] = useState<UltimateAnalysisResult[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  
  // 使用血战到底分析API
  const analyzeHandTiles = useCallback(async (hand: Tile[]): Promise<void> => {
    if (!replayGameState || !hand || hand.length === 0) {
      setCurrentAnalysis([]);
      return;
    }
    
    setIsAnalyzing(true);
    setAnalysisError(null);
    
    try {
      // 准备分析请求数据
      const handTiles = hand.map(tile => `${tile.value}${tile.type === TileType.WAN ? '万' : tile.type === TileType.TIAO ? '条' : '筒'}`);
      
      // 收集可见牌（弃牌等）
      const visibleTiles: string[] = [];
      if (replayGameState.discarded_tiles) {
        replayGameState.discarded_tiles.forEach(tile => {
          visibleTiles.push(`${tile.value}${tile.type === TileType.WAN ? '万' : tile.type === TileType.TIAO ? '条' : '筒'}`);
        });
      }
      
      // 获取定缺信息
      const missingSuit = replayGameState.player_hands?.['0']?.missing_suit || 'tong';  // 默认定缺筒
      const missingSuitChinese = missingSuit === 'wan' ? '万' : missingSuit === 'tiao' ? '条' : '筒';
      
      // 调用血战到底分析API
      console.log('🔍 牌谱分析调试 - 步骤', currentStep);
      console.log('手牌:', handTiles);
      console.log('可见牌:', visibleTiles);
      console.log('定缺:', missingSuitChinese);
      
      const response = await MahjongAPI.analyzeUltimate({
        hand_tiles: handTiles,
        visible_tiles: visibleTiles,
        missing_suit: missingSuitChinese
      });
      
      if (response.success && response.results) {
        // 按收益从高到低排序
        const sortedResults = response.results.sort((a, b) => b.expected_value - a.expected_value);
        console.log('🎯 分析结果:', sortedResults.slice(0, 3).map(r => ({
          discard: r.discard_tile,
          detail: r.jinzhang_detail,
          count: r.jinzhang_count
        })));
        setCurrentAnalysis(sortedResults);
      } else {
        console.log('❌ 分析失败:', response.message);
        setAnalysisError(response.message || '分析失败');
        setCurrentAnalysis([]);
      }
    } catch (err) {
      setAnalysisError(err instanceof Error ? err.message : '分析失败');
      setCurrentAnalysis([]);
    } finally {
      setIsAnalyzing(false);
    }
  }, [replayGameState]);
  

  // 触发分析当前玩家0的手牌
  useEffect(() => {
    if (replayGameState?.player_hands?.['0']?.tiles && replayGameState.player_hands['0'].tiles.length > 0) {
      const player0Hand = replayGameState.player_hands['0'].tiles;
      
      // 调试信息
      console.log('🎯 步骤', currentStep, '玩家0手牌:', player0Hand.map(t => `${t.value}${t.type}`).join(','));
      
      // 调用后端分析
      analyzeHandTiles(player0Hand);
    } else {
      setCurrentAnalysis([]);
    }
  }, [replayGameState?.player_hands?.['0']?.tiles, analyzeHandTiles, currentStep]);
  
  // 检查是否刚刚摸牌（用于触发分析）
  const isAfterDraw = useMemo(() => {
    if (!replayData || currentStep < 0) return false;
    
    const currentAction = replayData.actions[currentStep];
    return currentAction?.action_type === 'draw' && currentAction?.player_id === 0;
  }, [replayData, currentStep]);

  const handleImportReplay = useCallback((data: ReplayData) => {
    setReplayData(data);
    setCurrentStep(-1);
    setIsPlaying(false);
    setShowImporter(false);
    setActionHistory([]);
    
    // 设置初始状态
    const initialState = buildInitialGameState(data);
    setReplayGameState(initialState);
  }, [buildInitialGameState]);

  const handlePlayPause = useCallback(() => {
    setIsPlaying(prev => !prev);
  }, []);

  const handleStepForward = useCallback(() => {
    if (!replayData) return;
    setCurrentStep(prev => Math.min(prev + 1, replayData.actions.length - 1));
  }, [replayData]);

  const handleStepBackward = useCallback(() => {
    setCurrentStep(prev => Math.max(prev - 1, -1));
  }, []);

  const handleReset = useCallback(() => {
    setCurrentStep(-1);
    setIsPlaying(false);
  }, []);

  const handleClose = useCallback(() => {
    setReplayData(null);
    setShowImporter(true);
    setCurrentStep(-1);
    setIsPlaying(false);
    setActionHistory([]);
  }, []);

  if (showImporter || !replayData) {
    return (
      <div className="replay-system p-6 bg-white rounded-lg shadow-lg">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800">🎬 牌谱回放系统</h2>
          {replayData && (
            <button
              onClick={() => setShowImporter(false)}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              返回回放
            </button>
          )}
        </div>
        <ReplayImporter onImport={handleImportReplay} />
      </div>
    );
  }

  const currentAction = currentStep >= 0 ? replayData.actions[currentStep] : null;

  return (
    <div className="replay-system min-h-screen bg-gray-50">
      {/* 头部控制区 */}
      <div className="bg-white shadow-sm border-b p-4">
        <div className="max-w-full mx-auto px-4 sm:px-6">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h2 className="text-xl font-bold text-gray-800">
                🎬 {replayData.game_info.game_id}
              </h2>
              <p className="text-sm text-gray-600">
                {new Date(replayData.game_info.start_time).toLocaleString()}
                {replayData.game_info.duration && ` · ${Math.floor(replayData.game_info.duration / 60)}分钟`}
              </p>
            </div>
            
            <div className="flex gap-2">
              <button
                onClick={() => setShowImporter(true)}
                className="px-3 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 text-sm"
              >
                导入其他牌谱
              </button>
              <button
                onClick={handleClose}
                className="px-3 py-2 bg-red-500 text-white rounded hover:bg-red-600 text-sm"
              >
                关闭回放
              </button>
            </div>
          </div>

          {/* 播放控制 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleReset}
                className="px-4 py-2 bg-gradient-to-r from-gray-500 to-gray-600 text-white rounded-lg shadow-md hover:shadow-lg transition-all duration-200 font-medium"
              >
                🔄 重置
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleStepBackward}
                disabled={currentStep <= -1}
                className={classNames(
                  'px-4 py-2 rounded-lg shadow-md hover:shadow-lg transition-all duration-200 font-medium',
                  currentStep <= -1
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-gradient-to-r from-blue-500 to-blue-600 text-white'
                )}
              >
                ⏮️ 上一步
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handlePlayPause}
                className={classNames(
                  'px-6 py-2 rounded-lg shadow-md hover:shadow-lg transition-all duration-200 font-medium text-white',
                  isPlaying
                    ? 'bg-gradient-to-r from-red-500 to-red-600'
                    : 'bg-gradient-to-r from-green-500 to-green-600'
                )}
              >
                {isPlaying ? '⏸️ 暂停' : '▶️ 播放'}
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleStepForward}
                disabled={currentStep >= replayData.actions.length - 1}
                className={classNames(
                  'px-4 py-2 rounded-lg shadow-md hover:shadow-lg transition-all duration-200 font-medium',
                  currentStep >= replayData.actions.length - 1
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-gradient-to-r from-blue-500 to-blue-600 text-white'
                )}
              >
                下一步 ⏭️
              </motion.button>
            </div>

            <div className="flex items-center gap-4">
              <div className="px-3 py-1 bg-blue-50 text-blue-700 rounded-lg text-sm font-medium">
                步骤 {Math.max(0, currentStep + 1)} / {replayData.actions.length}
              </div>
              
              <select
                value={playSpeed}
                onChange={(e) => setPlaySpeed(Number(e.target.value))}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              >
                <option value={2000}>🐌 0.5x</option>
                <option value={1000}>🚶 1x</option>
                <option value={500}>🏃 2x</option>
                <option value={250}>🚀 4x</option>
              </select>
            </div>
          </div>

          {/* 进度条 */}
          <div className="mt-4">
            <div className="relative w-full bg-gradient-to-r from-gray-200 to-gray-300 rounded-full h-3 shadow-inner">
              <motion.div 
                className="bg-gradient-to-r from-blue-500 to-purple-600 h-3 rounded-full shadow-lg"
                style={{ 
                  width: `${((currentStep + 1) / replayData.actions.length) * 100}%` 
                }}
                animate={{
                  width: `${((currentStep + 1) / replayData.actions.length) * 100}%`
                }}
                transition={{ duration: 0.3, ease: "easeInOut" }}
              >
                <div className="h-full w-full bg-gradient-to-r from-white/20 to-transparent rounded-full"></div>
              </motion.div>
              
              {/* 进度条上的时间标记点 */}
              {replayData.actions.length > 0 && (
                <div className="absolute top-0 left-0 w-full h-full">
                  {[0, 0.25, 0.5, 0.75, 1].map((pos, index) => (
                    <div
                      key={index}
                      className="absolute top-0 w-0.5 h-3 bg-white/50 rounded-full"
                      style={{ left: `${pos * 100}%` }}
                    />
                  ))}
                </div>
              )}
            </div>
            
            <input
              type="range"
              min="-1"
              max={replayData.actions.length - 1}
              value={currentStep}
              onChange={(e) => setCurrentStep(Number(e.target.value))}
              className="w-full mt-2 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider-thumb"
              style={{
                background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${((currentStep + 1) / replayData.actions.length) * 100}%, #e5e7eb ${((currentStep + 1) / replayData.actions.length) * 100}%, #e5e7eb 100%)`
              }}
            />
          </div>
          
        </div>
      </div>

      {/* 主内容区 */}
      {/* <div className="max-w-7xl mx-auto p-4"> */}
      <div className="w-full mx-auto">


        <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
          {/* 麻将桌面 - 占3列 */}
          <div className="xl:col-span-3 space-y-4">
            <div className="bg-white rounded-lg shadow-lg p-4">
              <MahjongTable cardBackStyle="elegant" gameState={replayGameState} />
            </div>
            
            
            {/* 所有麻将牌显示区域 */}
            <div className="bg-white rounded-lg shadow-lg p-4">
              <div className="flex items-center gap-3 mb-3">
                <div className="text-base font-semibold text-gray-800">🀄 所有麻将牌</div>
                <div className="text-xs text-gray-500">剩余数量实时显示</div>
              </div>
              
              <div className="space-y-2">
                <div>
 
                  <div className="flex gap-0.5 flex-wrap">
                    {uniqueTiles
                      .filter(tile => tile.type === TileType.WAN)
                      .map((tile, index) => {
                        const remainingCount = getTileRemainingCount(tile);
                        return (
                          <div key={`wan-${tile.value}`} className="relative">
                            <MahjongTile
                              tile={tile}
                              size="tiny"
                              variant="default"
                              cardBackStyle="elegant"
                              remainingCount={remainingCount}
                              animationDelay={index * 0.01}
                            />
                          </div>
                        );
                      })}

                    {uniqueTiles
                      .filter(tile => tile.type === TileType.TIAO)
                      .map((tile, index) => {
                        const remainingCount = getTileRemainingCount(tile);
                        return (
                          <div key={`tiao-${tile.value}`} className="relative">
                            <MahjongTile
                              tile={tile}
                              size="tiny"
                              variant="default"
                              cardBackStyle="elegant"
                              remainingCount={remainingCount}
                              animationDelay={index * 0.01}
                            />
                          </div>
                        );
                      })}



                    {uniqueTiles
                      .filter(tile => tile.type === TileType.TONG)
                      .map((tile, index) => {
                        const remainingCount = getTileRemainingCount(tile);
                        return (
                          <div key={`tong-${tile.value}`} className="relative">
                            <MahjongTile
                              tile={tile}
                              size="tiny"
                              variant="default"
                              cardBackStyle="elegant"
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

          {/* 侧边栏 - 占1列 */}
          <div className="space-y-6">
            {/* 牌谱分析 */}
            <div className="bg-white rounded-lg shadow-lg p-3">
              <div className="flex items-center gap-2 mb-3">
                <h3 className="text-base font-semibold text-gray-800">🧠 牌谱分析</h3>
                <div className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded-full">
                  玩家0专用
                </div>
                {isAfterDraw && (
                  <motion.div
                    animate={{ scale: [1, 1.1, 1] }}
                    transition={{ duration: 0.6, repeat: Infinity }}
                    className="w-2 h-2 bg-green-500 rounded-full"
                  />
                )}
              </div>
              
              {/* 错误显示 */}
              {analysisError && (
                <div className="bg-red-100 border border-red-300 text-red-700 px-3 py-2 rounded mb-3 text-sm">
                  {analysisError}
                </div>
              )}
              
              {/* 加载状态 */}
              {isAnalyzing && (
                <div className="flex items-center justify-center py-8">
                  <div className="flex items-center gap-2 text-blue-600">
                    <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                    <span className="text-sm">分析中...</span>
                  </div>
                </div>
              )}
              
              {/* 分析结果 */}
              {!isAnalyzing && currentAnalysis.length > 0 ? (
                <div className="space-y-3">
                  {currentAnalysis.slice(0, 6).map((analysis, index) => {
                    // 转换牌名为Tile对象用于显示
                    const discardTile = {
                      type: analysis.discard_tile.includes('万') ? TileType.WAN : 
                            analysis.discard_tile.includes('条') ? TileType.TIAO : TileType.TONG,
                      value: parseInt(analysis.discard_tile[0])
                    };
                    
                    return (
                      <motion.div
                        key={`${analysis.discard_tile}-${index}`}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className={classNames(
                          'p-3 rounded-lg border-2 transition-all duration-300',
                          {
                            'border-green-400 bg-gradient-to-br from-green-50 to-green-100': index === 0,
                            'border-blue-300 bg-gradient-to-br from-blue-50 to-blue-100': index === 1,
                            'border-yellow-300 bg-gradient-to-br from-yellow-50 to-yellow-100': index === 2,
                            'border-gray-300 bg-gradient-to-br from-gray-50 to-gray-100': index > 2
                          }
                        )}
                      >
                        {/* 第一行：弃牌和基本信息 */}
                        <div className="flex items-center gap-2 mb-2">
                          <div className="flex items-center gap-1">
                            <MahjongTile
                              tile={discardTile}
                              size="tiny"
                              variant="default"
                              cardBackStyle="elegant"
                            />
                            <span className="text-sm font-bold text-gray-800">
                              {analysis.expected_value}-{analysis.jinzhang_types}种-{analysis.jinzhang_count}张 向听:{analysis.shanten}
                            </span>
                          </div>
                          {index === 0 && (
                            <span className="text-xs bg-green-500 text-white px-1 rounded">
                              推荐
                            </span>
                          )}
                        </div>
                        
                        {/* 第二行：进张麻将牌显示 */}
                        <div className="mt-1">
                          {analysis.jinzhang_detail ? (() => {
                            // 解析进张详细信息，提取牌和数量
                            const parseJinzhangDetail = (detail: string) => {
                              const regex = /(\d+[万条筒])（(\d+)）/g;
                              const tiles = [];
                              let match;
                              
                              while ((match = regex.exec(detail)) !== null) {
                                const tileStr = match[1]; // 如"2条"
                                const count = parseInt(match[2]); // 如"1"
                                
                                // 转换为Tile对象
                                const value = parseInt(tileStr[0]);
                                const type = tileStr.includes('万') ? TileType.WAN : 
                                            tileStr.includes('条') ? TileType.TIAO : TileType.TONG;
                                
                                tiles.push({
                                  tile: { type, value },
                                  count
                                });
                              }
                              return tiles;
                            };
                            
                            const jinzhangTiles = parseJinzhangDetail(analysis.jinzhang_detail);
                            
                            return jinzhangTiles.length > 0 ? (
                              <div className="flex flex-wrap gap-1">
                                {jinzhangTiles.map((item, tileIndex) => (
                                  <div key={`${item.tile.type}-${item.tile.value}-${tileIndex}`} className="relative">
                                    <MahjongTile
                                      tile={item.tile}
                                      size="tiny"
                                      variant="default"
                                      cardBackStyle="elegant"
                                    />
                                    {/* 右上角显示剩余数量 */}
                                    <div className="absolute -top-1 -right-1 bg-blue-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center font-bold">
                                      {item.count}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="text-xs text-gray-500 italic">
                                无进张
                              </div>
                            );
                          })() : (
                            <div className="text-xs text-gray-500 italic">
                              无进张
                            </div>
                          )}
                        </div>
                        
                      </motion.div>
                    );
                  })}
                </div>
              ) : !isAnalyzing && (
                <div className="text-center py-8">
                  <div className="text-4xl mb-2">🤔</div>
                  <div className="text-sm text-gray-500">
                    {replayGameState?.player_hands?.['0']?.tiles ? (
                      isAfterDraw ? '等待分析结果...' : '摸牌后开始分析'
                    ) : (
                      '等待手牌数据'
                    )}
                  </div>
                </div>
              )}
              
            </div>

            {/* 操作历史 */}
            <div className="bg-white rounded-lg shadow-lg p-3">
              <div className="flex items-center gap-2 mb-3">
                <h3 className="text-base font-semibold text-gray-800">📜 操作历史</h3>
                <div className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                  {actionHistory.length} 条记录
                </div>
              </div>
              
              <div className="max-h-64 overflow-y-auto space-y-1 custom-scrollbar">
                {actionHistory.slice(-15).reverse().map((action, index) => {
                  const isLatest = index === 0;
                  const actionIcons = {
                    '摸牌': '🀄',
                    '弃牌': '🗑️',
                    '碰牌': '💥',
                    '杠': '⚡',
                    '胡牌': '🎉',
                    '定缺': '🎯'
                  };
                  
                  // 提取操作类型
                  const actionType = Object.keys(actionIcons).find(type => action.includes(type));
                  const icon = actionType ? actionIcons[actionType as keyof typeof actionIcons] : '🎮';
                  
                  return (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: (actionHistory.slice(-15).length - 1 - index) * 0.05 }}
                      className={classNames(
                        'text-xs p-2 rounded-md border-l-3 transition-all duration-200',
                        {
                          'bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-400 text-blue-800 shadow-md': isLatest,
                          'bg-gray-50 border-gray-300 text-gray-600 hover:bg-gray-100': !isLatest
                        }
                      )}
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-sm">{icon}</span>
                        <span className={classNames('flex-1 text-xs', {
                          'font-medium': isLatest
                        })}>
                          {action}
                        </span>
                        {isLatest && (
                          <motion.div
                            animate={{ scale: [1, 1.2, 1] }}
                            transition={{ duration: 1, repeat: Infinity }}
                            className="w-2 h-2 bg-blue-500 rounded-full"
                          />
                        )}
                      </div>
                    </motion.div>
                  );
                })}
                
                {actionHistory.length === 0 && (
                  <div className="text-center py-8">
                    <div className="text-4xl mb-2">📝</div>
                    <div className="text-sm text-gray-500">暂无操作记录</div>
                    <div className="text-xs text-gray-400 mt-1">操作将在这里显示</div>
                  </div>
                )}
              </div>
              
            </div>

          </div>
        </div>
      </div>
    </div>
  );
};

export default ReplaySystem;