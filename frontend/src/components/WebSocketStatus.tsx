import React from 'react';
import { ConnectionStatus } from '../services/WebSocketClient';

interface WebSocketStatusProps {
  status: ConnectionStatus;
  reconnectAttempts?: number;
  lastError?: string | null;
  className?: string;
}

const statusConfig = {
  [ConnectionStatus.DISCONNECTED]: {
    color: 'text-gray-500',
    bgColor: 'bg-gray-100',
    icon: '⚫',
    text: '未连接',
    description: 'WebSocket未连接'
  },
  [ConnectionStatus.CONNECTING]: {
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-100',
    icon: '🟡',
    text: '连接中',
    description: '正在建立WebSocket连接...'
  },
  [ConnectionStatus.CONNECTED]: {
    color: 'text-green-600',
    bgColor: 'bg-green-100',
    icon: '🟢',
    text: '已连接',
    description: 'WebSocket连接正常'
  },
  [ConnectionStatus.RECONNECTING]: {
    color: 'text-orange-600',
    bgColor: 'bg-orange-100',
    icon: '🔄',
    text: '重连中',
    description: '正在尝试重新连接...'
  },
  [ConnectionStatus.ERROR]: {
    color: 'text-red-600',
    bgColor: 'bg-red-100',
    icon: '🔴',
    text: '连接错误',
    description: '连接出现问题'
  }
};

export const WebSocketStatus: React.FC<WebSocketStatusProps> = ({
  status,
  reconnectAttempts = 0,
  lastError,
  className = ''
}) => {
  const config = statusConfig[status];
  
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div 
        className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium ${config.color} ${config.bgColor}`}
        title={config.description + (lastError ? ` (${lastError})` : '')}
      >
        <span className="text-sm">{config.icon}</span>
        <span>{config.text}</span>
        {status === ConnectionStatus.RECONNECTING && reconnectAttempts > 0 && (
          <span className="text-xs opacity-75">({reconnectAttempts})</span>
        )}
      </div>
      
      {lastError && status === ConnectionStatus.ERROR && (
        <div className="text-xs text-red-500 max-w-xs truncate" title={lastError}>
          {lastError}
        </div>
      )}
    </div>
  );
};