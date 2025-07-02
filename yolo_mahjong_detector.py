#!/usr/bin/env python3
"""
基于YOLO的麻将牌检测和识别系统
同时处理牌的定位、识别和操作检测
"""

import cv2
import numpy as np
import torch
import torchvision.transforms as transforms
from pathlib import Path
import json
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MahjongTileDetection:
    """麻将牌检测结果"""
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    tile_type: str  # "1万", "2条", "3筒" etc.
    confidence: float
    player_zone: int  # 0-3 表示哪个玩家区域
    tile_category: str  # "hand", "discard", "meld"

@dataclass
class GameAction:
    """游戏操作"""
    timestamp: float
    action_type: str  # "draw", "discard", "peng", "gang", "hu"
    player_id: int
    tiles_involved: List[str]
    target_player: Optional[int] = None
    confidence: float = 0.0

class YOLOMahjongDetector:
    """基于YOLO的麻将牌检测器"""
    
    def __init__(self, model_path: str = None):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"使用设备: {self.device}")
        
        # 麻将牌类别定义 (27种牌型)
        self.tile_classes = self._create_tile_classes()
        self.num_classes = len(self.tile_classes)
        
        # 游戏区域定义
        self.game_zones = self._define_game_zones()
        
        # 加载或创建模型
        self.model = self._load_or_create_model(model_path)
        
        # 操作检测器
        self.action_detector = MahjongActionDetector()
        
    def _create_tile_classes(self) -> List[str]:
        """创建麻将牌类别列表"""
        classes = []
        
        # 万字牌 1-9万
        for i in range(1, 10):
            classes.append(f"{i}万")
        
        # 条子牌 1-9条  
        for i in range(1, 10):
            classes.append(f"{i}条")
            
        # 筒子牌 1-9筒
        for i in range(1, 10):
            classes.append(f"{i}筒")
            
        logger.info(f"定义了 {len(classes)} 种麻将牌类别")
        return classes
    
    def _define_game_zones(self) -> Dict[str, Dict]:
        """定义游戏区域坐标"""
        # 这些坐标需要根据实际录像分辨率调整
        # 假设1920x1080分辨率
        zones = {
            'player_0': {  # 自己(下方)
                'hand': (200, 850, 1720, 1000),
                'discard': (400, 650, 1520, 800),
                'meld': (100, 750, 350, 850)
            },
            'player_1': {  # 右侧
                'hand': (1600, 300, 1850, 700),
                'discard': (1400, 400, 1580, 600),
                'meld': (1500, 200, 1650, 300)
            },
            'player_2': {  # 对面(上方)
                'hand': (200, 80, 1720, 230),
                'discard': (400, 280, 1520, 430),
                'meld': (1570, 130, 1820, 230)
            },
            'player_3': {  # 左侧
                'hand': (70, 300, 320, 700),
                'discard': (340, 400, 520, 600),
                'meld': (270, 200, 420, 300)
            },
            'center': {  # 中央区域
                'deck': (800, 450, 1120, 630),
                'action_area': (600, 400, 1320, 680)
            }
        }
        return zones
    
    def _load_or_create_model(self, model_path: str = None):
        """加载或创建YOLO模型"""
        try:
            if model_path and Path(model_path).exists():
                # 加载预训练模型
                model = torch.hub.load('ultralytics/yolov5', 'custom', 
                                     path=model_path, device=self.device)
                logger.info(f"加载自定义模型: {model_path}")
            else:
                # 使用预训练的YOLOv5作为基础
                model = torch.hub.load('ultralytics/yolov5', 'yolov5s', 
                                     device=self.device)
                # 修改输出层以适应麻将牌分类
                model.model[-1].nc = self.num_classes
                model.model[-1].anchors = model.model[-1].anchors.clone()
                logger.info("创建新的YOLOv5模型")
                
            return model
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            return None
    
    def detect_tiles_in_frame(self, frame: np.ndarray) -> List[MahjongTileDetection]:
        """在单帧中检测麻将牌"""
        if self.model is None:
            return []
        
        # YOLO推理
        results = self.model(frame)
        detections = []
        
        # 解析检测结果
        for *bbox, conf, cls in results.xyxy[0].cpu().numpy():
            if conf > 0.5:  # 置信度阈值
                x1, y1, x2, y2 = map(int, bbox)
                tile_type = self.tile_classes[int(cls)]
                
                # 确定牌所在的游戏区域
                player_zone, tile_category = self._classify_tile_location(x1, y1, x2, y2)
                
                detection = MahjongTileDetection(
                    bbox=(x1, y1, x2, y2),
                    tile_type=tile_type,
                    confidence=float(conf),
                    player_zone=player_zone,
                    tile_category=tile_category
                )
                detections.append(detection)
        
        return detections
    
    def _classify_tile_location(self, x1: int, y1: int, x2: int, y2: int) -> Tuple[int, str]:
        """根据坐标判断牌所在的区域"""
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        
        # 检查每个玩家的区域
        for player_id in range(4):
            zones = self.game_zones[f'player_{player_id}']
            
            for category, (zx1, zy1, zx2, zy2) in zones.items():
                if zx1 <= center_x <= zx2 and zy1 <= center_y <= zy2:
                    return player_id, category
        
        # 默认返回
        return -1, "unknown"
    
    def track_game_state(self, detections: List[MahjongTileDetection]) -> Dict:
        """跟踪游戏状态"""
        game_state = {
            'players': {i: {'hand': [], 'discard': [], 'meld': []} for i in range(4)},
            'center_tiles': []
        }
        
        # 按区域分组检测结果
        for detection in detections:
            if detection.player_zone >= 0:
                player_tiles = game_state['players'][detection.player_zone]
                player_tiles[detection.tile_category].append({
                    'tile': detection.tile_type,
                    'bbox': detection.bbox,
                    'confidence': detection.confidence
                })
            else:
                game_state['center_tiles'].append({
                    'tile': detection.tile_type,
                    'bbox': detection.bbox,
                    'confidence': detection.confidence
                })
        
        return game_state

class MahjongActionDetector:
    """麻将操作检测器"""
    
    def __init__(self):
        self.previous_state = None
        self.action_templates = self._load_action_templates()
    
    def _load_action_templates(self) -> Dict:
        """加载操作模板"""
        return {
            'draw': {
                'hand_increase': 1,
                'deck_decrease': 1,
                'time_window': 2.0  # 秒
            },
            'discard': {
                'hand_decrease': 1,
                'discard_increase': 1,
                'time_window': 3.0
            },
            'peng': {
                'hand_decrease': 2,
                'meld_increase': 3,
                'discard_source': True,
                'time_window': 5.0
            },
            'gang': {
                'hand_decrease': [1, 3, 4],  # 加杠/直杠/暗杠
                'meld_increase': 4,
                'time_window': 5.0
            },
            'hu': {
                'game_end': True,
                'special_highlight': True
            }
        }
    
    def detect_actions(self, current_state: Dict, timestamp: float) -> List[GameAction]:
        """检测游戏操作"""
        actions = []
        
        if self.previous_state is None:
            self.previous_state = current_state
            return actions
        
        # 比较当前状态和之前状态
        for player_id in range(4):
            player_actions = self._detect_player_actions(
                player_id, current_state, timestamp
            )
            actions.extend(player_actions)
        
        self.previous_state = current_state
        return actions
    
    def _detect_player_actions(self, player_id: int, current_state: Dict, 
                             timestamp: float) -> List[GameAction]:
        """检测单个玩家的操作"""
        actions = []
        
        prev_player = self.previous_state['players'][player_id]
        curr_player = current_state['players'][player_id]
        
        # 检测摸牌
        if len(curr_player['hand']) > len(prev_player['hand']):
            action = GameAction(
                timestamp=timestamp,
                action_type='draw',
                player_id=player_id,
                tiles_involved=self._get_new_tiles(prev_player['hand'], curr_player['hand']),
                confidence=0.8
            )
            actions.append(action)
        
        # 检测弃牌
        if len(curr_player['discard']) > len(prev_player['discard']):
            action = GameAction(
                timestamp=timestamp,
                action_type='discard',
                player_id=player_id,
                tiles_involved=self._get_new_tiles(prev_player['discard'], curr_player['discard']),
                confidence=0.9
            )
            actions.append(action)
        
        # 检测碰牌
        if len(curr_player['meld']) > len(prev_player['meld']):
            # 进一步分析是碰还是杠
            action_type = self._classify_meld_action(prev_player['meld'], curr_player['meld'])
            action = GameAction(
                timestamp=timestamp,
                action_type=action_type,
                player_id=player_id,
                tiles_involved=self._get_meld_tiles(prev_player['meld'], curr_player['meld']),
                confidence=0.85
            )
            actions.append(action)
        
        return actions
    
    def _get_new_tiles(self, prev_tiles: List, curr_tiles: List) -> List[str]:
        """获取新增的牌"""
        prev_set = {tile['tile'] for tile in prev_tiles}
        curr_set = {tile['tile'] for tile in curr_tiles}
        return list(curr_set - prev_set)
    
    def _get_meld_tiles(self, prev_melds: List, curr_melds: List) -> List[str]:
        """获取碰杠的牌"""
        # 简化实现，实际需要更复杂的逻辑
        if len(curr_melds) > len(prev_melds):
            return [curr_melds[-1]['tile']] if curr_melds else []
        return []
    
    def _classify_meld_action(self, prev_melds: List, curr_melds: List) -> str:
        """分类碰杠操作"""
        if len(curr_melds) > len(prev_melds):
            new_meld = curr_melds[-1]
            # 根据牌数判断是碰(3张)还是杠(4张)
            # 这里需要更复杂的逻辑来准确判断
            return 'peng'  # 简化返回
        return 'unknown'

class VideoMahjongAnalyzer:
    """完整的视频麻将分析器"""
    
    def __init__(self, model_path: str = None):
        self.detector = YOLOMahjongDetector(model_path)
        self.game_history = []
        
    def analyze_video(self, video_path: str, output_path: str = None) -> Dict:
        """分析完整视频"""
        logger.info(f"开始分析视频: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        all_actions = []
        frame_idx = 0
        
        # 每隔一定帧数分析一次
        analysis_interval = max(1, int(fps // 2))  # 每0.5秒分析一次
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_idx % analysis_interval == 0:
                timestamp = frame_idx / fps
                
                # 检测当前帧的麻将牌
                detections = self.detector.detect_tiles_in_frame(frame)
                
                # 跟踪游戏状态
                game_state = self.detector.track_game_state(detections)
                
                # 检测操作
                actions = self.detector.action_detector.detect_actions(game_state, timestamp)
                all_actions.extend(actions)
                
                # 显示进度
                progress = (frame_idx / frame_count) * 100
                if frame_idx % (analysis_interval * 10) == 0:
                    logger.info(f"分析进度: {progress:.1f}%")
            
            frame_idx += 1
        
        cap.release()
        
        # 生成牌谱数据
        replay_data = self._generate_replay_data(all_actions, video_path)
        
        # 保存结果
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(replay_data, f, ensure_ascii=False, indent=2)
            logger.info(f"牌谱已保存到: {output_path}")
        
        return replay_data
    
    def _generate_replay_data(self, actions: List[GameAction], video_path: str) -> Dict:
        """生成牌谱数据"""
        return {
            "game_info": {
                "game_id": f"yolo_game_{int(datetime.now().timestamp())}",
                "start_time": datetime.now().isoformat(),
                "duration": len(actions) * 30,  # 估算
                "player_count": 4,
                "game_mode": "xuezhan_daodi"
            },
            "players": self._generate_player_data(),
            "actions": [self._action_to_dict(action) for action in actions],
            "metadata": {
                "source": "yolo_detection",
                "video_path": video_path,
                "detection_method": "YOLOv5",
                "total_detections": len(actions)
            }
        }
    
    def _generate_player_data(self) -> List[Dict]:
        """生成玩家数据"""
        return [
            {
                "id": i,
                "name": f"玩家{i+1}",
                "position": i,
                "initial_hand": [],
                "final_score": 0,
                "is_winner": False,
                "statistics": {
                    "draw_count": 0,
                    "discard_count": 0,
                    "peng_count": 0,
                    "gang_count": 0
                }
            }
            for i in range(4)
        ]
    
    def _action_to_dict(self, action: GameAction) -> Dict:
        """转换操作为字典格式"""
        return {
            "sequence": len(self.game_history) + 1,
            "timestamp": datetime.fromtimestamp(action.timestamp).isoformat(),
            "player_id": action.player_id,
            "action_type": action.action_type,
            "card": action.tiles_involved[0] if action.tiles_involved else None,
            "target_player": action.target_player,
            "score_change": 0,
            "confidence": action.confidence
        }

def main():
    """主函数示例"""
    try:
        # 创建分析器
        analyzer = VideoMahjongAnalyzer()
        
        # 分析视频
        video_path = "sample_mahjong_game.mp4"
        output_path = "yolo_replay.json"
        
        replay_data = analyzer.analyze_video(video_path, output_path)
        
        logger.info("✅ YOLO分析完成!")
        logger.info(f"检测到 {len(replay_data['actions'])} 个操作")
        
    except Exception as e:
        logger.error(f"分析失败: {e}")

if __name__ == "__main__":
    main()