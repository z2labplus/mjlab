# 血战麻将 - 杠牌显示解决方案

## 问题分析

在血战麻将中，杠牌有两种类型：
1. **直杠（明杠）**：杠其他玩家打出的牌，需要显示是杠的哪个玩家
2. **加杠**：在已有碰牌基础上加杠，需要区分原碰牌和新加的牌

## 数据结构设计

### 杠牌数据模型
```typescript
interface KongMeld {
  id: string;                    // 杠牌唯一ID
  type: 'direct_kong' | 'added_kong'; // 杠牌类型
  card: MahjongCard;            // 杠的牌
  cards: MahjongCard[];         // 所有4张牌
  source_player?: number;        // 直杠：被杠牌的来源玩家ID
  original_peng_id?: string;     // 加杠：原碰牌的ID
  kong_player: number;           // 杠牌的玩家ID
  timestamp: number;             // 杠牌时间戳
}

// 示例数据
const directKong: KongMeld = {
  id: "kong_001",
  type: "direct_kong",
  card: { id: 5, suit: "wan", value: 5 },
  cards: [
    { id: 5, suit: "wan", value: 5 },  // 来自其他玩家
    { id: 5, suit: "wan", value: 5 },  // 手牌
    { id: 5, suit: "wan", value: 5 },  // 手牌
    { id: 5, suit: "wan", value: 5 }   // 手牌
  ],
  source_player: 2,  // 来自玩家2
  kong_player: 0,    // 玩家0杠牌
  timestamp: Date.now()
};

const addedKong: KongMeld = {
  id: "kong_002", 
  type: "added_kong",
  card: { id: 3, suit: "tiao", value: 3 },
  cards: [
    { id: 3, suit: "tiao", value: 3 },
    { id: 3, suit: "tiao", value: 3 },
    { id: 3, suit: "tiao", value: 3 },
    { id: 3, suit: "tiao", value: 3 }
  ],
  original_peng_id: "peng_001",
  kong_player: 0,
  timestamp: Date.now()
};
```

## UI组件设计

### 1. KongDisplay 组件
```tsx
interface KongDisplayProps {
  kong: KongMeld;
  playerPosition: 'bottom' | 'right' | 'top' | 'left';
  className?: string;
}

const KongDisplay: React.FC<KongDisplayProps> = ({ 
  kong, 
  playerPosition, 
  className 
}) => {
  const getCardLayout = () => {
    if (kong.type === 'direct_kong') {
      return getDirectKongLayout();
    } else {
      return getAddedKongLayout();
    }
  };

  const getDirectKongLayout = () => {
    // 直杠布局：3张竖放 + 1张横放（表示来源）
    return (
      <div className={`kong-container direct-kong ${className}`}>
        {/* 前3张牌竖放 */}
        <div className="vertical-cards flex">
          {kong.cards.slice(0, 3).map((card, index) => (
            <MahjongCard
              key={index}
              card={card}
              orientation="vertical"
              className="mr-1"
            />
          ))}
        </div>
        
        {/* 第4张牌横放，表示来自其他玩家 */}
        <div className="horizontal-card relative">
          <MahjongCard
            card={kong.cards[3]}
            orientation="horizontal"
            className="ml-2"
          />
          
          {/* 来源指示器 */}
          <SourceIndicator 
            sourcePlayer={kong.source_player!}
            currentPlayer={kong.kong_player}
            position={playerPosition}
          />
        </div>
      </div>
    );
  };

  const getAddedKongLayout = () => {
    // 加杠布局：原碰牌3张 + 新加1张（有特殊标记）
    return (
      <div className={`kong-container added-kong ${className}`}>
        {/* 原来的3张碰牌 */}
        <div className="original-peng flex">
          {kong.cards.slice(0, 3).map((card, index) => (
            <MahjongCard
              key={index}
              card={card}
              orientation="vertical"
              className="mr-1"
            />
          ))}
        </div>
        
        {/* 新加的第4张牌 */}
        <div className="added-card relative">
          <MahjongCard
            card={kong.cards[3]}
            orientation="vertical"
            className="ml-2 border-2 border-yellow-400"
          />
          
          {/* 加杠标识 */}
          <div className="absolute -top-1 -right-1 bg-yellow-400 text-xs px-1 rounded">
            加
          </div>
        </div>
      </div>
    );
  };

  return getCardLayout();
};
```

### 2. SourceIndicator 来源指示组件
```tsx
interface SourceIndicatorProps {
  sourcePlayer: number;
  currentPlayer: number;
  position: 'bottom' | 'right' | 'top' | 'left';
}

const SourceIndicator: React.FC<SourceIndicatorProps> = ({
  sourcePlayer,
  currentPlayer,
  position
}) => {
  const getDirection = () => {
    // 根据玩家位置计算方向
    const positions = ['bottom', 'right', 'top', 'left'];
    const currentIndex = positions.indexOf(position);
    const sourceIndex = (currentIndex + sourcePlayer - currentPlayer + 4) % 4;
    return positions[sourceIndex];
  };

  const getArrowIcon = () => {
    const direction = getDirection();
    const arrowMap = {
      'bottom': '↓',
      'right': '→', 
      'top': '↑',
      'left': '←'
    };
    return arrowMap[direction];
  };

  return (
    <div className="absolute -top-2 -right-2 bg-red-500 text-white text-xs w-6 h-6 rounded-full flex items-center justify-center">
      {getArrowIcon()}
    </div>
  );
};
```

### 3. MahjongCard 基础组件
```tsx
interface MahjongCardProps {
  card: MahjongCard;
  orientation?: 'vertical' | 'horizontal';
  className?: string;
}

const MahjongCard: React.FC<MahjongCardProps> = ({ 
  card, 
  orientation = 'vertical',
  className 
}) => {
  const cardClasses = classNames(
    'mahjong-card bg-white border border-gray-300 rounded shadow-sm',
    {
      'w-8 h-12': orientation === 'vertical',
      'w-12 h-8': orientation === 'horizontal',
    },
    className
  );

  return (
    <div className={cardClasses}>
      <div className={`card-content flex items-center justify-center h-full ${
        orientation === 'horizontal' ? 'transform rotate-90' : ''
      }`}>
        <span className="text-xs font-bold">
          {card.value}{getSuitSymbol(card.suit)}
        </span>
      </div>
    </div>
  );
};

const getSuitSymbol = (suit: string): string => {
  const symbols = {
    'wan': '万',
    'tiao': '条', 
    'tong': '筒'
  };
  return symbols[suit] || '';
};
```

## CSS样式设计

```css
/* Kong Display Styles */
.kong-container {
  @apply flex items-end p-2 bg-gray-50 rounded-lg border border-gray-200;
  min-height: 60px;
}

.direct-kong {
  @apply relative;
}

.direct-kong .horizontal-card {
  @apply ml-1;
}

.added-kong .added-card {
  @apply relative;
}

.mahjong-card {
  @apply transition-all duration-200;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.mahjong-card:hover {
  @apply transform -translate-y-1;
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

/* 不同位置的Kong显示 */
.player-bottom .kong-container {
  @apply flex-row;
}

.player-right .kong-container {
  @apply flex-col;
}

.player-top .kong-container {
  @apply flex-row-reverse;
}

.player-left .kong-container {
  @apply flex-col-reverse;
}
```

## 使用示例

```tsx
const GameBoard: React.FC = () => {
  const [kongs, setKongs] = useState<KongMeld[]>([]);

  return (
    <div className="game-board">
      {/* 玩家手牌区域 */}
      <div className="player-melds">
        {kongs.map(kong => (
          <KongDisplay
            key={kong.id}
            kong={kong}
            playerPosition="bottom"
            className="mb-2"
          />
        ))}
      </div>
    </div>
  );
};
```

## 交互反馈

### 1. 杠牌动画
```tsx
const KongAnimation: React.FC<{ kong: KongMeld }> = ({ kong }) => {
  return (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <KongDisplay kong={kong} playerPosition="bottom" />
    </motion.div>
  );
};
```

### 2. 悬停提示
```tsx
const KongTooltip: React.FC<{ kong: KongMeld }> = ({ kong }) => {
  const getTooltipText = () => {
    if (kong.type === 'direct_kong') {
      return `直杠 - 杠了玩家${kong.source_player + 1}的${kong.card.value}${getSuitSymbol(kong.card.suit)}`;
    } else {
      return `加杠 - 在原有碰牌基础上加杠${kong.card.value}${getSuitSymbol(kong.card.suit)}`;
    }
  };

  return (
    <div className="tooltip-container group relative">
      <KongDisplay kong={kong} playerPosition="bottom" />
      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-black text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity">
        {getTooltipText()}
      </div>
    </div>
  );
};
```

## 响应式设计

```tsx
const ResponsiveKongDisplay: React.FC<KongDisplayProps> = (props) => {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  return (
    <div className={isMobile ? 'kong-mobile' : 'kong-desktop'}>
      <KongDisplay {...props} />
    </div>
  );
};
```

## 总结

这个方案提供了：

1. **清晰的视觉区分** - 直杠和加杠有不同的显示方式
2. **来源指示** - 通过箭头和位置明确显示直杠的牌来源
3. **动画反馈** - 杠牌时的流畅动画效果
4. **响应式设计** - 适配不同屏幕尺寸
5. **交互提示** - 悬停显示详细信息

这样的设计能让玩家清楚地知道每个杠牌的类型和来源，提升游戏体验。 