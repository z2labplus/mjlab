import React from 'react';
import { motion } from 'framer-motion';
import classNames from 'classnames';
import { Tile, tileToString, TileType } from '../types/mahjong';
import { getTileSvg, getBackSvg } from '../utils/mahjongUtils';

export type CardBackStyle = 'classic' | 'elegant' | 'bamboo' | 'cloud' | 'traditional';

export type TileSize = 'micro' | 'tiny' | 'small' | 'medium' | 'large';

interface MahjongTileProps {
  tile: Tile;
  size?: TileSize;
  variant?: 'default' | 'selected' | 'selectedHorizontal' | 'recommended' | 'disabled' | 'disabledHorizontal' | 'back';
  onClick?: () => void;
  onDoubleClick?: () => void;
  className?: string;
  showBackground?: boolean;
  animationDelay?: number;
  seamless?: boolean;
  direction?: 'horizontal' | 'vertical';
  cardBackStyle?: CardBackStyle;
  remainingCount?: number;
}

const MahjongTile: React.FC<MahjongTileProps> = ({
  tile,
  size = 'medium',
  variant = 'default',
  onClick,
  onDoubleClick,
  className,
  showBackground = true,
  animationDelay = 0,
  seamless = false,
  direction = 'horizontal',
  cardBackStyle = 'elegant',
  remainingCount
}) => {
  const tileText = tileToString(tile);
  
  // 尺寸样式
  const sizeClasses: Record<TileSize, string> = {
    micro: 'w-4 h-6',
    tiny: 'w-6 h-8',
    small: 'w-8 h-10',
    medium: 'w-12 h-16',
    large: 'w-16 h-20'
  };
  
  // SVG尺寸样式
  const svgSizeClasses: Record<TileSize, string> = {
    micro: 'w-3 h-5',
    tiny: 'w-5 h-7',
    small: 'w-7 h-9',
    medium: 'w-10 h-14',
    large: 'w-14 h-18'
  };
  
  // 获取背面样式
  const getBackVariantClasses = (style: CardBackStyle): string => {
    const backStyles = {
      classic: 'bg-gradient-to-br from-green-600 to-green-800 border-green-700',
      elegant: 'bg-gradient-to-br from-blue-50 to-blue-100 border-blue-300', // 改为蓝色背景，更明显
      bamboo: 'bg-gradient-to-br from-emerald-50 to-emerald-100 border-emerald-200',
      cloud: 'bg-gradient-to-br from-slate-50 to-slate-100 border-slate-200',
      traditional: 'bg-gradient-to-br from-red-900 to-red-950 border-red-800'
    };
    return backStyles[style] + ' cursor-not-allowed';
  };
  
  // 变体样式
  const variantClasses = {
    default: 'bg-white border-gray-300 text-gray-800 hover:bg-gray-50',
    selected: 'bg-blue-100 border-blue-400 text-blue-800 ring-2 ring-blue-300',
    selectedHorizontal: 'bg-blue-100 border-blue-400 text-blue-800 ring-2 ring-blue-300',
    recommended: 'bg-green-100 border-green-400 text-green-800 ring-2 ring-green-300 animate-pulse',
    disabled: 'bg-gray-100 border-gray-200 text-gray-400 cursor-not-allowed',
    disabledHorizontal: 'bg-gray-100 border-gray-200 text-gray-400 cursor-not-allowed',
    back: getBackVariantClasses(cardBackStyle)
  };
  

  
  // 根据方向和seamless属性生成边框和圆角样式
  const getSeamlessClasses = () => {
    if (!seamless) {
      return 'border-2 rounded-lg';
    }
    
    if (direction === 'horizontal') {
      // 水平方向：移除右边框，只有最后一个元素有右边框
      return 'border-2 border-r-0 last:border-r-2 rounded-none first:rounded-l-lg last:rounded-r-lg';
    } else {
      // 垂直方向：移除下边框，只有最后一个元素有下边框
      return 'border-2 border-b-0 last:border-b-2 rounded-none first:rounded-t-lg last:rounded-b-lg';
    }
  };
  
  const baseClasses = classNames(
    'relative flex items-center justify-center',
    getSeamlessClasses(),
    'cursor-pointer',
    'font-bold select-none transition-all duration-200',
    seamless ? '' : 'shadow-sm hover:shadow-md',
    sizeClasses[size],
    variantClasses[variant],
    {
      'active:scale-95': onClick && variant !== 'disabled' && variant !== 'back' && !seamless,
      'transform rotate-90': variant === 'selectedHorizontal' || variant === 'disabledHorizontal'
    },
    className
  );
  
  const handleClick = () => {
    if (variant !== 'disabled' && variant !== 'back' && onClick) {
      onClick();
    }
  };
  
  const handleDoubleClick = () => {
    if (variant !== 'disabled' && variant !== 'back' && onDoubleClick) {
      onDoubleClick();
    }
  };
  
  return (
    <motion.div
      className={baseClasses}
      onClick={handleClick}
      onDoubleClick={handleDoubleClick}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ 
        duration: 0.01, 
        delay: 0,
        type: "spring",
        stiffness: 120
      }}
      whileTap={onClick && variant !== 'disabled' && variant !== 'back' ? { scale: 0.95 } : {}}
    >
      {/* 背景装饰 */}
      {showBackground && variant !== 'back' && (
        <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent rounded-lg" />
      )}
      
      {/* SVG显示或背面图案 */}
      {variant === 'back' ? (
        <div className="w-full h-full flex items-center justify-center">
          <img
            src={getBackSvg()}
            alt="麻将牌背面"
            className={classNames(svgSizeClasses[size], 'object-contain')}
            onError={(e) => {
              // 如果SVG加载失败，显示备用的背面样式
              console.warn('背面SVG加载失败，使用备用样式');
              const target = e.target as HTMLImageElement;
              target.style.display = 'none';
              const parent = target.parentElement;
              if (parent) {
                parent.innerHTML = `
                  <div class="w-full h-full bg-gradient-to-br from-blue-600 to-blue-800 rounded flex items-center justify-center text-white font-bold text-xs">
                    麻
                  </div>
                `;
              }
            }}
          />
        </div>
      ) : (
        <img
          src={getTileSvg(tile)}
          alt={tileText}
          className={classNames(svgSizeClasses[size], 'object-contain')}
          onError={(e) => {
            // 如果牌面SVG加载失败，显示文字作为备用
            console.warn(`牌面SVG加载失败: ${tileText}，使用文字显示`);
            const target = e.target as HTMLImageElement;
            target.style.display = 'none';
            const parent = target.parentElement;
            if (parent) {
              parent.innerHTML = `
                <span class="text-xs font-bold">${tileText}</span>
              `;
            }
          }}
        />
      )}
      
      {/* 剩余数量显示 - 只有当数量大于0且不是背面时显示 */}
      {remainingCount !== undefined && remainingCount > 0 && variant !== 'back' && (
        <div className={classNames(
          'absolute -top-1 -right-1 bg-orange-500 text-white font-bold rounded-full flex items-center justify-center z-20',
          {
            'w-3 h-3 text-xs': size === 'micro',
            'w-4 h-4 text-xs': size !== 'micro'
          }
        )}>
          {remainingCount}
        </div>
      )}
      
      {/* 推荐标识 */}
      {variant === 'recommended' && (
        <motion.div
          className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full"
          animate={{
            scale: [1, 1.2, 1],
            opacity: [1, 0.7, 1]
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      )}
      
      {/* 选中标识 */}
      {variant === 'selected' && (
        <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full" />
      )}
      
      {/* 横向选中标识 */}
      {variant === 'selectedHorizontal' && (
        <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full">
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-1.5 h-0.5 bg-white rounded-full transform rotate-90" />
          </div>
        </div>
      )}
    </motion.div>
  );
};

export default MahjongTile; 