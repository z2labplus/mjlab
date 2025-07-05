import React, { useEffect, useState, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import GameBoard from './components/GameBoard';
import AnalysisPanel from './components/AnalysisPanel';
import SettingsPanel from './components/SettingsPanel';
import ReplaySystem from './components/ReplaySystem';
import HandAnalyzer from './components/HandAnalyzer';
import { useWebSocketGameStore } from './stores/webSocketGameStore';
import { useSettings } from './hooks/useSettings';

import { MahjongAPI } from './utils/api';
import './App.css';

// 玩家名称映射
const playerNames = {
  0: "我",
  1: "下家", 
  2: "对家",
  3: "上家"
};

// 花色名称映射
const suitNames = {
  wan: "万",
  tiao: "条",
  tong: "筒"
};

function App() {
  const { 
    initWebSocket, 
    connect, 
    isConnected, 
    connectionStatus, 
    setAvailableTiles, 
    gameState,
    checkForWinners,
    lastError
  } = useWebSocketGameStore();
  const { settings } = useSettings();
  const [showSettings, setShowSettings] = useState(false);
  const [currentMode, setCurrentMode] = useState<'live' | 'replay' | 'analyzer'>('live');
  
  // 胜利通知显示状态
  const [showWinNotification, setShowWinNotification] = useState(false);
  const [playerWinMessage, setPlayerWinMessage] = useState<any>(null);
  const [lastWinnerCheck, setLastWinnerCheck] = useState<string>('');
  const [displayedWinnerIndex, setDisplayedWinnerIndex] = useState<number>(0);
  const [notificationShown, setNotificationShown] = useState<boolean>(false);

  useEffect(() => {
    // 只在实时游戏模式下初始化WebSocket连接
    if (currentMode !== 'live') return;
    
    const initializeApp = async () => {
      try {
        console.log('🔗 初始化WebSocket连接...');
        
        // 初始化WebSocket客户端 - 使用与测试脚本相同的房间ID
        await initWebSocket('ws://localhost:8000/api/ws', 'test_room');
        
        // 连接到WebSocket服务器
        await connect();
        
        console.log('✅ WebSocket连接成功');
        
        // 获取麻将牌信息（如果需要的话）
        try {
          const tiles = await MahjongAPI.getTileCodes();
          setAvailableTiles(tiles);
        } catch (error) {
          console.warn('⚠️ 获取麻将牌信息失败，使用默认配置');
        }
      } catch (error) {
        console.error('❌ 初始化WebSocket连接失败:', error);
      }
    };

    initializeApp();
  }, [currentMode, initWebSocket, connect, setAvailableTiles]);

  // 定期同步游戏状态 - 只在实时游戏模式下进行
  useEffect(() => {
    if (currentMode !== 'live') return;
    
    const { syncGameStateFromAPI } = useWebSocketGameStore.getState();
    
    const syncAndCheckState = async () => {
      try {
        // 定期从API同步游戏状态
        await syncGameStateFromAPI();
        
        // // 检查胜利者
        // const winners = checkForWinners();
        
        // if (winners.length > 0) {
        //   // 生成所有胜利者的标识字符串
        //   const allWinnerIds = winners.map(w => `${w.player_id}-${w.win_type}`).join(',');
          
        //   // 如果胜利者列表发生变化，重置显示索引和通知状态
        //   if (allWinnerIds !== lastWinnerCheck) {
        //     setDisplayedWinnerIndex(0);
        //     setLastWinnerCheck(allWinnerIds);
        //     setNotificationShown(false); // 重置通知状态，允许显示新的通知
        //     console.log('🏆 检测到胜利者变化，重置显示:', winners);
        //   }
          
        //   // 只有在通知还未显示时才设置胜利者消息（避免重复触发计时器）
        //   if (!notificationShown) {
        //     const currentWinnerIndex = displayedWinnerIndex % winners.length;
        //     const currentWinner = winners[currentWinnerIndex];
            
        //     setPlayerWinMessage(currentWinner);
        //     setNotificationShown(true); // 标记通知已显示
        //     console.log(`🏆 显示胜利者 ${currentWinnerIndex + 1}/${winners.length}:`, currentWinner);
        //     console.log(`🏆 胜利详情: 玩家${currentWinner.player_id} ${currentWinner.win_type === 'zimo' ? '自摸' : '点炮胡牌'} ${currentWinner.win_tile ? `${currentWinner.win_tile.value}${suitNames[currentWinner.win_tile.type as keyof typeof suitNames]}` : ''}`);
        //   }
        // } else {
        //   // 如果没有胜利者了，清除状态
        //   if (lastWinnerCheck !== '') {
        //     setLastWinnerCheck('');
        //     setDisplayedWinnerIndex(0);
        //     setPlayerWinMessage(null);
        //     setNotificationShown(false);
        //     console.log('🏆 胜利者状态已清除');
        //   }
        // }
      } catch (error) {
        console.error('❌ 状态同步失败:', error);
      }
    };

    // 每1秒同步一次游戏状态和检查胜利状态
    const interval = setInterval(syncAndCheckState, 1000);
    
    return () => clearInterval(interval);
  }, [currentMode, checkForWinners, lastWinnerCheck]);

  // 处理玩家胜利消息
  useEffect(() => {
    if (playerWinMessage) {
      setShowWinNotification(true);
      console.log('🏆 显示胜利通知:', playerWinMessage);
      
      // 5秒后自动隐藏通知
      const timer = setTimeout(() => {
        setShowWinNotification(false);
        setPlayerWinMessage(null);
        setNotificationShown(false); // 重置通知状态，允许下次显示
        console.log('🏆 胜利通知已自动隐藏');
      }, 5000);
      
      return () => clearTimeout(timer);
    }
  }, [playerWinMessage]);

  // 手动关闭胜利通知
  const handleCloseWinNotification = () => {
    setShowWinNotification(false);
    setPlayerWinMessage(null);
    setNotificationShown(false); // 重置通知状态，允许下次显示
  };

  // 切换到下一个胜利者
  const handleNextWinner = () => {
    const winners = checkForWinners();
    if (winners.length > 1) {
      setDisplayedWinnerIndex((prev) => (prev + 1) % winners.length);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex flex-col">
      {/* 头部 - 紧凑版 */}
      <header className="bg-white shadow-sm border-b border-gray-200 flex-shrink-0">
        <div className="max-w-full mx-auto px-4 sm:px-6">
          <div className="flex justify-between items-center h-12">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-3"
            >
              <div className="text-2xl">🀅</div>
              <div>
                <h1 className="text-lg font-bold text-gray-900">
                  欢乐麻将辅助工具
                </h1>
                <p className="text-xs text-gray-500">
                  智能分析 · 精准建议 · 提升胜率
                </p>
              </div>
            </motion.div>
            
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-3"
            >
              {/* 模式切换 */}
              <div className="flex items-center gap-2 bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setCurrentMode('live')}
                  className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                    currentMode === 'live'
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-800'
                  }`}
                >
                  🎮 实时游戏
                </button>
                <button
                  onClick={() => setCurrentMode('replay')}
                  className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                    currentMode === 'replay'
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-800'
                  }`}
                >
                  🎬 牌谱回放
                </button>
                <button
                  onClick={() => setCurrentMode('analyzer')}
                  className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                    currentMode === 'analyzer'
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-800'
                  }`}
                >
                  🧠 手牌分析
                </button>
              </div>

              {currentMode === 'live' && (
                <div className="hidden sm:flex items-center gap-2 text-sm text-gray-600">
                  <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
                  <span>{isConnected ? 'WebSocket已连接' : 'WebSocket未连接'}</span>
                </div>
              )}
              
              <button 
                onClick={() => setShowSettings(true)}
                className="p-1.5 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                title="游戏设置"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </button>
            </motion.div>
          </div>
        </div>
      </header>

      {/* 主内容区 */}
      <main className="flex-1 flex overflow-hidden">
        {currentMode === 'live' ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="w-full h-full p-4"
          >
            <div className="grid grid-cols-1 xl:grid-cols-4 gap-6 h-full">
              {/* 左侧：游戏面板 - 占3列，与牌谱回放布局一致 */}
              <div className="xl:col-span-3 space-y-4">
                <GameBoard className="h-full" cardBackStyle={settings.cardBackStyle} />
              </div>

              {/* 右侧：分析面板 - 占1列，与牌谱回放布局一致 */}
              <div className="space-y-6">
                <AnalysisPanel className="h-full" />
              </div>
            </div>
          </motion.div>
        ) : currentMode === 'replay' ? (
          /* 回放模式 - 全屏显示 */
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="w-full h-full"
          >
            <ReplaySystem />
          </motion.div>
        ) : (
          /* 手牌分析模式 - 全屏显示 */
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="w-full h-full"
          >
            <HandAnalyzer />
          </motion.div>
        )}
      </main>

      {/* 底部信息 - 更紧凑 */}
      <footer className="bg-white border-t border-gray-200 flex-shrink-0">
        <div className="max-w-full mx-auto px-4 sm:px-6 py-2">
          <div className="flex justify-between items-center text-xs text-gray-600">
            <div className="flex items-center gap-3">
              <span>© 2024 欢乐麻将辅助工具</span>
              <span className="hidden sm:inline">|</span>
              <span className="hidden sm:inline">智能算法驱动</span>
            </div>
            
            <div className="flex items-center gap-3">
              <a 
                href="/docs" 
                className="hover:text-gray-900 transition-colors"
              >
                使用说明
              </a>
              <a 
                href="/api/docs" 
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-gray-900 transition-colors"
              >
                API文档
              </a>
            </div>
          </div>
        </div>
      </footer>

      {/* 设置面板 */}
      <SettingsPanel 
        isOpen={showSettings} 
        onClose={() => setShowSettings(false)} 
      />

      {/* 胜利通知 */}
      <AnimatePresence>
        {showWinNotification && playerWinMessage && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: -100 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: -100 }}
            transition={{ type: "spring", stiffness: 300, damping: 20 }}
            className="fixed top-20 left-1/2 transform -translate-x-1/2 z-50"
          >
            <div className="bg-gradient-to-r from-yellow-400 to-orange-500 text-white px-8 py-6 rounded-2xl shadow-2xl border-4 border-yellow-300 min-w-96">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="text-4xl animate-bounce">🎉</div>
                  <div>
                    <h3 className="text-xl font-bold mb-1">
                      {playerNames[playerWinMessage.player_id as keyof typeof playerNames]}胡牌！
                    </h3>
                    <div className="text-lg">
                      {playerWinMessage.win_type === 'zimo' ? (
                        <span className="flex items-center gap-2">
                          <span className="text-2xl">🙌</span>
                          自摸
                          {playerWinMessage.win_tile && (
                            <span className="bg-white text-orange-600 px-2 py-1 rounded-lg font-bold ml-1">
                              {playerWinMessage.win_tile.value}{suitNames[playerWinMessage.win_tile.type as keyof typeof suitNames]}
                            </span>
                          )}
                        </span>
                      ) : (
                        <span className="flex items-center gap-2">
                          <span className="text-2xl">🎯</span>
                          点炮胡牌
                          {playerWinMessage.win_tile && (
                            <span className="bg-white text-orange-600 px-2 py-1 rounded-lg font-bold ml-1">
                              {playerWinMessage.win_tile.value}{suitNames[playerWinMessage.win_tile.type as keyof typeof suitNames]}
                            </span>
                          )}
                          {playerWinMessage.dianpao_player_id !== undefined && (
                            <span className="text-sm">
                              (点炮者: {playerNames[playerWinMessage.dianpao_player_id as keyof typeof playerNames]})
                            </span>
                          )}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                
                <button 
                  onClick={handleCloseWinNotification}
                  className="text-white hover:text-yellow-200 transition-colors ml-4"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>


    </div>
  );
}

export default App; 