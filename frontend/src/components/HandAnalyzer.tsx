import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Tile, TileType } from '../types/mahjong';
import MahjongTile from './MahjongTile';
import { tileToString } from '../types/mahjong';

interface AnalysisResult {
  is_winning: boolean;
  shanten: number;
  effective_draws: Tile[];
  winning_tiles: Tile[];
  detailed_analysis: {
    current_shanten: number;
    draw_analysis: {
      tile: string;
      new_shanten: number;
      probability: number;
    }[];
    patterns: string[];
    suggestions: string[];
  };
}

interface HandAnalyzerProps {
  className?: string;
}

const HandAnalyzer: React.FC<HandAnalyzerProps> = ({ className }) => {
  const [selectedTiles, setSelectedTiles] = useState<Tile[]>([]);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [hoveredTile, setHoveredTile] = useState<string | null>(null);

  // 生成所有可能的麻将牌（当前只支持万、条、筒，不包含字牌）
  const getAllTiles = (): Tile[] => {
    const tiles: Tile[] = [];
    
    // 万子 1-9
    for (let i = 1; i <= 9; i++) {
      tiles.push({ type: TileType.WAN, value: i });
    }
    
    // 条子 1-9  
    for (let i = 1; i <= 9; i++) {
      tiles.push({ type: TileType.TIAO, value: i });
    }
    
    // 筒子 1-9
    for (let i = 1; i <= 9; i++) {
      tiles.push({ type: TileType.TONG, value: i });
    }
    
    // TODO: 未来可以添加字牌支持
    // 字牌：东南西北中发白 (1-7)
    // for (let i = 1; i <= 7; i++) {
    //   tiles.push({ type: TileType.ZI, value: i });
    // }
    
    return tiles;
  };

  const allTiles = getAllTiles();

  // 添加牌到手牌
  const addTile = (tile: Tile) => {
    if (selectedTiles.length >= 14) {
      return; // 最多14张牌
    }
    
    // 检查该牌是否已有4张
    const existingCount = selectedTiles.filter(t => 
      t.type === tile.type && t.value === tile.value
    ).length;
    
    if (existingCount >= 4) {
      return; // 每种牌最多4张
    }
    
    setSelectedTiles([...selectedTiles, tile]);
    setAnalysisResult(null); // 清除之前的分析结果
  };

  // 移除牌
  const removeTile = (index: number) => {
    const newTiles = [...selectedTiles];
    newTiles.splice(index, 1);
    setSelectedTiles(newTiles);
    setAnalysisResult(null);
  };

  // 清空手牌
  const clearHand = () => {
    setSelectedTiles([]);
    setAnalysisResult(null);
  };

  // 预设手牌示例
  const setPresetHand = (preset: string) => {
    let tiles: Tile[] = [];
    
    switch (preset) {
      case 'winning':
        // 胡牌示例：123456789万99条
        tiles = [
          { type: TileType.WAN, value: 1 },
          { type: TileType.WAN, value: 2 },
          { type: TileType.WAN, value: 3 },
          { type: TileType.WAN, value: 4 },
          { type: TileType.WAN, value: 5 },
          { type: TileType.WAN, value: 6 },
          { type: TileType.WAN, value: 7 },
          { type: TileType.WAN, value: 8 },
          { type: TileType.WAN, value: 9 },
          { type: TileType.TIAO, value: 9 },
          { type: TileType.TIAO, value: 9 }
        ];
        break;
      case 'seven_pairs':
        // 七对示例：112233445566万77条
        tiles = [
          { type: TileType.WAN, value: 1 },
          { type: TileType.WAN, value: 1 },
          { type: TileType.WAN, value: 2 },
          { type: TileType.WAN, value: 2 },
          { type: TileType.WAN, value: 3 },
          { type: TileType.WAN, value: 3 },
          { type: TileType.WAN, value: 4 },
          { type: TileType.WAN, value: 4 },
          { type: TileType.WAN, value: 5 },
          { type: TileType.WAN, value: 5 },
          { type: TileType.WAN, value: 6 },
          { type: TileType.WAN, value: 6 },
          { type: TileType.TIAO, value: 7 },
          { type: TileType.TIAO, value: 7 }
        ];
        break;
      case 'one_shanten':
        // 一向听示例：12345678万9条
        tiles = [
          { type: TileType.WAN, value: 1 },
          { type: TileType.WAN, value: 2 },
          { type: TileType.WAN, value: 3 },
          { type: TileType.WAN, value: 4 },
          { type: TileType.WAN, value: 5 },
          { type: TileType.WAN, value: 6 },
          { type: TileType.WAN, value: 7 },
          { type: TileType.WAN, value: 8 },
          { type: TileType.TIAO, value: 9 }
        ];
        break;
      default:
        tiles = [];
    }
    
    setSelectedTiles(tiles);
    setAnalysisResult(null);
  };

  // 分析手牌
  const analyzeHand = async () => {
    if (selectedTiles.length === 0) {
      return;
    }

    setIsAnalyzing(true);
    
    // 分析前自动排序手牌
    const sortedTiles = sortTiles(selectedTiles);
    setSelectedTiles(sortedTiles);
    
    try {
      // 转换为后端需要的格式
      const handData = {
        tiles: sortedTiles.map(tile => `${tile.value}${tile.type}`),
        melds: []
      };

      const response = await fetch('http://localhost:8000/api/mahjong/analyze-hand', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(handData),
      });

      if (response.ok) {
        const result = await response.json();
        
        // 确保effective_draws和winning_tiles的数据格式正确
        if (result.effective_draws) {
          result.effective_draws = result.effective_draws.map((tile: any) => {
            // 如果是字典格式，转换为正确的Tile对象
            if (typeof tile === 'object' && tile.type && tile.value) {
              return {
                type: tile.type as TileType,
                value: tile.value
              };
            }
            return tile;
          });
        }
        
        if (result.winning_tiles) {
          result.winning_tiles = result.winning_tiles.map((tile: any) => {
            // 如果是字典格式，转换为正确的Tile对象
            if (typeof tile === 'object' && tile.type && tile.value) {
              return {
                type: tile.type as TileType,
                value: tile.value
              };
            }
            return tile;
          });
        }
        
        console.log('Analysis result:', result); // 调试信息
        setAnalysisResult(result);
      } else {
        console.error('分析失败');
      }
    } catch (error) {
      console.error('分析错误:', error);
    }
    
    setIsAnalyzing(false);
  };

  // 获取牌的显示计数
  const getTileCount = (tile: Tile): number => {
    return selectedTiles.filter(t => 
      t.type === tile.type && t.value === tile.value
    ).length;
  };

  // 排序手牌
  const sortTiles = (tiles: Tile[]): Tile[] => {
    return [...tiles].sort((a, b) => {
      // 首先按花色排序：万 < 条 < 筒 < 字
      const typeOrder: Record<TileType, number> = { 
        [TileType.WAN]: 1, 
        [TileType.TIAO]: 2, 
        [TileType.TONG]: 3,
        [TileType.ZI]: 4
      };
      
      const aOrder = typeOrder[a.type] || 999;
      const bOrder = typeOrder[b.type] || 999;
      
      if (aOrder !== bOrder) {
        return aOrder - bOrder;
      }
      // 相同花色按数值排序
      return a.value - b.value;
    });
  };

  // 获取排序后的手牌
  const getSortedTiles = (): Tile[] => {
    return sortTiles(selectedTiles);
  };

  // 自动排序功能
  const autoSortTiles = () => {
    setSelectedTiles(sortTiles(selectedTiles));
  };

  // 快速添加相同牌
  const quickAddTile = (tile: Tile, count: number = 1) => {
    const currentCount = getTileCount(tile);
    const maxAdd = Math.min(count, 4 - currentCount, 14 - selectedTiles.length);
    
    if (maxAdd > 0) {
      const newTiles = [...selectedTiles];
      for (let i = 0; i < maxAdd; i++) {
        newTiles.push(tile);
      }
      setSelectedTiles(newTiles);
      setAnalysisResult(null);
    }
  };

  // 键盘快捷键支持
  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      if (event.target instanceof HTMLInputElement) return; // 忽略输入框中的按键
      
      switch (event.key.toLowerCase()) {
        case 'enter':
        case ' ':
          if (selectedTiles.length > 0) {
            analyzeHand();
          }
          break;
        case 'c':
          if (selectedTiles.length > 0) {
            clearHand();
          }
          break;
        case 's':
          if (selectedTiles.length > 1) {
            autoSortTiles();
          }
          break;
        case 'escape':
          setAnalysisResult(null);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [selectedTiles]);

  return (
    <div className={`min-h-screen bg-gradient-to-br from-green-50 to-green-100 ${className}`}>
      {/* 背景装饰 */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-72 h-72 bg-green-500/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-green-500/5 rounded-full blur-3xl"></div>
      </div>

      <div className="relative z-10 container mx-auto p-6">

        {/* 主要内容区域 */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          
          {/* 左侧：牌池选择区 */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="xl:col-span-1"
          >
            <div className="bg-white/90 backdrop-filter backdrop-blur-lg rounded-2xl border border-gray-200 p-6 shadow-lg">
              <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
                <span className="w-2 h-2 bg-green-400 rounded-full mr-3"></span>
                选择手牌
              </h2>
              
              {/* 预设手牌按钮 */}
              <div className="mb-6 flex flex-wrap gap-2">
                <button
                  onClick={() => setPresetHand('winning')}
                  className="px-4 py-2 bg-green-500/20 text-green-300 rounded-lg hover:bg-green-500/30 transition-all duration-200 text-sm"
                >
                  🏆 胡牌示例
                </button>
                <button
                  onClick={() => setPresetHand('seven_pairs')}
                  className="px-4 py-2 bg-purple-500/20 text-purple-300 rounded-lg hover:bg-purple-500/30 transition-all duration-200 text-sm"
                >
                  🎭 七对示例
                </button>
                <button
                  onClick={() => setPresetHand('one_shanten')}
                  className="px-4 py-2 bg-green-500/20 text-blue-300 rounded-lg hover:bg-green-500/30 transition-all duration-200 text-sm"
                >
                  🎯 一向听示例
                </button>
                <button
                  onClick={clearHand}
                  className="px-4 py-2 bg-red-500/20 text-red-300 rounded-lg hover:bg-red-500/30 transition-all duration-200 text-sm"
                >
                  🗑️ 清空
                </button>
              </div>

              {/* 牌池 */}
              <div className="space-y-4">
                {/* 万子 */}
                <div>
                  <h3 className="text-gray-800 mb-2 text-sm font-medium flex items-center">
                    万子
                    <span className="ml-2 text-xs text-gray-500">左键添加 • 右键添加多张</span>
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {allTiles.filter(t => t.type === TileType.WAN).map((tile, index) => (
                      <div key={`wan-${index}`} className="relative">
                        <motion.div
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onHoverStart={() => setHoveredTile(`${tile.value}${tile.type}`)}
                          onHoverEnd={() => setHoveredTile(null)}
                        >
                          <MahjongTile
                            tile={tile}
                            size="small"
                            onClick={() => addTile(tile)}
                            onContextMenu={(e: React.MouseEvent<HTMLDivElement>) => {
                              e.preventDefault();
                              quickAddTile(tile, 4 - getTileCount(tile)); // 右键添加到最大数量
                            }}
                            className={`cursor-pointer transition-all duration-200 ${
                              getTileCount(tile) >= 4 
                                ? 'opacity-30 cursor-not-allowed' 
                                : 'opacity-80 hover:opacity-100 hover:shadow-lg'
                            }`}
                          />
                        </motion.div>
                        {getTileCount(tile) > 0 && (
                          <div className="absolute -top-2 -right-2 w-5 h-5 bg-green-500 text-white text-xs rounded-full flex items-center justify-center font-bold">
                            {getTileCount(tile)}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* 条子 */}
                <div>
                  <h3 className="text-gray-800 mb-2 text-sm font-medium">条子</h3>
                  <div className="flex flex-wrap gap-2">
                    {allTiles.filter(t => t.type === TileType.TIAO).map((tile, index) => (
                      <div key={`tiao-${index}`} className="relative">
                        <motion.div
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onHoverStart={() => setHoveredTile(`${tile.value}${tile.type}`)}
                          onHoverEnd={() => setHoveredTile(null)}
                        >
                          <MahjongTile
                            tile={tile}
                            size="small"
                            onClick={() => addTile(tile)}
                            onContextMenu={(e: React.MouseEvent<HTMLDivElement>) => {
                              e.preventDefault();
                              quickAddTile(tile, 4 - getTileCount(tile));
                            }}
                            className={`cursor-pointer transition-all duration-200 ${
                              getTileCount(tile) >= 4 
                                ? 'opacity-30 cursor-not-allowed' 
                                : 'opacity-80 hover:opacity-100 hover:shadow-lg'
                            }`}
                          />
                        </motion.div>
                        {getTileCount(tile) > 0 && (
                          <div className="absolute -top-2 -right-2 w-5 h-5 bg-green-500 text-white text-xs rounded-full flex items-center justify-center font-bold">
                            {getTileCount(tile)}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* 筒子 */}
                <div>
                  <h3 className="text-gray-800 mb-2 text-sm font-medium">筒子</h3>
                  <div className="flex flex-wrap gap-2">
                    {allTiles.filter(t => t.type === TileType.TONG).map((tile, index) => (
                      <div key={`tong-${index}`} className="relative">
                        <motion.div
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onHoverStart={() => setHoveredTile(`${tile.value}${tile.type}`)}
                          onHoverEnd={() => setHoveredTile(null)}
                        >
                          <MahjongTile
                            tile={tile}
                            size="small"
                            onClick={() => addTile(tile)}
                            onContextMenu={(e: React.MouseEvent<HTMLDivElement>) => {
                              e.preventDefault();
                              quickAddTile(tile, 4 - getTileCount(tile));
                            }}
                            className={`cursor-pointer transition-all duration-200 ${
                              getTileCount(tile) >= 4 
                                ? 'opacity-30 cursor-not-allowed' 
                                : 'opacity-80 hover:opacity-100 hover:shadow-lg'
                            }`}
                          />
                        </motion.div>
                        {getTileCount(tile) > 0 && (
                          <div className="absolute -top-2 -right-2 w-5 h-5 bg-green-500 text-white text-xs rounded-full flex items-center justify-center font-bold">
                            {getTileCount(tile)}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* 右侧：手牌和分析区 */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-6 xl:col-span-2"
          >
            
            {/* 当前手牌 */}
            <div className="bg-white/90 backdrop-filter backdrop-blur-lg rounded-2xl border border-gray-200 p-6 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-800 flex items-center">
                  <span className="w-2 h-2 bg-green-400 rounded-full mr-3"></span>
                  当前手牌
                </h2>
                <div className="flex items-center space-x-3">
                  <span className="text-sm text-gray-600">
                    {selectedTiles.length}/14张
                  </span>
                  {selectedTiles.length > 1 && (
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={autoSortTiles}
                      className="px-3 py-1 bg-yellow-500/20 text-yellow-300 rounded-md hover:bg-yellow-500/30 transition-all duration-200 text-xs flex items-center"
                    >
                      🔧 排序
                    </motion.button>
                  )}
                </div>
              </div>
              
              <div className="min-h-[140px] bg-black/20 rounded-lg p-4 mb-4 relative">
                {selectedTiles.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                    <div className="text-center">
                      <div className="text-2xl mb-2">🀄</div>
                      <div>请从下方选择麻将牌组成手牌</div>
                      <div className="text-xs mt-1">支持拖拽排序 • 点击牌可移除</div>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {/* 按花色分组显示 */}
                    {[TileType.WAN, TileType.TIAO, TileType.TONG].map(tileType => {
                      const tilesOfType = selectedTiles.filter(tile => tile.type === tileType);
                      if (tilesOfType.length === 0) return null;
                      
                      const sortedTilesOfType = sortTiles(tilesOfType);
                      const typeNames: Record<TileType, string> = { 
                        [TileType.WAN]: '万', 
                        [TileType.TIAO]: '条', 
                        [TileType.TONG]: '筒',
                        [TileType.ZI]: '字'
                      };
                      
                      return (
                        <div key={tileType} className="space-y-1">
                          <div className="text-xs text-gray-600 flex items-center">
                            <span className="w-1 h-1 bg-gray-400 rounded-full mr-2"></span>
                            {typeNames[tileType]}子 ({tilesOfType.length}张)
                          </div>
                          <div className="flex flex-wrap gap-1">
                            <AnimatePresence>
                              {sortedTilesOfType.map((tile, typeIndex) => {
                                const globalIndex = selectedTiles.findIndex((t, i) => 
                                  t.type === tile.type && t.value === tile.value && 
                                  selectedTiles.slice(0, i + 1).filter(st => st.type === tile.type && st.value === tile.value).length === 
                                  sortedTilesOfType.slice(0, typeIndex + 1).filter(st => st.type === tile.type && st.value === tile.value).length
                                );
                                return (
                                  <motion.div
                                    key={`${tileType}-${typeIndex}-${tile.value}`}
                                    initial={{ opacity: 0, scale: 0.8 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    exit={{ opacity: 0, scale: 0.8 }}
                                    whileHover={{ scale: 1.05, y: -2 }}
                                    layout
                                  >
                                    <MahjongTile
                                      tile={tile}
                                      size="small"
                                      onClick={() => removeTile(globalIndex)}
                                      className="cursor-pointer hover:opacity-70 transition-all duration-200 shadow-md hover:shadow-lg"
                                    />
                                  </motion.div>
                                );
                              })}
                            </AnimatePresence>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* 操作按钮组 */}
              <div className="space-y-3">
                {/* 主要分析按钮 */}
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={analyzeHand}
                  disabled={selectedTiles.length === 0 || isAnalyzing}
                  className="w-full py-3 px-6 bg-gradient-to-r from-green-500 to-emerald-500 text-white font-semibold rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:from-green-600 hover:to-emerald-600 transition-all duration-200 flex items-center justify-center shadow-lg"
                >
                  {isAnalyzing ? (
                    <>
                      <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                      AI分析中...
                    </>
                  ) : (
                    <>
                      🧠 智能分析
                      <span className="ml-2 text-xs opacity-75">({selectedTiles.length}张)</span>
                    </>
                  )}
                </motion.button>

                {/* 辅助功能按钮 */}
                {selectedTiles.length > 0 && (
                  <div className="grid grid-cols-2 gap-2">
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={autoSortTiles}
                      className="py-2 px-3 bg-yellow-500/20 text-yellow-700 rounded-md hover:bg-yellow-500/30 transition-all duration-200 text-sm flex items-center justify-center"
                    >
                      🔧 重新排序
                    </motion.button>
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={clearHand}
                      className="py-2 px-3 bg-red-500/20 text-red-600 rounded-md hover:bg-red-500/30 transition-all duration-200 text-sm flex items-center justify-center"
                    >
                      🗑️ 清空手牌
                    </motion.button>
                  </div>
                )}
              </div>
            </div>

            {/* 分析结果 */}
            <AnimatePresence>
              {analysisResult && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="bg-white/90 backdrop-filter backdrop-blur-lg rounded-2xl border border-gray-200 p-6 shadow-lg"
                >
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-semibold text-gray-800 flex items-center">
                      <span className="w-2 h-2 bg-green-400 rounded-full mr-3"></span>
                      AI分析结果
                    </h2>
                    {/* 状态指示器 */}
                    <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                      analysisResult.is_winning 
                        ? 'bg-green-500/20 text-green-700' 
                        : analysisResult.shanten <= 1 
                          ? 'bg-yellow-500/20 text-yellow-700'
                          : 'bg-green-500/20 text-blue-700'
                    }`}>
                      {analysisResult.is_winning ? '✅ 胡牌' : `${analysisResult.shanten}向听`}
                    </div>
                  </div>

                  {/* 核心指标卡片 */}
                  <div className="grid grid-cols-1 gap-3 mb-6">
                    {/* 主要状态卡片 */}
                    <div className={`p-4 rounded-xl border-2 ${
                      analysisResult.is_winning 
                        ? 'bg-green-500/10 border-green-500/30' 
                        : analysisResult.shanten <= 1 
                          ? 'bg-yellow-500/10 border-yellow-500/30'
                          : 'bg-green-500/10 border-blue-500/30'
                    }`}>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="text-3xl">
                            {analysisResult.is_winning ? '🏆' : analysisResult.shanten <= 1 ? '🎯' : '📈'}
                          </div>
                          <div>
                            <div className="text-gray-800 font-semibold text-lg">
                              {analysisResult.is_winning ? '恭喜胡牌！' : `${analysisResult.shanten}向听`}
                            </div>
                            <div className="text-gray-600 text-sm">
                              {analysisResult.is_winning 
                                ? '手牌已达成胡牌条件' 
                                : `距离胡牌还需 ${analysisResult.shanten} 步`}
                            </div>
                          </div>
                        </div>
                        {!analysisResult.is_winning && (
                          <div className="text-right">
                            <div className="text-2xl font-bold text-gray-800">
                              {analysisResult.effective_draws?.length || 0}
                            </div>
                            <div className="text-xs text-gray-600">种进张</div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* 进张效率指示器 */}
                    {!analysisResult.is_winning && (analysisResult.effective_draws?.length || 0) > 0 && (
                      <div className="bg-gray-100/80 rounded-lg p-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-gray-700">进张效率</span>
                          <span className="text-xs text-gray-600">
                            {analysisResult.effective_draws?.length || 0}/27 种
                          </span>
                        </div>
                        <div className="w-full bg-gray-300 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full transition-all duration-500 ${
                              (analysisResult.effective_draws?.length || 0) >= 15 
                                ? 'bg-green-500' 
                                : (analysisResult.effective_draws?.length || 0) >= 8
                                  ? 'bg-yellow-500'
                                  : 'bg-red-500'
                            }`}
                            style={{ 
                              width: `${Math.min(((analysisResult.effective_draws?.length || 0) / 27) * 100, 100)}%` 
                            }}
                          ></div>
                        </div>
                        <div className="mt-1 text-xs text-gray-600">
                          {(analysisResult.effective_draws?.length || 0) >= 15 
                            ? '⚡ 进张丰富，发展良好' 
                            : (analysisResult.effective_draws?.length || 0) >= 8
                              ? '📊 进张适中，继续优化'
                              : '⚠️ 进张较少，需要调整'}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* 胡牌张或有效进张 */}
                  {analysisResult.is_winning ? (
                    <div className="mb-6">
                      <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                        <h3 className="text-green-700 mb-3 text-sm font-medium flex items-center">
                          🎊 恭喜！可胡牌张:
                          <span className="ml-2 px-2 py-1 bg-green-500/20 rounded text-xs">
                            {analysisResult.winning_tiles?.length || 0}种
                          </span>
                        </h3>
                        <div className="flex flex-wrap gap-2">
                          {analysisResult.winning_tiles?.map((tile, index) => (
                            <motion.div
                              key={`winning-${index}`}
                              initial={{ scale: 0, rotate: 180 }}
                              animate={{ scale: 1, rotate: 0 }}
                              transition={{ delay: index * 0.1 }}
                            >
                              <MahjongTile
                                tile={tile}
                                size="tiny"
                                variant="recommended"
                                className="opacity-90 shadow-lg hover:scale-110 transition-transform"
                              />
                            </motion.div>
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : (
                    analysisResult.effective_draws && analysisResult.effective_draws.length > 0 && (
                      <div className="mb-6">
                        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4">
                          <h3 className="text-emerald-700 mb-3 text-sm font-medium flex items-center justify-between">
                            <span className="flex items-center">
                              ⚡ 有效进张:
                              <span className="ml-2 px-2 py-1 bg-emerald-500/20 rounded text-xs">
                                {analysisResult.effective_draws.length}种
                              </span>
                            </span>
                            {analysisResult.effective_draws.length > 9 && (
                              <button 
                                className="text-xs text-emerald-600 hover:text-emerald-700 transition-colors"
                                onClick={() => {/* TODO: 展开所有进张 */}}
                              >
                                查看全部
                              </button>
                            )}
                          </h3>
                          <div className="flex flex-wrap gap-1">
                            {analysisResult.effective_draws.slice(0, 9).map((tile, index) => {
                              console.log('Effective draw tile:', tile); // 调试信息
                              return (
                                <motion.div
                                  key={`effective-${index}`}
                                  initial={{ opacity: 0, y: 10 }}
                                  animate={{ opacity: 1, y: 0 }}
                                  transition={{ delay: index * 0.05 }}
                                >
                                  <MahjongTile
                                    tile={tile}
                                    size="tiny"
                                    variant="default"
                                    className="opacity-90 hover:scale-110 transition-transform"
                                  />
                                </motion.div>
                              );
                            }
                            ))}
                            {analysisResult.effective_draws.length > 9 && (
                              <div className="flex items-center justify-center w-8 h-10 bg-gray-600/30 rounded text-gray-400 text-xs">
                                +{analysisResult.effective_draws.length - 9}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  )}

                  {/* AI分析建议 */}
                  {analysisResult.detailed_analysis?.suggestions && analysisResult.detailed_analysis.suggestions.length > 0 && (
                    <div className="bg-teal-500/10 border border-teal-500/30 rounded-lg p-4">
                      <h3 className="text-teal-700 mb-3 text-sm font-medium flex items-center">
                        🤖 AI智能建议
                        <span className="ml-2 w-2 h-2 bg-teal-500 rounded-full animate-pulse"></span>
                      </h3>
                      <div className="space-y-2">
                        {analysisResult.detailed_analysis.suggestions.slice(0, 4).map((suggestion, index) => (
                          <motion.div
                            key={index}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.1 }}
                            className="flex items-start space-x-2 text-sm"
                          >
                            <div className="w-5 h-5 rounded-full bg-teal-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                              <span className="text-xs text-teal-700">{index + 1}</span>
                            </div>
                            <div className="text-gray-700 leading-relaxed">
                              {suggestion}
                            </div>
                          </motion.div>
                        ))}
                      </div>
                      
                      {/* 额外分析信息 */}
                      {analysisResult.detailed_analysis.patterns && analysisResult.detailed_analysis.patterns.length > 0 && (
                        <div className="mt-4 pt-3 border-t border-teal-500/20">
                          <div className="text-xs text-teal-700 mb-2">🔍 牌型特征:</div>
                          <div className="flex flex-wrap gap-1">
                            {analysisResult.detailed_analysis.patterns.slice(0, 3).map((pattern, index) => (
                              <span
                                key={index}
                                className="px-2 py-1 bg-teal-500/20 text-teal-700 rounded text-xs"
                              >
                                {pattern}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>

        {/* 底部信息和快捷键 */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-8 space-y-4"
        >
          {/* 快捷键提示 */}
          <div className="bg-white/80 rounded-lg p-4 mx-auto max-w-4xl shadow-md border border-gray-200">
            <h3 className="text-gray-800 text-sm font-medium mb-3 text-center">⌨️ 快捷键操作</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
              <div className="flex items-center justify-center space-x-2 text-green-700">
                <kbd className="px-2 py-1 bg-gray-200 rounded shadow-sm">Enter</kbd>
                <span>分析手牌</span>
              </div>
              <div className="flex items-center justify-center space-x-2 text-yellow-700">
                <kbd className="px-2 py-1 bg-gray-200 rounded shadow-sm">S</kbd>
                <span>重新排序</span>
              </div>
              <div className="flex items-center justify-center space-x-2 text-red-700">
                <kbd className="px-2 py-1 bg-gray-200 rounded shadow-sm">C</kbd>
                <span>清空手牌</span>
              </div>
              <div className="flex items-center justify-center space-x-2 text-purple-700">
                <kbd className="px-2 py-1 bg-gray-200 rounded shadow-sm">Esc</kbd>
                <span>关闭结果</span>
              </div>
            </div>
            <div className="mt-2 text-center text-gray-600 text-xs">
              💡 提示：右键点击牌池中的牌可快速添加多张 • 点击手牌可移除
            </div>
          </div>
          
          {/* 系统信息 */}
          <div className="text-center text-gray-600/80 text-sm">
            ⚡ 基于27位数组算法 | 🎯 专业级向听数计算 | 🧠 AI智能建议 | 🔧 实时排序优化
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default HandAnalyzer;