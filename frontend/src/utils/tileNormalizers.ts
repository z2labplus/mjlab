import { GameState, HandTiles, Meld, Tile, TileType } from '../types/mahjong';

// 将后端/脚本的花色字符串规范化为前端内部使用的 m/s/p/z
export const normalizeTileType = (type: string | undefined | null): TileType => {
  const t = (type || '').toString().toLowerCase();
  switch (t) {
    case 'wan':
    case 'm':
      return TileType.WAN;
    case 'tiao':
    case 's':
      return TileType.TIAO;
    case 'tong':
    case 'p':
      return TileType.TONG;
    case 'zi':
    case 'z':
      return TileType.ZI;
    default:
      // 默认按字牌处理，避免渲染报错
      return TileType.ZI;
  }
};

// 将前端内部 m/s/p/z 转换为后端期望的 wan/tiao/tong/zi
export const toBackendTileType = (type: string | undefined | null): 'wan' | 'tiao' | 'tong' | 'zi' => {
  const t = (type || '').toString().toLowerCase();
  switch (t) {
    case 'm':
    case 'wan':
      return 'wan';
    case 's':
    case 'tiao':
      return 'tiao';
    case 'p':
    case 'tong':
      return 'tong';
    default:
      return 'zi';
  }
};

export const normalizeTile = (tileLike: any): Tile => {
  if (!tileLike || typeof tileLike !== 'object') {
    // 返回一个可渲染的占位，以免前端崩溃
    return { type: TileType.ZI, value: 5 } as Tile;
  }
  return {
    type: normalizeTileType(tileLike.type),
    value: Number(tileLike.value),
    id: tileLike.id,
  } as Tile;
};

export const normalizeMeld = (meldLike: any): Meld => {
  const tiles = Array.isArray(meldLike?.tiles) ? meldLike.tiles.map(normalizeTile) : [];
  return {
    id: meldLike?.id,
    type: meldLike?.type,
    tiles,
    exposed: Boolean(meldLike?.exposed),
    gang_type: meldLike?.gang_type,
    source_player: meldLike?.source_player,
    original_peng_id: meldLike?.original_peng_id,
    timestamp: meldLike?.timestamp,
  } as Meld;
};

export const normalizeHand = (handLike: any): HandTiles => {
  const tiles = Array.isArray(handLike?.tiles) ? handLike.tiles.map(normalizeTile) : handLike?.tiles ?? null;
  const melds = Array.isArray(handLike?.melds) ? handLike.melds.map(normalizeMeld) : [];
  const tile_count = Array.isArray(tiles) ? tiles.length : (typeof handLike?.tile_count === 'number' ? handLike.tile_count : 0);
  return {
    tiles: tiles,
    tile_count,
    melds,
    missing_suit: handLike?.missing_suit ?? null,
    is_winner: handLike?.is_winner ?? false,
    win_type: handLike?.win_type,
    win_tile: handLike?.win_tile ? normalizeTile(handLike.win_tile) : undefined,
    dianpao_player_id: handLike?.dianpao_player_id,
  } as HandTiles;
};

// 规范化整个 GameState（入站）
export const normalizeGameState = (gs: any): GameState => {
  const player_hands: Record<string, HandTiles> = {};
  const srcHands = (gs && gs.player_hands) || {};
  Object.keys(srcHands).forEach((pid) => {
    player_hands[pid] = normalizeHand(srcHands[pid]);
  });

  const player_discarded_tiles: Record<string, Tile[]> = {};
  const srcDiscards = (gs && gs.player_discarded_tiles) || {};
  Object.keys(srcDiscards).forEach((pid) => {
    const arr = Array.isArray(srcDiscards[pid]) ? srcDiscards[pid].map(normalizeTile) : [];
    player_discarded_tiles[pid] = arr;
  });

  const discarded_tiles: Tile[] = Array.isArray(gs?.discarded_tiles)
    ? gs.discarded_tiles.map(normalizeTile)
    : [];

  return {
    game_id: (gs && gs.game_id) || 'default',
    player_hands,
    player_discarded_tiles,
    discarded_tiles,
    actions_history: Array.isArray(gs?.actions_history) ? gs.actions_history : [],
    current_player: typeof gs?.current_player === 'number' ? gs.current_player : 0,
    game_started: Boolean(gs?.game_started),
    game_ended: Boolean(gs?.game_ended),
    show_all_hands: Boolean(gs?.show_all_hands),
  } as GameState;
};

// 将 GameState 转回后端所需格式（出站）
export const convertGameStateToBackend = (gs: GameState): any => {
  const toBackendTile = (t: Tile) => ({ type: toBackendTileType(t.type), value: t.value, id: (t as any).id });

  const player_hands: Record<string, any> = {};
  Object.keys(gs.player_hands || {}).forEach((pid) => {
    const hand = gs.player_hands[pid] as any;
    const tiles = Array.isArray(hand?.tiles) ? hand.tiles.map(toBackendTile) : hand?.tiles ?? null;
    const melds = Array.isArray(hand?.melds)
      ? hand.melds.map((m: any) => ({
          ...m,
          tiles: Array.isArray(m?.tiles) ? m.tiles.map(toBackendTile) : [],
        }))
      : [];
    const out: any = { ...hand, tiles, melds };
    if (hand?.win_tile) out.win_tile = toBackendTile(hand.win_tile);
    // tile_count 与 tiles 长度保持一致
    out.tile_count = Array.isArray(tiles) ? tiles.length : hand?.tile_count || 0;
    player_hands[pid] = out;
  });

  const player_discarded_tiles: Record<string, any[]> = {};
  Object.keys(gs.player_discarded_tiles || {}).forEach((pid) => {
    const arr = gs.player_discarded_tiles[pid] || [];
    player_discarded_tiles[pid] = arr.map(toBackendTile);
  });

  const discarded_tiles = (gs.discarded_tiles || []).map(toBackendTile);

  return {
    ...gs,
    player_hands,
    player_discarded_tiles,
    discarded_tiles,
  };
};

