export enum TileType {
  WAN = "m",        // 万 - 统一使用m表示
  TIAO = "s",       // 条 - 统一使用s表示  
  TONG = "p",       // 筒 - 统一使用p表示
  ZI = "z"          // 字牌 - 统一使用z表示
}

// 保持兼容性的旧枚举（用于显示）
export enum TileTypeDisplay {
  WAN = "wan",      // 万
  TIAO = "tiao",    // 条
  TONG = "tong",    // 筒
  ZI = "zi"         // 字牌
}

export interface Tile {
  type: TileType;
  value: number;
  id?: string;      // 添加牌的唯一标识
}

export enum MeldType {
  PENG = "peng",    // 碰
  GANG = "gang",    // 杠
  CHI = "chi"       // 吃
}

export enum GangType {
  MING_GANG = "ming_gang",  // 明杠（直杠）
  AN_GANG = "an_gang",      // 暗杠
  JIA_GANG = "jia_gang"     // 加杠
}

export interface Meld {
  id?: string;      // 添加唯一标识
  type: MeldType;
  tiles: Tile[];
  exposed: boolean;
  gang_type?: GangType; // 杠牌类型（仅当type为GANG时有效）
  source_player?: number;        // 直杠时：被杠牌的来源玩家ID
  original_peng_id?: string;     // 加杠时：原碰牌的ID
  timestamp?: number;            // 操作时间戳
}

export interface HandTiles {
  tiles: Tile[] | null;  // 其他玩家为null，只有我（玩家0）有具体牌面
  tile_count: number;     // 手牌数量（必需字段）
  melds: Meld[];
  missing_suit?: string | null;  // 定缺花色：wan/tiao/tong
  is_winner?: boolean;    // 是否胜利
  win_type?: 'zimo' | 'dianpao';  // 胜利类型：自摸或点炮
  win_tile?: Tile;        // 胡牌牌
  dianpao_player_id?: number;  // 点炮者ID（仅点炮胡牌时有效）
}

export interface PlayerAction {
  player_id: number;
  action_type: string;
  tiles: Tile[];
  timestamp?: number;
}

export interface GameState {
  game_id: string;
  player_hands: {
    [key: string]: HandTiles;
  };
  current_player: number;
  discarded_tiles: Tile[];
  player_discarded_tiles: {
    [key: string]: Tile[];
  };
  actions_history: PlayerAction[];
  game_started: boolean;
  game_ended?: boolean;  // 牌局是否结束
  show_all_hands?: boolean;  // 是否显示所有玩家手牌
}

export interface AnalysisResult {
  recommended_discard?: Tile;
  discard_scores: { [key: string]: number };
  listen_tiles: Tile[];
  win_probability: number;
  remaining_tiles_count: { [key: number]: number };
  suggestions: string[];
  ultimate_results?: UltimateAnalysisResult[];  // 血战到底分析结果
}

// 血战到底分析结果接口
export interface UltimateAnalysisResult {
  discard_tile: string;
  expected_value: number;    // 收益
  jinzhang_types: number;    // 进张种类数
  jinzhang_count: number;    // 总进张数
  jinzhang_detail: string;   // 详细进张信息
  shanten: number;           // 向听数
  can_win: boolean;          // 是否可胡
  is_forced: boolean;        // 是否必出
  patterns: string[];        // 特殊牌型
}

export interface GameRequest {
  game_state: GameState;
  target_player: number;
}

export interface GameResponse {
  success: boolean;
  analysis?: AnalysisResult;
  message: string;
}

export interface TileInfo {
  code: number;
  type: string;
  value: number;
  display: string;
}

// 胜利者信息接口
export interface Winner {
  player_id: number;
  win_type: 'zimo' | 'dianpao';
  win_tile?: Tile;
  dianpao_player_id?: number;
}

// 输入模式枚举
export enum InputMode {
  ADD_TO_HAND = "add_to_hand",
  DISCARD = "discard", 
  PENG = "peng",
  MING_GANG = "ming_gang",
  AN_GANG = "an_gang"
}

// 工具函数
export const createTile = (type: TileType, value: number): Tile => ({
  type,
  value
});

export const tileToCode = (tile: Tile): number => {
  switch (tile.type) {
    case TileType.WAN:
      return tile.value;
    case TileType.TIAO:
      return tile.value + 10;
    case TileType.TONG:
      return tile.value + 20;
    case TileType.ZI:
      return tile.value + 30;
    default:
      throw new Error(`Invalid tile type: ${tile.type}`);
  }
};

export const codeToTile = (code: number): Tile => {
  if (1 <= code && code <= 9) {
    return { type: TileType.WAN, value: code };
  } else if (11 <= code && code <= 19) {
    return { type: TileType.TIAO, value: code - 10 };
  } else if (21 <= code && code <= 29) {
    return { type: TileType.TONG, value: code - 20 };
  } else if (31 <= code && code <= 37) {
    return { type: TileType.ZI, value: code - 30 };
  } else {
    throw new Error(`Invalid tile code: ${code}`);
  }
};

export const tileToString = (tile: Tile): string => {
  const typeMap = {
    [TileType.WAN]: "万",
    [TileType.TIAO]: "条", 
    [TileType.TONG]: "筒",
    [TileType.ZI]: ["", "东", "南", "西", "北", "中", "发", "白"][tile.value] || ""
  };
  
  if (tile.type === TileType.ZI) {
    return typeMap[tile.type];
  } else {
    return `${tile.value}${typeMap[tile.type]}`;
  }
};

// 转换为mps格式（用于后端API）
export const tileToMpsString = (tile: Tile): string => {
  return `${tile.value}${tile.type}`;
};

// 从mps格式转换为Tile对象
export const mpsStringToTile = (mpsStr: string): Tile => {
  if (mpsStr.length !== 2) {
    throw new Error(`Invalid mps string: ${mpsStr}`);
  }
  
  const value = parseInt(mpsStr[0]);
  const type = mpsStr[1] as TileType;
  
  if (!Object.values(TileType).includes(type)) {
    throw new Error(`Invalid tile type: ${type}`);
  }
  
  return { type, value };
};

// 转换手牌数组为mps字符串
export const tilesToMpsString = (tiles: Tile[]): string => {
  const grouped: { [key in TileType]?: number[] } = {};
  
  tiles.forEach(tile => {
    if (!grouped[tile.type]) {
      grouped[tile.type] = [];
    }
    grouped[tile.type]!.push(tile.value);
  });
  
  let result = "";
  
  // 按照 m, p, s, z 的顺序
  const order: TileType[] = [TileType.WAN, TileType.TONG, TileType.TIAO, TileType.ZI];
  
  order.forEach(type => {
    if (grouped[type]) {
      const sortedValues = grouped[type]!.sort((a, b) => a - b);
      result += sortedValues.join('') + type;
    }
  });
  
  return result;
};

export const tilesEqual = (tile1: Tile, tile2: Tile): boolean => {
  return tile1.type === tile2.type && tile1.value === tile2.value;
};

// 计算剩余牌数（原有逻辑：基于tile_count计算所有已使用的牌）
export const calculateRemainingTiles = (gameState: GameState): number => {
  const totalTiles = 108; // 标准麻将总牌数
  
  // 计算已使用的牌数
  let usedTiles = 0;
  
  // 计算所有玩家手牌数量
  Object.values(gameState.player_hands).forEach(hand => {
    // 使用tile_count字段，如果不存在则用tiles数组长度（向后兼容）
    const handTileCount = hand.tile_count !== undefined ? hand.tile_count : (hand.tiles?.length || 0);
    usedTiles += handTileCount;
    
    // 计算碰牌杠牌数量（所有碰杠都计算）
    hand.melds.forEach(meld => {
      usedTiles += meld.tiles.length;
    });
  });
  
  // 计算弃牌数量
  usedTiles += gameState.discarded_tiles.length;
  
  return Math.max(0, totalTiles - usedTiles);
};

// 计算基于可见牌的剩余牌数（用于未出牌数计算）
export const calculateVisibleRemainingTiles = (gameState: GameState): number => {
  const totalTiles = 108; // 标准麻将总牌数
  
  // 计算已使用的可见牌数
  let usedTiles = 0;
  
  // 计算所有玩家手牌数量
  Object.entries(gameState.player_hands).forEach(([playerIdStr, hand]) => {
    const playerId = parseInt(playerIdStr);
    
    // 计算手牌：游戏结束时所有玩家手牌可见，平时只有"我"的手牌可见
    if (playerId === 0 || gameState.game_ended) {
      const handTileCount = hand.tile_count !== undefined ? hand.tile_count : (hand.tiles?.length || 0);
      usedTiles += handTileCount;
    }
    
    // 计算碰牌杠牌数量
    hand.melds.forEach(meld => {
      if (meld.type === MeldType.GANG && meld.gang_type === GangType.AN_GANG) {
        // 暗杠：游戏结束时所有玩家暗杠可见，平时只有"我"的暗杠可见
        if (playerId === 0 || gameState.game_ended) {
          usedTiles += meld.tiles.length;
        }
      } else {
        // 明牌（碰牌、明杠）：所有玩家的都要计算
        usedTiles += meld.tiles.length;
      }
    });
  });
  
  // 计算弃牌数量 - 所有玩家的弃牌都是可见的
  usedTiles += gameState.discarded_tiles.length;
  
  return Math.max(0, totalTiles - usedTiles);
};

// 计算每种牌的剩余数量（基于可见牌）
export const calculateRemainingTilesByType = (gameState: GameState): { [key: string]: number } => {
  console.log('🔍 开始计算剩余牌数...');
  
  // 初始化每种牌的数量为4张
  const remainingCounts: { [key: string]: number } = {};
  
  // 万子 1-9
  for (let i = 1; i <= 9; i++) {
    remainingCounts[`${TileType.WAN}-${i}`] = 4;
  }
  
  // 条子 1-9  
  for (let i = 1; i <= 9; i++) {
    remainingCounts[`${TileType.TIAO}-${i}`] = 4;
  }
  
  // 筒子 1-9
  for (let i = 1; i <= 9; i++) {
    remainingCounts[`${TileType.TONG}-${i}`] = 4;
  }
  
  console.log('📦 初始牌数:', remainingCounts);
  
  // 收集所有已使用的可见牌
  const usedTiles: Tile[] = [];
  
  // 收集玩家的手牌和碰杠牌
  Object.entries(gameState.player_hands).forEach(([playerIdStr, hand]) => {
    const playerId = parseInt(playerIdStr);
    
    // 获取手牌数量，安全处理null的情况
    const handTileCount = hand.tile_count !== undefined ? hand.tile_count : (hand.tiles?.length || 0);
    const handTiles = hand.tiles || [];
    
    console.log(`🏠 处理玩家${playerId}:`, {
      手牌数量: handTileCount,
      碰杠数量: hand.melds.length,
      具体手牌: playerId === 0 ? handTiles.map(t => `${t.value}${t.type}`) : '(隐藏)'
    });
    
    // 收集手牌：游戏结束时所有玩家手牌可见，平时只有"我"的手牌可见
    if (handTiles.length > 0 && (playerId === 0 || gameState.game_ended)) {
      console.log(`👤 收集玩家${playerId}的手牌:`, handTiles.map(t => `${t.value}${t.type}`));
      usedTiles.push(...handTiles);
    }
    
    // 胜利牌现在已经包含在最终手牌中，不需要单独计算
    
    // 收集碰牌杠牌
    hand.melds.forEach((meld, meldIndex) => {
      console.log(`🎴 处理玩家${playerId}的第${meldIndex}个碰杠:`, {
        类型: meld.type,
        杠牌类型: meld.gang_type,
        是否明牌: meld.exposed,
        牌数量: meld.tiles.length,
        牌内容: meld.tiles.map(t => `${t.value}${t.type}`)
      });
      
      if (meld.type === MeldType.GANG && meld.gang_type === GangType.AN_GANG) {
        // 暗杠：游戏结束时所有玩家暗杠可见，平时只有"我"的暗杠可见
        if (playerId === 0 || gameState.game_ended) {
          console.log(`🔒 收集玩家${playerId}的暗杠牌`);
          usedTiles.push(...meld.tiles);
        } else {
          console.log(`🔒 跳过玩家${playerId}的暗杠牌（游戏未结束）`);
        }
      } else {
        // 明牌（碰牌、明杠）：所有玩家的都要收集
        console.log('👁️ 收集明牌:', meld.tiles.map(t => `${t.value}${t.type}`));
        usedTiles.push(...meld.tiles);
      }
    });
  });
  
  // 收集弃牌 - 所有玩家的弃牌都是可见的
  console.log('🗑️ 收集弃牌:', gameState.discarded_tiles.map(t => `${t.value}${t.type}`));
  usedTiles.push(...gameState.discarded_tiles);
  
  console.log('📊 所有已使用的牌:', usedTiles.map(t => `${t.value}${t.type}`));
  
  // 减去已使用的牌
  usedTiles.forEach(tile => {
    const key = `${tile.type}-${tile.value}`;
    console.log(`🔢 处理牌 ${tile.value}${tile.type}, key: ${key}, 当前剩余: ${remainingCounts[key]}`);
    if (remainingCounts[key] !== undefined) {
      remainingCounts[key] = Math.max(0, remainingCounts[key] - 1);
      console.log(`  ➡️ 减少后剩余: ${remainingCounts[key]}`);
    } else {
      console.warn(`  ⚠️ 未知的牌类型key: ${key}`);
    }
  });
  
  console.log('✅ 最终剩余牌数:', remainingCounts);
  return remainingCounts;
};

// 综合分析相关类型定义
export interface ComprehensiveAnalysisChoice {
  tile: string;           // 打牌选择 (如 "1m")
  number: number;         // 有效牌数
  tiles: string[];        // 有效牌列表
}

export interface ComprehensiveAnalysisResult {
  method: 'tenhou_website' | 'local_simulation' | 'exhaustive';
  method_name: string;
  success: boolean;
  error_message?: string;
  choices: ComprehensiveAnalysisChoice[];
  analysis_time: number;
  timestamp: string;
}

export interface ComprehensiveAnalysisResponse {
  hand: string;
  hand_display: string;
  results: ComprehensiveAnalysisResult[];
  comparison?: {
    success_rate: { [key: string]: boolean };
    performance: { [key: string]: string };
    choice_consistency: {
      match_rate: string;
      percentage: string;
    };
    summary: {
      total_methods: number;
      successful_methods: number;
      fastest_method?: string;
    };
  };
}

export interface ComprehensiveAnalysisRequest {
  hand: string;
  methods: Array<'tenhou_website' | 'local_simulation' | 'exhaustive'>;
  tile_format: 'mps' | 'frontend';
} 