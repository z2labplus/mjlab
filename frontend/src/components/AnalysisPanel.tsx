import React, { useState } from 'react';
import { useWebSocketGameStore } from '../stores/webSocketGameStore';
import { MahjongAPI } from '../utils/api';
import { codeToTile, TileType, AnalysisResult } from '../types/mahjong';
import MahjongTile from './MahjongTile';

interface AnalysisPanelProps {
  className?: string;
}

const AnalysisPanel: React.FC<AnalysisPanelProps> = ({ className }) => {
  const gameState = useWebSocketGameStore(state => state.gameState);
  const analysisResult = useWebSocketGameStore(state => state.analysisResult);
  const isAnalyzing = useWebSocketGameStore(state => state.isAnalyzing);
  const { setAnalysisResult, setIsAnalyzing } = useWebSocketGameStore();
  
  const [error, setError] = useState<string | null>(null);
  
  // 执行分析
  const handleAnalyze = async () => {
    const myHand = gameState.player_hands[0];
    if (!myHand || !myHand.tiles || myHand.tiles.length === 0) {
      setError('请先添加手牌');
      return;
    }
    
    setIsAnalyzing(true);
    setError(null);
    
    try {
      // 准备分析请求数据
      const handTiles = myHand.tiles.map(tile => `${tile.value}${tile.type === 'wan' ? '万' : tile.type === 'tiao' ? '条' : '筒'}`);
      
      // 收集可见牌（弃牌等）
      const visibleTiles: string[] = [];
      if (gameState.discarded_tiles) {
        gameState.discarded_tiles.forEach(tile => {
          visibleTiles.push(`${tile.value}${tile.type === 'wan' ? '万' : tile.type === 'tiao' ? '条' : '筒'}`);
        });
      }
      
      // 获取定缺信息
      const missingSuit = myHand.missing_suit || gameState.player_hands['0']?.missing_suit || 'tong';  // 默认定缺筒
      const missingSuitChinese = missingSuit === 'wan' ? '万' : missingSuit === 'tiao' ? '条' : '筒';
      
      // 调用血战到底分析API
      const response = await MahjongAPI.analyzeUltimate({
        hand_tiles: handTiles,
        visible_tiles: visibleTiles,
        missing_suit: missingSuitChinese
      });
      
      if (response.success && response.results) {
        // 构建弃牌分数对象
        const discardScores: { [key: string]: number } = {};
        response.results.forEach(result => {
          discardScores[result.discard_tile] = result.expected_value;
        });

        // 转换推荐弃牌为Tile类型
        const recommendedDiscard = response.results[0] ? {
          type: response.results[0].discard_tile.includes('万') ? TileType.WAN : 
                response.results[0].discard_tile.includes('条') ? TileType.TIAO : TileType.TONG,
          value: parseInt(response.results[0].discard_tile[0])
        } : undefined;

        // 转换为原有格式以保持兼容性
        const compatibleAnalysis: AnalysisResult = {
          win_probability: response.results[0]?.can_win ? 0.8 : 0.2,
          recommended_discard: recommendedDiscard,
          listen_tiles: [],
          suggestions: [
            `推荐打出：${response.results[0]?.discard_tile}（收益：${response.results[0]?.expected_value}）`,
            `进张：${response.results[0]?.jinzhang_types}种-${response.results[0]?.jinzhang_count}张`,
            response.results[0]?.jinzhang_detail || ''
          ],
          discard_scores: discardScores,
          remaining_tiles_count: {},
          ultimate_results: response.results  // 保存完整的血战到底分析结果
        };
        
        setAnalysisResult(compatibleAnalysis);
      } else {
        setError(response.message || '分析失败');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '分析失败');
    } finally {
      setIsAnalyzing(false);
    }
  };
  
  // 渲染剩余牌统计
  const renderRemainingTiles = () => {
    if (!analysisResult) return null;
    
    const remainingTiles = analysisResult.remaining_tiles_count;
    const tileGroups = {
      wan: [] as Array<{ code: number; count: number; tile: any }>,
      tiao: [] as Array<{ code: number; count: number; tile: any }>,
      tong: [] as Array<{ code: number; count: number; tile: any }>,
      zi: [] as Array<{ code: number; count: number; tile: any }>
    };
    
    // 分组整理剩余牌
    Object.entries(remainingTiles).forEach(([codeStr, count]) => {
      const code = parseInt(codeStr);
      if (count > 0) {
        const tile = codeToTile(code);
        const item = { code, count, tile };
        
        if (tile.type === TileType.WAN) {
          tileGroups.wan.push(item);
        } else if (tile.type === TileType.TIAO) {
          tileGroups.tiao.push(item);
        } else if (tile.type === TileType.TONG) {
          tileGroups.tong.push(item);
        } else if (tile.type === TileType.ZI) {
          tileGroups.zi.push(item);
        }
      }
    });
    
    return (
      <div className="space-y-4">
        {Object.entries(tileGroups).map(([type, tiles]) => {
          if (tiles.length === 0) return null;
          
          const typeNames = {
            wan: '万子',
            tiao: '条子',
            tong: '筒子',
            zi: '字牌'
          };
          
          return (
            <div key={type} className="bg-gray-50 rounded-lg p-3">
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                {typeNames[type as keyof typeof typeNames]}
              </h4>
              <div className="flex flex-wrap gap-2">
                {tiles.map(({ tile, count }) => (
                  <div key={tile.value} className="relative">
                    <MahjongTile tile={tile} size="small" variant="disabled" />
                    <div className="absolute -top-1 -right-1 bg-blue-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                      {count}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    );
  };
  
  // 渲染弃牌分析（与牌谱回放界面样式一致）
  const renderDiscardScores = () => {
    if (!analysisResult?.ultimate_results) return null;
    
    // 按收益从高到低排序
    const results = analysisResult.ultimate_results
      .sort((a, b) => b.expected_value - a.expected_value)
      .slice(0, 6); // 显示前6个，与牌谱回放一致
    
    return (
      <div className="space-y-3">
        {results.map((result, index) => (
          <div 
            key={result.discard_tile} 
            className={`p-3 rounded-lg border-2 transition-all duration-300 ${
              index === 0 ? 'border-green-400 bg-gradient-to-br from-green-50 to-green-100' :
              index === 1 ? 'border-blue-300 bg-gradient-to-br from-blue-50 to-blue-100' :
              index === 2 ? 'border-yellow-300 bg-gradient-to-br from-yellow-50 to-yellow-100' :
              'border-gray-300 bg-gradient-to-br from-gray-50 to-gray-100'
            }`}
          >
            {/* 第一行：弃牌和基本信息 */}
            <div className="flex items-center gap-2 mb-2">
              <div className="flex items-center gap-1">
                {(() => {
                  // 解析弃牌为Tile对象
                  const discardTile = {
                    type: result.discard_tile.includes('万') ? TileType.WAN : 
                          result.discard_tile.includes('条') ? TileType.TIAO : TileType.TONG,
                    value: parseInt(result.discard_tile[0])
                  };
                  
                  return (
                    <MahjongTile
                      tile={discardTile}
                      size="tiny"
                      variant="default"
                    />
                  );
                })()}
                <span className="text-sm font-bold text-gray-800">
                  {result.expected_value}-{result.jinzhang_types}种-{result.jinzhang_count}张 向听:{result.shanten}
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
              {result.jinzhang_detail ? (() => {
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
                
                const jinzhangTiles = parseJinzhangDetail(result.jinzhang_detail);
                
                return jinzhangTiles.length > 0 ? (
                  <div className="flex flex-wrap gap-1">
                    {jinzhangTiles.map((item, tileIndex) => (
                      <div key={`${item.tile.type}-${item.tile.value}-${tileIndex}`} className="relative">
                        <MahjongTile
                          tile={item.tile}
                          size="tiny"
                          variant="default"
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
          </div>
        ))}
      </div>
    );
  };
  
  return (
    <div className={`bg-white rounded-lg shadow-lg p-3 ${className}`}>
      {/* 标题和分析按钮 */}
      <div className="mb-3">
        <div className="flex justify-between items-center mb-3">
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-gray-800">🧠 智能分析</h3>
            <div className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded-full">
              实时分析
            </div>
          </div>
          <button
            onClick={handleAnalyze}
            disabled={isAnalyzing}
            className={`px-3 py-1.5 text-sm rounded-lg font-medium transition-all ${
              isAnalyzing
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-500 text-white hover:bg-blue-600'
            }`}
          >
            {isAnalyzing ? (
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
                分析中
              </div>
            ) : (
              '开始分析'
            )}
          </button>
        </div>
        
        {error && (
          <div className="bg-red-100 border border-red-300 text-red-700 px-3 py-2 rounded mb-3 text-sm">
            {error}
          </div>
        )}
      </div>
      
      {/* 分析结果 */}
      {analysisResult && (
        <div className="space-y-3">
          {/* 血战到底分析 */}
          <div className="bg-orange-50 rounded-lg p-3">
            <h4 className="text-sm font-semibold text-orange-800 mb-2">🎯 血战到底出牌分析</h4>
            {renderDiscardScores()}
          </div>
        </div>
      )}
      
      {/* 空状态 */}
      {!analysisResult && !isAnalyzing && (
        <div className="text-center py-8">
          <div className="text-4xl mb-2">🎯</div>
          <div className="text-sm text-gray-500">
            添加手牌后点击"开始分析"<br />
            获取专业的弃牌建议和胡牌概率
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalysisPanel; 