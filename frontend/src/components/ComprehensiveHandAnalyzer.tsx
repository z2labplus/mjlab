import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Tile, TileType, tilesToMpsString, mpsStringToTile, tileToString } from '../types/mahjong';
import { ComprehensiveAnalysisRequest, ComprehensiveAnalysisResponse, ComprehensiveAnalysisResult } from '../types/mahjong';
import MahjongTile from './MahjongTile';

interface ComprehensiveHandAnalyzerProps {
  className?: string;
}

interface AnalysisHistory {
  id: string;
  hand: string;
  handDisplay: string;
  timestamp: string;
  results: ComprehensiveAnalysisResult[];
  comparison?: any;
}

const ComprehensiveHandAnalyzer: React.FC<ComprehensiveHandAnalyzerProps> = ({ className }) => {
  const [selectedTiles, setSelectedTiles] = useState<Tile[]>([]);
  const [selectedMethods, setSelectedMethods] = useState<Array<'tenhou_website' | 'local_simulation' | 'exhaustive'>>(['local_simulation']);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisHistory, setAnalysisHistory] = useState<AnalysisHistory[]>([]);

  // 生成所有可能的麻将牌（万、条、筒）
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
      return;
    }
    
    const existingCount = selectedTiles.filter(t => 
      t.type === tile.type && t.value === tile.value
    ).length;
    
    if (existingCount >= 4) {
      return;
    }
    
    setSelectedTiles([...selectedTiles, tile]);
  };

  // 移除牌
  const removeTile = (index: number) => {
    const newTiles = [...selectedTiles];
    newTiles.splice(index, 1);
    setSelectedTiles(newTiles);
  };

  // 清空手牌
  const clearHand = () => {
    setSelectedTiles([]);
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
      return a.value - b.value;
    });
  };

  // 预设手牌示例
  const setPresetHand = (preset: string) => {
    let tiles: Tile[] = [];
    
    switch (preset) {
      case 'test1':
        // 测试手牌1：13m24p1578889s232z
        tiles = [
          { type: TileType.WAN, value: 1 },
          { type: TileType.WAN, value: 3 },
          { type: TileType.TONG, value: 2 },
          { type: TileType.TONG, value: 4 },
          { type: TileType.TIAO, value: 1 },
          { type: TileType.TIAO, value: 5 },
          { type: TileType.TIAO, value: 7 },
          { type: TileType.TIAO, value: 8 },
          { type: TileType.TIAO, value: 8 },
          { type: TileType.TIAO, value: 8 },
          { type: TileType.TIAO, value: 9 },
          { type: TileType.ZI, value: 2 },
          { type: TileType.ZI, value: 3 },
          { type: TileType.ZI, value: 2 }
        ];
        break;
      case 'test2':
        // 测试手牌2：1245589m1244588s
        const tiles2 = mpsStringToTileArray('1245589m1244588s');
        tiles = tiles2;
        break;
      case 'test3':
        // 测试手牌3：2233456m4456778s
        const tiles3 = mpsStringToTileArray('2233456m4456778s');
        tiles = tiles3;
        break;
      default:
        tiles = [];
    }
    
    setSelectedTiles(tiles);
  };

  // 将mps字符串转换为Tile数组
  const mpsStringToTileArray = (mpsString: string): Tile[] => {
    const tiles: Tile[] = [];
    let currentNumbers = '';
    
    for (const char of mpsString) {
      if (/\d/.test(char)) {
        currentNumbers += char;
      } else if (['m', 'p', 's', 'z'].includes(char)) {
        for (const numChar of currentNumbers) {
          const tile = mpsStringToTile(numChar + char);
          tiles.push(tile);
        }
        currentNumbers = '';
      }
    }
    
    return tiles;
  };

  // 分析方法选择
  const toggleMethod = (method: 'tenhou_website' | 'local_simulation' | 'exhaustive') => {
    setSelectedMethods(prev => {
      if (prev.includes(method)) {
        return prev.filter(m => m !== method);
      } else {
        return [...prev, method];
      }
    });
  };

  // 综合分析手牌
  const analyzeHand = async () => {
    if (selectedTiles.length === 0 || selectedMethods.length === 0) {
      return;
    }

    setIsAnalyzing(true);
    
    try {
      const sortedTiles = sortTiles(selectedTiles);
      const handMps = tilesToMpsString(sortedTiles);
      
      const request: ComprehensiveAnalysisRequest = {
        hand: handMps,
        methods: selectedMethods,
        tile_format: 'mps'
      };

      const response = await fetch('http://localhost:8000/api/mahjong/comprehensive-analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (response.ok) {
        const result: ComprehensiveAnalysisResponse = await response.json();
        
        // 添加到分析历史
        const historyItem: AnalysisHistory = {
          id: Date.now().toString(),
          hand: result.hand,
          handDisplay: result.hand_display,
          timestamp: new Date().toLocaleTimeString(),
          results: result.results,
          comparison: result.comparison
        };
        
        setAnalysisHistory(prev => [historyItem, ...prev.slice(0, 4)]); // 保留最近5个分析结果
        
        // 显示分析结果摘要
        const successCount = result.results.filter(r => r.success).length;
        const totalCount = result.results.length;
        console.log(`✅ 分析完成: ${successCount}/${totalCount} 种方法成功`);
        
        // 如果有失败的方法，显示警告
        const failedMethods = result.results.filter(r => !r.success);
        if (failedMethods.length > 0) {
          failedMethods.forEach(method => {
            console.warn(`⚠️ ${method.method_name} 分析失败: ${method.error_message}`);
          });
        }
      } else {
        const errorText = await response.text();
        console.error('分析失败:', errorText);
        alert(`分析失败: ${errorText}`);
      }
    } catch (error) {
      console.error('分析错误:', error);
    }
    
    setIsAnalyzing(false);
  };

  // 清除分析历史
  const clearHistory = () => {
    setAnalysisHistory([]);
  };

  // 方法名称映射
  const methodNames = {
    'tenhou_website': '🌐 天凤网站',
    'local_simulation': '🏠 本地模拟天凤',
    'exhaustive': '🔢 穷举算法'
  };

  // 方法描述映射
  const methodDescriptions = {
    'tenhou_website': '真实权威结果，需要网络连接',
    'local_simulation': '快速本地分析，推荐首选',
    'exhaustive': '纯数学计算，逻辑透明'
  };

  return (
    <div className={`min-h-screen bg-gradient-to-br from-blue-50 to-purple-100 ${className}`}>
      {/* 背景装饰 */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-72 h-72 bg-blue-500/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-500/5 rounded-full blur-3xl"></div>
      </div>

      <div className="relative z-10 container mx-auto p-6">
        <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
          
          {/* 左侧：牌池选择区 */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="xl:col-span-1"
          >
            <div className="bg-white/90 backdrop-filter backdrop-blur-lg rounded-2xl border border-gray-200 p-6 shadow-lg">
              <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
                <span className="w-2 h-2 bg-blue-400 rounded-full mr-3"></span>
                选择手牌
              </h2>
              
              {/* 预设手牌按钮 */}
              <div className="mb-6 space-y-2">
                <div className="text-sm text-gray-600 mb-2">测试手牌：</div>
                <div className="flex flex-col gap-2">
                  <button
                    onClick={() => setPresetHand('test1')}
                    className="px-3 py-2 bg-blue-500/20 text-blue-700 rounded-lg hover:bg-blue-500/30 transition-all duration-200 text-sm"
                  >
                    📋 测试1 (13m24p1578889s232z)
                  </button>
                  <button
                    onClick={() => setPresetHand('test2')}
                    className="px-3 py-2 bg-green-500/20 text-green-700 rounded-lg hover:bg-green-500/30 transition-all duration-200 text-sm"
                  >
                    📋 测试2 (1245589m1244588s)
                  </button>
                  <button
                    onClick={() => setPresetHand('test3')}
                    className="px-3 py-2 bg-purple-500/20 text-purple-700 rounded-lg hover:bg-purple-500/30 transition-all duration-200 text-sm"
                  >
                    📋 测试3 (2233456m4456778s)
                  </button>
                  <button
                    onClick={clearHand}
                    className="px-3 py-2 bg-red-500/20 text-red-700 rounded-lg hover:bg-red-500/30 transition-all duration-200 text-sm"
                  >
                    🗑️ 清空
                  </button>
                </div>
              </div>

              {/* 牌池 */}
              <div className="space-y-4">
                {/* 万子 */}
                <div>
                  <h3 className="text-gray-800 mb-2 text-sm font-medium">万子</h3>
                  <div className="flex flex-wrap gap-2">
                    {allTiles.filter(t => t.type === TileType.WAN).map((tile, index) => (
                      <div key={`wan-${index}`} className="relative">
                        <motion.div
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                        >
                          <MahjongTile
                            tile={tile}
                            size="small"
                            onClick={() => addTile(tile)}
                            className={`cursor-pointer transition-all duration-200 ${
                              getTileCount(tile) >= 4 
                                ? 'opacity-30 cursor-not-allowed' 
                                : 'opacity-80 hover:opacity-100 hover:shadow-lg'
                            }`}
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
                  <h3 className="text-gray-800 mb-2 text-sm font-medium">条子</h3>
                  <div className="flex flex-wrap gap-2">
                    {allTiles.filter(t => t.type === TileType.TIAO).map((tile, index) => (
                      <div key={`tiao-${index}`} className="relative">
                        <motion.div
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                        >
                          <MahjongTile
                            tile={tile}
                            size="small"
                            onClick={() => addTile(tile)}
                            className={`cursor-pointer transition-all duration-200 ${
                              getTileCount(tile) >= 4 
                                ? 'opacity-30 cursor-not-allowed' 
                                : 'opacity-80 hover:opacity-100 hover:shadow-lg'
                            }`}
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
                  <h3 className="text-gray-800 mb-2 text-sm font-medium">筒子</h3>
                  <div className="flex flex-wrap gap-2">
                    {allTiles.filter(t => t.type === TileType.TONG).map((tile, index) => (
                      <div key={`tong-${index}`} className="relative">
                        <motion.div
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                        >
                          <MahjongTile
                            tile={tile}
                            size="small"
                            onClick={() => addTile(tile)}
                            className={`cursor-pointer transition-all duration-200 ${
                              getTileCount(tile) >= 4 
                                ? 'opacity-30 cursor-not-allowed' 
                                : 'opacity-80 hover:opacity-100 hover:shadow-lg'
                            }`}
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

          {/* 中间：当前手牌和分析方法选择 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="xl:col-span-1"
          >
            <div className="space-y-6">
              {/* 当前手牌 */}
              <div className="bg-white/90 backdrop-filter backdrop-blur-lg rounded-2xl border border-gray-200 p-6 shadow-lg">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-gray-800 flex items-center">
                    <span className="w-2 h-2 bg-blue-400 rounded-full mr-3"></span>
                    当前手牌
                  </h2>
                  <span className="text-sm text-gray-600">
                    {selectedTiles.length}/14张
                  </span>
                </div>
                
                <div className="min-h-[100px] bg-black/10 rounded-lg p-4 mb-4">
                  {selectedTiles.length === 0 ? (
                    <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                      <div className="text-center">
                        <div className="text-2xl mb-2">🀄</div>
                        <div>请选择麻将牌组成手牌</div>
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-wrap gap-1">
                      {sortTiles(selectedTiles).map((tile, index) => (
                        <motion.div
                          key={`tile-${index}`}
                          initial={{ opacity: 0, scale: 0.8 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.8 }}
                          whileHover={{ scale: 1.05 }}
                        >
                          <MahjongTile
                            tile={tile}
                            size="small"
                            onClick={() => removeTile(index)}
                            className="cursor-pointer hover:opacity-70 transition-all duration-200 shadow-md hover:shadow-lg"
                          />
                        </motion.div>
                      ))}
                    </div>
                  )}
                </div>

                {/* 手牌统计 */}
                {selectedTiles.length > 0 && (
                  <div className="text-xs text-gray-600 bg-gray-100/80 rounded p-2">
                    MPS格式: {tilesToMpsString(sortTiles(selectedTiles))}
                  </div>
                )}
              </div>

              {/* 分析方法选择 */}
              <div className="bg-white/90 backdrop-filter backdrop-blur-lg rounded-2xl border border-gray-200 p-6 shadow-lg">
                <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
                  <span className="w-2 h-2 bg-purple-400 rounded-full mr-3"></span>
                  分析方法
                </h2>

                <div className="space-y-3">
                  {Object.entries(methodNames).map(([method, name]) => (
                    <label key={method} className="flex items-start cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedMethods.includes(method as any)}
                        onChange={() => toggleMethod(method as any)}
                        className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 mt-0.5"
                      />
                      <div className="ml-3 flex-1">
                        <div className="text-sm text-gray-700 font-medium">{name}</div>
                        <div className="text-xs text-gray-500 mt-0.5">
                          {methodDescriptions[method as keyof typeof methodDescriptions]}
                        </div>
                      </div>
                    </label>
                  ))}
                </div>

                {/* 使用建议 */}
                <div className="mt-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="text-xs text-gray-700">
                    <div className="font-medium mb-1">💡 使用建议:</div>
                    <div className="text-gray-600">
                      • 首次使用推荐选择"本地模拟天凤"<br />
                      • 天凤网站分析可能需要较长时间<br />
                      • 多选可进行方法对比分析
                    </div>
                  </div>
                </div>

                {/* 分析按钮 */}
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={analyzeHand}
                  disabled={selectedTiles.length === 0 || selectedMethods.length === 0 || isAnalyzing}
                  className="w-full mt-6 py-3 px-6 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:from-blue-600 hover:to-purple-600 transition-all duration-200 flex items-center justify-center shadow-lg"
                >
                  {isAnalyzing ? (
                    <>
                      <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                      分析中...
                    </>
                  ) : (
                    <>
                      🔄 开始综合分析
                      <span className="ml-2 text-xs opacity-75">({selectedMethods.length}种方法)</span>
                    </>
                  )}
                </motion.button>
              </div>
            </div>
          </motion.div>

          {/* 右侧：分析结果历史和对比 */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="xl:col-span-2"
          >
            <div className="bg-white/90 backdrop-filter backdrop-blur-lg rounded-2xl border border-gray-200 p-6 shadow-lg">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-800 flex items-center">
                  <span className="w-2 h-2 bg-green-400 rounded-full mr-3"></span>
                  分析结果对比
                </h2>
                {analysisHistory.length > 0 && (
                  <button
                    onClick={clearHistory}
                    className="px-3 py-1 bg-red-500/20 text-red-600 rounded-md hover:bg-red-500/30 transition-all duration-200 text-sm"
                  >
                    清除历史
                  </button>
                )}
              </div>

              {analysisHistory.length === 0 ? (
                <div className="flex items-center justify-center h-40 text-gray-400">
                  <div className="text-center">
                    <div className="text-3xl mb-2">📊</div>
                    <div>暂无分析结果</div>
                    <div className="text-xs mt-1">选择手牌和分析方法后点击分析</div>
                  </div>
                </div>
              ) : (
                <div className="space-y-6 max-h-[800px] overflow-y-auto">
                  {analysisHistory.map((history) => (
                    <motion.div
                      key={history.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="border border-gray-200 rounded-xl p-4 bg-gray-50/50"
                    >
                      {/* 分析结果标题 */}
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <div className="font-medium text-gray-800">
                            手牌: {history.handDisplay}
                          </div>
                          <div className="text-xs text-gray-600">
                            时间: {history.timestamp} | MPS: {history.hand}
                          </div>
                        </div>
                      </div>

                      {/* 各方法结果 */}
                      <div className="space-y-4">
                        {history.results.map((result, index) => (
                          <div key={index} className={`p-3 rounded-lg ${
                            result.success 
                              ? 'bg-green-50 border border-green-200' 
                              : 'bg-red-50 border border-red-200'
                          }`}>
                            <div className="flex items-center justify-between mb-2">
                              <div className="font-medium text-gray-800">
                                {result.method_name}
                              </div>
                              <div className="text-xs text-gray-600">
                                {result.analysis_time.toFixed(3)}s
                              </div>
                            </div>

                            {result.success ? (
                              <div className="space-y-2">
                                {result.choices.slice(0, 4).map((choice, choiceIndex) => (
                                  <div key={choiceIndex} className="flex items-center justify-between text-sm">
                                    <span className="font-medium">
                                      {choiceIndex + 1}. 打{choice.tile}
                                    </span>
                                    <span className="text-gray-600">
                                      {choice.number}枚 [{choice.tiles.slice(0, 6).join(', ')}{choice.tiles.length > 6 ? '...' : ''}]
                                    </span>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="text-red-600 text-sm">
                                ❌ {result.error_message}
                              </div>
                            )}
                          </div>
                        ))}

                        {/* 对比分析 */}
                        {history.comparison && (
                          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                            <div className="text-sm text-blue-800 font-medium mb-2">📊 对比分析</div>
                            <div className="grid grid-cols-2 gap-4 text-xs">
                              <div>
                                <div className="text-blue-700 mb-1">成功率:</div>
                                {Object.entries(history.comparison.success_rate).map(([method, success]) => (
                                  <div key={method} className="text-gray-600">
                                    {method}: {success ? '✅' : '❌'}
                                  </div>
                                ))}
                              </div>
                              <div>
                                <div className="text-blue-700 mb-1">性能:</div>
                                {Object.entries(history.comparison.performance).map(([method, time]) => (
                                  <div key={method} className="text-gray-600">
                                    {`${method}: ${time}`}
                                  </div>
                                ))}
                              </div>
                            </div>
                            {history.comparison.choice_consistency && (
                              <div className="mt-2 text-xs text-blue-700">
                                选择一致性: {history.comparison.choice_consistency.match_rate} ({history.comparison.choice_consistency.percentage})
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default ComprehensiveHandAnalyzer;