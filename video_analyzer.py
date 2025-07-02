#!/usr/bin/env python3
"""
腾讯欢乐麻将录像分析器
从录像视频中提取牌谱数据
"""

import cv2
import numpy as np
import json
import time
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
import pytesseract
from pathlib import Path

@dataclass
class MahjongTile:
    """麻将牌数据结构"""
    suit: str  # 'wan', 'tiao', 'tong'
    value: int  # 1-9
    
    def __str__(self):
        suit_names = {'wan': '万', 'tiao': '条', 'tong': '筒'}
        return f"{self.value}{suit_names.get(self.suit, self.suit)}"

@dataclass
class GameAction:
    """游戏操作记录"""
    sequence: int
    timestamp: str
    player_id: int  # 0-3
    action_type: str  # 'draw', 'discard', 'peng', 'gang', 'hu', 'missing_suit'
    card: Optional[str] = None
    target_player: Optional[int] = None
    gang_type: Optional[str] = None
    missing_suit: Optional[str] = None
    score_change: int = 0

@dataclass
class PlayerRecord:
    """玩家记录"""
    player_id: int
    player_name: str
    position: int
    initial_hand: List[str]
    missing_suit: Optional[str] = None
    final_score: int = 0
    is_winner: bool = False
    statistics: Dict = None
    
    def __post_init__(self):
        if self.statistics is None:
            self.statistics = {
                'draw_count': 0,
                'discard_count': 0,
                'peng_count': 0,
                'gang_count': 0
            }

class TencentMahjongVideoAnalyzer:
    """腾讯欢乐麻将录像分析器"""
    
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        
        # 视频基本信息
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.frame_count / self.fps
        
        # 游戏数据
        self.players = []
        self.actions = []
        self.game_id = f"video_game_{int(time.time())}"
        
        # 识别配置
        self.setup_recognition_areas()
        
    def setup_recognition_areas(self):
        """设置识别区域坐标"""
        # 根据腾讯欢乐麻将界面布局定义关键区域
        # 这些坐标需要根据实际录像分辨率调整
        self.areas = {
            'player_hands': {
                0: (100, 600, 800, 750),   # 自己手牌区域 (x1, y1, x2, y2)
                1: (850, 300, 950, 600),   # 下家手牌区域  
                2: (100, 50, 800, 150),    # 对家手牌区域
                3: (50, 300, 150, 600)     # 上家手牌区域
            },
            'discard_areas': {
                0: (200, 450, 700, 580),   # 自己弃牌区
                1: (700, 200, 850, 500),   # 下家弃牌区
                2: (200, 200, 700, 350),   # 对家弃牌区  
                3: (150, 200, 300, 500)    # 上家弃牌区
            },
            'meld_areas': {
                0: (50, 550, 150, 650),    # 自己碰杠区
                1: (800, 150, 900, 250),   # 下家碰杠区
                2: (750, 50, 850, 150),    # 对家碰杠区
                3: (50, 150, 150, 250)     # 上家碰杠区
            },
            'action_indicator': (400, 300, 500, 400),  # 操作提示区域
            'score_area': (50, 50, 200, 100),          # 分数显示区域
            'player_names': {
                0: (100, 750, 200, 780),   # 玩家名称区域
                1: (850, 600, 950, 630),
                2: (100, 20, 200, 50),
                3: (20, 600, 120, 630)
            }
        }
    
    def extract_frame_at_time(self, timestamp: float) -> np.ndarray:
        """提取指定时间的帧"""
        frame_number = int(timestamp * self.fps)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()
        return frame if ret else None
    
    def recognize_tile(self, tile_image: np.ndarray) -> Optional[MahjongTile]:
        """识别单张麻将牌"""
        # 预处理图像
        gray = cv2.cvtColor(tile_image, cv2.COLOR_BGR2GRAY)
        
        # 使用模板匹配或训练好的CNN模型识别
        # 这里简化为颜色和形状分析
        return self._analyze_tile_features(gray)
    
    def _analyze_tile_features(self, gray_image: np.ndarray) -> Optional[MahjongTile]:
        """分析麻将牌特征"""
        # 实际实现需要训练好的模型
        # 这里返回示例数据
        return MahjongTile('wan', 1)
    
    def detect_game_events(self, frame: np.ndarray, timestamp: float) -> List[GameAction]:
        """检测游戏事件"""
        events = []
        
        # 检测操作提示区域变化
        action_region = self._extract_region(frame, self.areas['action_indicator'])
        action_type = self._recognize_action_type(action_region)
        
        if action_type:
            # 检测是哪个玩家的操作
            player_id = self._detect_current_player(frame)
            
            action = GameAction(
                sequence=len(self.actions) + 1,
                timestamp=datetime.fromtimestamp(timestamp).isoformat(),
                player_id=player_id,
                action_type=action_type
            )
            
            # 根据操作类型提取相关信息
            if action_type in ['discard', 'draw']:
                card = self._detect_involved_card(frame, player_id, action_type)
                action.card = str(card) if card else None
            
            events.append(action)
        
        return events
    
    def _extract_region(self, frame: np.ndarray, region: Tuple[int, int, int, int]) -> np.ndarray:
        """提取图像区域"""
        x1, y1, x2, y2 = region
        return frame[y1:y2, x1:x2]
    
    def _recognize_action_type(self, action_image: np.ndarray) -> Optional[str]:
        """识别操作类型"""
        # 使用OCR或图像识别判断操作类型
        # 检测"碰"、"杠"、"胡"等文字
        text = pytesseract.image_to_string(action_image, lang='chi_sim')
        
        if '碰' in text:
            return 'peng'
        elif '杠' in text:
            return 'gang'
        elif '胡' in text:
            return 'hu'
        elif '摸' in text:
            return 'draw'
        
        return None
    
    def _detect_current_player(self, frame: np.ndarray) -> int:
        """检测当前操作玩家"""
        # 通过高亮、边框或其他视觉提示判断当前玩家
        # 这里返回示例数据
        return 0
    
    def _detect_involved_card(self, frame: np.ndarray, player_id: int, action_type: str) -> Optional[MahjongTile]:
        """检测操作涉及的牌"""
        if action_type == 'discard':
            # 检测弃牌区域最新的牌
            discard_area = self.areas['discard_areas'][player_id]
            discard_region = self._extract_region(frame, discard_area)
            return self._find_latest_discard(discard_region)
        
        return None
    
    def _find_latest_discard(self, discard_region: np.ndarray) -> Optional[MahjongTile]:
        """在弃牌区域找到最新弃的牌"""
        # 实际实现需要检测牌的位置和识别
        return MahjongTile('wan', 1)
    
    def analyze_full_video(self, sample_interval: float = 1.0) -> Dict:
        """分析完整视频"""
        print(f"开始分析视频: {self.video_path}")
        print(f"视频信息: {self.fps}fps, {self.duration:.1f}秒, {self.frame_count}帧")
        
        # 初始化玩家数据
        self._initialize_players()
        
        # 按时间间隔采样分析
        current_time = 0.0
        while current_time < self.duration:
            frame = self.extract_frame_at_time(current_time)
            if frame is not None:
                events = self.detect_game_events(frame, current_time)
                self.actions.extend(events)
                
                # 显示进度
                progress = (current_time / self.duration) * 100
                print(f"\r分析进度: {progress:.1f}%", end='')
            
            current_time += sample_interval
        
        print("\n分析完成!")
        return self._generate_replay_data()
    
    def _initialize_players(self):
        """初始化玩家数据"""
        # 从视频中识别玩家名称
        first_frame = self.extract_frame_at_time(0)
        
        for i in range(4):
            name_region = self._extract_region(first_frame, self.areas['player_names'][i])
            player_name = self._recognize_player_name(name_region)
            
            player = PlayerRecord(
                player_id=i,
                player_name=player_name or f"玩家{i+1}",
                position=i,
                initial_hand=[]  # 需要从游戏开始时的画面识别
            )
            self.players.append(player)
    
    def _recognize_player_name(self, name_image: np.ndarray) -> Optional[str]:
        """识别玩家名称"""
        # 使用OCR识别玩家名称
        try:
            text = pytesseract.image_to_string(name_image, lang='chi_sim')
            return text.strip() if text.strip() else None
        except:
            return None
    
    def _generate_replay_data(self) -> Dict:
        """生成牌谱数据"""
        return {
            "game_info": {
                "game_id": self.game_id,
                "start_time": datetime.now().isoformat(),
                "duration": int(self.duration),
                "player_count": 4,
                "game_mode": "xuezhan_daodi"
            },
            "players": [asdict(player) for player in self.players],
            "actions": [asdict(action) for action in self.actions],
            "metadata": {
                "source": "video_analysis",
                "video_path": self.video_path,
                "analysis_method": "computer_vision",
                "fps": self.fps,
                "frame_count": self.frame_count
            }
        }
    
    def save_replay(self, output_path: str):
        """保存牌谱到文件"""
        replay_data = self._generate_replay_data()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(replay_data, f, ensure_ascii=False, indent=2)
        
        print(f"牌谱已保存到: {output_path}")
    
    def __del__(self):
        """释放资源"""
        if hasattr(self, 'cap'):
            self.cap.release()

def main():
    """主函数示例"""
    video_path = "mahjong_game_recording.mp4"  # 替换为实际视频路径
    
    if not Path(video_path).exists():
        print(f"视频文件不存在: {video_path}")
        return
    
    # 创建分析器
    analyzer = TencentMahjongVideoAnalyzer(video_path)
    
    # 分析视频
    replay_data = analyzer.analyze_full_video(sample_interval=0.5)
    
    # 保存结果
    output_path = f"replay_{analyzer.game_id}.json"
    analyzer.save_replay(output_path)
    
    print(f"识别到 {len(analyzer.actions)} 个操作")
    print(f"牌谱数据已生成: {output_path}")

if __name__ == "__main__":
    main()