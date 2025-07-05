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

  // 生成所有可能的麻将牌
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
    
    try {
      // 转换为后端需要的格式
      const handData = {
        tiles: selectedTiles.map(tile => `${tile.value}${tile.type}`),
        melds: []
      };

      const response = await fetch('/api/mahjong/analyze-hand', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(handData),
      });

      if (response.ok) {
        const result = await response.json();
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

  return (
    <div className={`min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 ${className}`}>
      {/* 背景装饰 */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-72 h-72 bg-blue-500/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-cyan-500/5 rounded-full blur-3xl"></div>
      </div>

      <div className="relative z-10 container mx-auto p-6">
        {/* 标题区域 */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="text-4xl font-bold text-white mb-2">
            🎯 智能手牌分析器
          </h1>
          <p className="text-blue-200 text-lg">
            基于数学算法的专业麻将分析工具
          </p>
        </motion.div>

        {/* 主要内容区域 */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          
          {/* 左侧：牌池选择区 */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="xl:col-span-2"
          >
            <div className="bg-white/10 backdrop-filter backdrop-blur-lg rounded-2xl border border-white/20 p-6">
              <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
                <span className="w-2 h-2 bg-blue-400 rounded-full mr-3"></span>
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
                  className="px-4 py-2 bg-blue-500/20 text-blue-300 rounded-lg hover:bg-blue-500/30 transition-all duration-200 text-sm"
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
                  <h3 className="text-white mb-2 text-sm font-medium">万子</h3>
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
                            className="cursor-pointer opacity-80 hover:opacity-100 transition-opacity"
                          />
                        </motion.div>
                        {getTileCount(tile) > 0 && (
                          <div className="absolute -top-2 -right-2 w-5 h-5 bg-blue-500 text-white text-xs rounded-full flex items-center justify-center font-bold">
                            {getTileCount(tile)}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* 条子 */}
                <div>
                  <h3 className="text-white mb-2 text-sm font-medium">条子</h3>
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
                            className="cursor-pointer opacity-80 hover:opacity-100 transition-opacity"
                          />
                        </motion.div>
                        {getTileCount(tile) > 0 && (
                          <div className="absolute -top-2 -right-2 w-5 h-5 bg-blue-500 text-white text-xs rounded-full flex items-center justify-center font-bold">
                            {getTileCount(tile)}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* 筒子 */}
                <div>
                  <h3 className="text-white mb-2 text-sm font-medium">筒子</h3>
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
                            className="cursor-pointer opacity-80 hover:opacity-100 transition-opacity"
                          />
                        </motion.div>
                        {getTileCount(tile) > 0 && (
                          <div className="absolute -top-2 -right-2 w-5 h-5 bg-blue-500 text-white text-xs rounded-full flex items-center justify-center font-bold">
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
            className="space-y-6"
          >
            
            {/* 当前手牌 */}
            <div className="bg-white/10 backdrop-filter backdrop-blur-lg rounded-2xl border border-white/20 p-6">
              <h2 className="text-xl font-semibold text-white mb-4 flex items-center justify-between">
                <span className="flex items-center">
                  <span className="w-2 h-2 bg-green-400 rounded-full mr-3"></span>
                  当前手牌
                </span>
                <span className="text-sm text-blue-200">
                  {selectedTiles.length}/14张
                </span>
              </h2>
              
              <div className="min-h-[120px] bg-black/20 rounded-lg p-4 mb-4">
                <div className="flex flex-wrap gap-1">
                  <AnimatePresence>
                    {selectedTiles.map((tile, index) => (
                      <motion.div
                        key={`selected-${index}`}
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        whileHover={{ scale: 1.05 }}
                      >
                        <MahjongTile
                          tile={tile}
                          size="small"
                          onClick={() => removeTile(index)}
                          className="cursor-pointer hover:opacity-70 transition-opacity"
                        />
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              </div>

              {/* 分析按钮 */}
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={analyzeHand}
                disabled={selectedTiles.length === 0 || isAnalyzing}
                className="w-full py-3 px-6 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:from-blue-600 hover:to-purple-600 transition-all duration-200 flex items-center justify-center"
              >
                {isAnalyzing ? (
                  <>
                    <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                    分析中...
                  </>
                ) : (
                  <>
                    🧠 智能分析
                  </>
                )}
              </motion.button>
            </div>

            {/* 分析结果 */}
            <AnimatePresence>
              {analysisResult && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="bg-white/10 backdrop-filter backdrop-blur-lg rounded-2xl border border-white/20 p-6"
                >
                  <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
                    <span className="w-2 h-2 bg-yellow-400 rounded-full mr-3"></span>
                    分析结果
                  </h2>

                  {/* 基础状态 */}
                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="bg-black/20 rounded-lg p-3 text-center">
                      <div className="text-2xl mb-1">
                        {analysisResult.is_winning ? '🏆' : '🎯'}
                      </div>
                      <div className="text-white font-medium">
                        {analysisResult.is_winning ? '可胡牌' : `${analysisResult.shanten}向听`}
                      </div>
                    </div>
                    <div className="bg-black/20 rounded-lg p-3 text-center">
                      <div className="text-2xl mb-1">📊</div>
                      <div className="text-white font-medium">
                        {analysisResult.effective_draws?.length || 0}种进张
                      </div>
                    </div>
                  </div>

                  {/* 胡牌张或有效进张 */}
                  {analysisResult.is_winning ? (
                    <div className="mb-4">
                      <h3 className="text-white mb-2 text-sm font-medium">🎊 胡牌张:</h3>
                      <div className="flex flex-wrap gap-1">
                        {analysisResult.winning_tiles?.map((tile, index) => (
                          <MahjongTile
                            key={`winning-${index}`}
                            tile={tile}
                            size="tiny"
                            variant="recommended"
                            className="opacity-90"
                          />
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="mb-4">
                      <h3 className="text-white mb-2 text-sm font-medium">⚡ 有效进张:</h3>
                      <div className="flex flex-wrap gap-1">
                        {analysisResult.effective_draws?.slice(0, 12).map((tile, index) => (
                          <MahjongTile
                            key={`effective-${index}`}
                            tile={tile}
                            size="tiny"
                            className="opacity-90"
                          />
                        ))}
                        {analysisResult.effective_draws?.length > 12 && (
                          <div className="text-white text-xs self-center ml-2">
                            +{analysisResult.effective_draws.length - 12}种...
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* 详细建议 */}
                  {analysisResult.detailed_analysis?.suggestions && (
                    <div>
                      <h3 className="text-white mb-2 text-sm font-medium">💡 AI建议:</h3>
                      <div className="space-y-1">
                        {analysisResult.detailed_analysis.suggestions.slice(0, 3).map((suggestion, index) => (
                          <div key={index} className="text-blue-200 text-xs bg-black/20 rounded px-2 py-1">
                            {suggestion}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>

        {/* 底部信息 */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-8 text-center text-blue-200/60 text-sm"
        >
          ⚡ 基于27位数组算法 | 🎯 专业级向听数计算 | 🧠 AI智能建议
        </motion.div>
      </div>
    </div>
  );
};

export default HandAnalyzer;