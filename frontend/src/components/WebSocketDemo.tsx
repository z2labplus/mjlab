import React, { useEffect, useState } from 'react';
import { useWebSocketGameStore } from '../stores/webSocketGameStore';
import ConnectionStatus from './ConnectionStatus';
import { Tile, TileType } from '../types/mahjong';

const WebSocketDemo: React.FC = () => {
  const {
    wsClient,
    connectionStatus,
    isConnected,
    gameState,
    lastError,
    isLoading,
    
    // 连接控制
    initWebSocket,
    connect,
    disconnect,
    
    // 游戏操作
    addTileToHand,
    discardTile,
    resetGame,
    setCurrentPlayer,
    nextPlayer,
    
    // 定缺操作
    setMissingSuit,
    getMissingSuits,
    
    // 牌谱操作
    exportGameRecord,
    importGameRecord,
    
    // 本地状态同步
    syncGameStateFromWS
  } = useWebSocketGameStore();
  
  const [missingSuits, setMissingSuitsState] = useState<Record<string, string | null>>({});
  
  // 初始化WebSocket
  useEffect(() => {
    const initWS = async () => {
      await initWebSocket();
    };
    initWS();
  }, [initWebSocket]);
  
  // 测试用的牌
  const testTile: Tile = { type: TileType.WAN, value: 1 };
  
  const handleConnect = async () => {
    try {
      await connect();
    } catch (error) {
      console.error('连接失败:', error);
    }
  };
  
  const handleDisconnect = () => {
    disconnect();
  };
  
  const handleAddTile = async () => {
    if (!isConnected) return;
    try {
      await addTileToHand(0, testTile);
    } catch (error) {
      console.error('添加手牌失败:', error);
    }
  };
  
  const handleDiscardTile = async () => {
    if (!isConnected) return;
    try {
      await discardTile(0, testTile);
    } catch (error) {
      console.error('弃牌失败:', error);
    }
  };
  
  const handleResetGame = async () => {
    if (!isConnected) return;
    try {
      await resetGame();
    } catch (error) {
      console.error('重置游戏失败:', error);
    }
  };
  
  const handleSetCurrentPlayer = async (playerId: number) => {
    if (!isConnected) return;
    try {
      await setCurrentPlayer(playerId);
    } catch (error) {
      console.error('设置当前玩家失败:', error);
    }
  };
  
  const handleNextPlayer = async () => {
    if (!isConnected) return;
    try {
      await nextPlayer();
    } catch (error) {
      console.error('切换下一个玩家失败:', error);
    }
  };
  
  const handleSetMissingSuit = async (playerId: number, suit: string) => {
    if (!isConnected) return;
    try {
      await setMissingSuit(playerId, suit);
      // 更新本地状态
      const suits = await getMissingSuits();
      setMissingSuitsState(suits);
    } catch (error) {
      console.error('设置定缺失败:', error);
    }
  };
  
  const handleGetMissingSuits = async () => {
    if (!isConnected) return;
    try {
      const suits = await getMissingSuits();
      setMissingSuitsState(suits);
    } catch (error) {
      console.error('获取定缺失败:', error);
    }
  };
  
  const handleExportRecord = async () => {
    if (!isConnected) return;
    try {
      const record = await exportGameRecord();
      console.log('导出的牌谱:', record);
      
      // 下载为JSON文件
      const blob = new Blob([JSON.stringify(record, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `mahjong_record_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('导出牌谱失败:', error);
    }
  };
  
  const handleSyncGameState = async () => {
    if (!isConnected) return;
    try {
      await syncGameStateFromWS();
    } catch (error) {
      console.error('同步游戏状态失败:', error);
    }
  };
  
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      {/* 连接状态 */}
      <ConnectionStatus useWebSocket={true} />
      
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">WebSocket 麻将游戏演示</h1>
          
          {/* 连接控制 */}
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-3">连接控制</h2>
            <div className="flex gap-3">
              <button
                onClick={handleConnect}
                disabled={isConnected || isLoading}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
              >
                {isLoading ? '连接中...' : '连接'}
              </button>
              <button
                onClick={handleDisconnect}
                disabled={!isConnected}
                className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
              >
                断开连接
              </button>
              <button
                onClick={handleSyncGameState}
                disabled={!isConnected}
                className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
              >
                同步状态
              </button>
            </div>
          </div>
          
          {/* 错误信息 */}
          {lastError && (
            <div className="mb-6 p-3 bg-red-100 border border-red-300 rounded text-red-700">
              <strong>错误:</strong> {lastError}
            </div>
          )}
          
          {/* 游戏操作 */}
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-3">游戏操作</h2>
            <div className="flex gap-3 flex-wrap">
              <button
                onClick={handleAddTile}
                disabled={!isConnected || isLoading}
                className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
              >
                添加手牌 (1万)
              </button>
              <button
                onClick={handleDiscardTile}
                disabled={!isConnected || isLoading}
                className="px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600 disabled:opacity-50"
              >
                弃牌 (1万)
              </button>
              <button
                onClick={handleResetGame}
                disabled={!isConnected || isLoading}
                className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50"
              >
                重置游戏
              </button>
              <button
                onClick={handleNextPlayer}
                disabled={!isConnected || isLoading}
                className="px-4 py-2 bg-indigo-500 text-white rounded hover:bg-indigo-600 disabled:opacity-50"
              >
                下一个玩家
              </button>
            </div>
          </div>
          
          {/* 当前玩家控制 */}
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-3">当前玩家控制</h2>
            <div className="flex gap-2">
              {[0, 1, 2, 3].map(playerId => (
                <button
                  key={playerId}
                  onClick={() => handleSetCurrentPlayer(playerId)}
                  disabled={!isConnected || isLoading}
                  className={`px-3 py-2 rounded text-white disabled:opacity-50 ${
                    gameState.current_player === playerId 
                      ? 'bg-blue-600' 
                      : 'bg-gray-500 hover:bg-gray-600'
                  }`}
                >
                  玩家 {playerId}
                </button>
              ))}
            </div>
          </div>
          
          {/* 定缺操作 */}
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-3">定缺操作</h2>
            <div className="space-y-3">
              <div className="flex gap-2">
                <button
                  onClick={() => handleSetMissingSuit(0, 'wan')}
                  disabled={!isConnected || isLoading}
                  className="px-3 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
                >
                  玩家0定万
                </button>
                <button
                  onClick={() => handleSetMissingSuit(0, 'tiao')}
                  disabled={!isConnected || isLoading}
                  className="px-3 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
                >
                  玩家0定条
                </button>
                <button
                  onClick={() => handleSetMissingSuit(0, 'tong')}
                  disabled={!isConnected || isLoading}
                  className="px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                >
                  玩家0定筒
                </button>
                <button
                  onClick={handleGetMissingSuits}
                  disabled={!isConnected || isLoading}
                  className="px-3 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 disabled:opacity-50"
                >
                  获取定缺
                </button>
              </div>
              
              {/* 显示定缺信息 */}
              {Object.keys(missingSuits).length > 0 && (
                <div className="p-3 bg-gray-100 rounded">
                  <div className="text-sm font-medium mb-1">当前定缺:</div>
                  {Object.entries(missingSuits).map(([playerId, suit]) => (
                    <div key={playerId} className="text-sm">
                      玩家{playerId}: {suit || '未定缺'}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          
          {/* 牌谱操作 */}
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-3">牌谱操作</h2>
            <div className="flex gap-3">
              <button
                onClick={handleExportRecord}
                disabled={!isConnected || isLoading}
                className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50"
              >
                导出牌谱
              </button>
            </div>
          </div>
          
          {/* 游戏状态显示 */}
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-3">游戏状态</h2>
            <div className="bg-gray-100 p-4 rounded text-sm">
              <div className="mb-2"><strong>游戏ID:</strong> {gameState.game_id}</div>
              <div className="mb-2"><strong>当前玩家:</strong> {gameState.current_player}</div>
              <div className="mb-2"><strong>游戏已开始:</strong> {gameState.game_started ? '是' : '否'}</div>
              
              {/* 玩家手牌信息 */}
              <div className="mt-4">
                <div className="font-medium mb-2">玩家手牌:</div>
                {Object.entries(gameState.player_hands).map(([playerId, hand]) => (
                  <div key={playerId} className="mb-1">
                    <strong>玩家{playerId}:</strong> 
                    {playerId === '0' ? (
                      ` ${(hand.tiles as any[])?.length || 0}张具体牌`
                    ) : (
                      ` ${hand.tile_count}张牌`
                    )}
                    {hand.melds.length > 0 && ` (${hand.melds.length}个面子)`}
                  </div>
                ))}
              </div>
              
              {/* 弃牌信息 */}
              <div className="mt-4">
                <div className="font-medium mb-2">弃牌数量:</div>
                {Object.entries(gameState.player_discarded_tiles).map(([playerId, tiles]) => (
                  <div key={playerId} className="mb-1">
                    <strong>玩家{playerId}:</strong> {tiles.length}张弃牌
                  </div>
                ))}
              </div>
              
              <div className="mt-4">
                <div className="font-medium mb-1">操作历史:</div>
                <div>{gameState.actions_history.length}个操作</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WebSocketDemo;