import React from 'react';
import { useGameStore } from '../stores/gameStore';
import { useWebSocketGameStore } from '../stores/webSocketGameStore';
import { WebSocketStatus } from './WebSocketStatus';

interface ConnectionStatusProps {
  useWebSocket?: boolean;
}

const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ useWebSocket = false }) => {
  const { isApiConnected, lastSyncTime } = useGameStore();
  const { 
    connectionStatus, 
    isConnected, 
    reconnectAttempts, 
    lastError,
    lastSyncTime: wsLastSyncTime 
  } = useWebSocketGameStore();
  
  // 选择使用的连接状态和同步时间
  const isCurrentConnected = useWebSocket ? isConnected : isApiConnected;
  const currentLastSyncTime = useWebSocket ? wsLastSyncTime : lastSyncTime;

  const formatLastSync = (date: Date | null) => {
    if (!date) return '未同步';
    
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const seconds = Math.floor(diff / 1000);
    
    if (seconds < 60) return `${seconds}秒前`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}分钟前`;
    const hours = Math.floor(minutes / 60);
    return `${hours}小时前`;
  };

  return (
    <div className="fixed top-4 right-4 z-50">
      {useWebSocket ? (
        <div className="flex items-center gap-3 px-3 py-2 bg-white rounded-lg shadow-md border">
          <WebSocketStatus 
            status={connectionStatus}
            reconnectAttempts={reconnectAttempts}
            lastError={lastError}
          />
          
          {/* 最后同步时间 */}
          {currentLastSyncTime && (
            <span className="text-xs text-gray-500">
              · {formatLastSync(currentLastSyncTime)}
            </span>
          )}
        </div>
      ) : (
        <div 
          className={`flex items-center gap-2 px-3 py-2 rounded-lg shadow-md text-sm font-medium transition-all duration-300 ${
            isCurrentConnected 
              ? 'bg-green-100 text-green-700 border border-green-200' 
              : 'bg-red-100 text-red-700 border border-red-200'
          }`}
        >
          {/* 连接状态指示灯 */}
          <div 
            className={`w-2 h-2 rounded-full transition-all duration-300 ${
              isCurrentConnected 
                ? 'bg-green-500 animate-pulse' 
                : 'bg-red-500'
            }`}
          />
          
          {/* 连接状态文字 */}
          <span>
            {isCurrentConnected ? '已连接' : '离线模式'}
          </span>
          
          {/* 最后同步时间 */}
          {currentLastSyncTime && (
            <span className="text-xs opacity-75">
              · {formatLastSync(currentLastSyncTime)}
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default ConnectionStatus; 