import { Tile, TileType } from '../types/mahjong';

/**
 * 获取麻将牌对应的SVG文件路径
 * @param tile 麻将牌对象
 * @returns SVG文件路径
 */
export const getTileSvg = (tile: Tile): string => {
  let filename = '';
  
  switch (tile.type) {
    case TileType.WAN:
      filename = `${tile.value}m.svg`;
      break;
    case TileType.TIAO:
      filename = `${tile.value}s.svg`;
      break;
    case TileType.TONG:
      filename = `${tile.value}p.svg`;
      break;
    default:
      filename = '5z.svg'; // 默认返回背面
  }
  
  // 使用public目录的URL路径
  return `/assets/mahjong/${filename}`;
};

/**
 * 获取麻将牌背面SVG
 * @returns 背面SVG文件路径
 */
export const getBackSvg = (): string => {
  return '/assets/mahjong/5z.svg';
};

/**
 * 检查麻将牌是否有对应的SVG文件
 * @param tile 麻将牌对象
 * @returns 是否存在对应的SVG文件
 */
export const hasTileSvg = (tile: Tile): boolean => {
  // 对于public目录的文件，我们假设所有有效的牌都存在对应的SVG
  if (tile.type === TileType.WAN || tile.type === TileType.TIAO || tile.type === TileType.TONG) {
    return tile.value >= 1 && tile.value <= 9;
  }
  return false;
}; 