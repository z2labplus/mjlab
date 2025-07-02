import React from 'react';
import { motion } from 'framer-motion';

interface SimpleSourceIndicatorProps {
  sourcePlayer: number;
  currentPlayer: number;
  className?: string;
}

const SimpleSourceIndicator: React.FC<SimpleSourceIndicatorProps> = ({ 
  sourcePlayer, 
  currentPlayer,
  className = ''
}) => {
  // 获取来源玩家的简短标识
  const getSourceLabel = (): string => {
    // 直接根据玩家ID映射显示对应标识
    // 玩家ID映射：0=我，1=下家，2=对家，3=上家
    const playerLabels = ['我', '下', '对', '上'];
    
    // 如果sourcePlayer为undefined、null或超出范围，返回问号
    if (sourcePlayer === undefined || sourcePlayer === null || sourcePlayer < 0 || sourcePlayer > 3) {
      console.warn(`⚠️ SimpleSourceIndicator: 无效的sourcePlayer值: ${sourcePlayer}`);
      return '?';
    }
    
    return playerLabels[sourcePlayer];
  };

  // 获取提示文本
  const getTooltipText = (): string => {
    const label = getSourceLabel();
    if (label === '我') return '杠了自己的弃牌';
    return `杠了${label}家的弃牌`;
  };

  return (
    <motion.div
      className={`w-4 h-4 bg-red-600 text-white text-xs font-bold rounded-sm flex items-center justify-center shadow-md z-30 ${className}`}
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ 
        delay: 0.2, 
        type: "spring", 
        stiffness: 300,
        damping: 20
      }}
      title={getTooltipText()}
    >
      {getSourceLabel()}
    </motion.div>
  );
};

export default SimpleSourceIndicator; 