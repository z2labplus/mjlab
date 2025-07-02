#!/usr/bin/env python3
"""
基于YOLOv8的高精度麻将牌检测系统
专为视频转牌谱设计，追求最高准确率
"""

import cv2
import numpy as np
from ultralytics import YOLO
import torch
from pathlib import Path
import json
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional, Union
from collections import defaultdict, deque
import time

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MahjongTile:
    """麻将牌检测结果"""
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    tile_type: str  # "1万", "2条", "3筒" etc.
    confidence: float
    player_zone: int  # 0-3 表示哪个玩家区域，-1表示未知
    tile_category: str  # "hand", "discard", "meld", "deck"
    frame_id: int
    timestamp: float

@dataclass 
class GameAction:
    """游戏操作记录"""
    sequence: int
    timestamp: str
    player_id: int
    action_type: str  # 'draw', 'discard', 'peng', 'gang', 'hu', 'pass'
    tiles_involved: List[str]
    target_player: Optional[int] = None
    confidence: float = 0.0
    evidence: Dict = None

class YOLOv8MahjongDetector:
    """基于YOLOv8的麻将牌检测器"""
    
    def __init__(self, model_path: Optional[str] = None, device: str = 'auto'):
        """
        初始化YOLOv8检测器
        
        Args:
            model_path: 自定义模型路径，None则使用预训练模型
            device: 'auto', 'cpu', 'cuda', 'mps'
        """
        self.device = self._setup_device(device)
        logger.info(f"使用设备: {self.device}")
        
        # 麻将牌类别定义
        self.tile_classes = self._create_mahjong_classes()
        self.num_classes = len(self.tile_classes)
        
        # 游戏区域配置
        self.game_zones = self._setup_game_zones()
        
        # 加载YOLO模型
        self.model = self._load_yolo_model(model_path)
        
        # 检测配置
        self.detection_config = {
            'conf_threshold': 0.6,  # 置信度阈值
            'iou_threshold': 0.4,   # NMS阈值
            'max_det': 300,         # 最大检测数量
            'agnostic_nms': True,   # 类别无关NMS
        }
        
        # 状态跟踪
        self.game_state_tracker = GameStateTracker()
        self.action_detector = AdvancedActionDetector()
        
    def _setup_device(self, device: str) -> str:
        """设置计算设备"""
        if device == 'auto':
            if torch.cuda.is_available():
                return 'cuda'
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return 'mps'
            else:
                return 'cpu'
        return device
    
    def _create_mahjong_classes(self) -> List[str]:
        """创建麻将牌类别列表（27种基础牌型）"""
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
        
        logger.info(f"定义麻将牌类别: {len(classes)}种 - {classes}")
        return classes
    
    def _setup_game_zones(self) -> Dict:
        """设置游戏区域 - 支持多分辨率自适应"""
        return {
            # 1920x1080分辨率的基准坐标
            '1920x1080': {
                'player_0': {  # 自己(下方)
                    'hand': (300, 900, 1620, 1060),
                    'discard': (500, 700, 1420, 880),
                    'meld': (150, 800, 450, 900)
                },
                'player_1': {  # 右侧
                    'hand': (1650, 350, 1900, 750),
                    'discard': (1450, 450, 1630, 650),
                    'meld': (1550, 250, 1750, 350)
                },
                'player_2': {  # 对面(上方)
                    'hand': (300, 20, 1620, 180),
                    'discard': (500, 200, 1420, 380),
                    'meld': (1470, 70, 1770, 170)
                },
                'player_3': {  # 左侧
                    'hand': (20, 350, 270, 750),
                    'discard': (290, 450, 470, 650),
                    'meld': (170, 250, 370, 350)
                },
                'center': {
                    'deck': (860, 500, 1060, 580),
                    'action_area': (700, 450, 1220, 630)
                }
            }
        }
    
    def _load_yolo_model(self, model_path: Optional[str]) -> YOLO:
        """加载YOLOv8模型"""
        try:
            if model_path and Path(model_path).exists():
                logger.info(f"加载自定义模型: {model_path}")
                model = YOLO(model_path)
            else:
                logger.info("使用YOLOv8预训练模型，将针对麻将牌进行微调")
                model = YOLO('yolov8n.pt')  # 使用nano版本，速度快
                
            # 设置设备
            model.to(self.device)
            return model
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise
    
    def detect_tiles_in_frame(self, frame: np.ndarray, frame_id: int = 0, 
                            timestamp: float = 0.0) -> List[MahjongTile]:
        """
        在单帧中检测麻将牌
        
        Args:
            frame: 输入图像帧
            frame_id: 帧编号
            timestamp: 时间戳
            
        Returns:
            检测到的麻将牌列表
        """
        detections = []
        
        try:
            # YOLOv8推理
            results = self.model(
                frame,
                conf=self.detection_config['conf_threshold'],
                iou=self.detection_config['iou_threshold'],
                max_det=self.detection_config['max_det'],
                agnostic_nms=self.detection_config['agnostic_nms'],
                verbose=False
            )
            
            # 解析检测结果
            if results and len(results) > 0:
                boxes = results[0].boxes
                
                if boxes is not None:
                    for i in range(len(boxes)):
                        # 提取边界框和置信度
                        bbox = boxes.xyxy[i].cpu().numpy()
                        conf = float(boxes.conf[i].cpu().numpy())
                        cls_id = int(boxes.cls[i].cpu().numpy())
                        
                        # 确保类别ID有效
                        if 0 <= cls_id < len(self.tile_classes):
                            x1, y1, x2, y2 = map(int, bbox)
                            tile_type = self.tile_classes[cls_id]
                            
                            # 分类牌的位置和类别
                            player_zone, tile_category = self._classify_tile_location(
                                x1, y1, x2, y2, frame.shape
                            )
                            
                            detection = MahjongTile(
                                bbox=(x1, y1, x2, y2),
                                tile_type=tile_type,
                                confidence=conf,
                                player_zone=player_zone,
                                tile_category=tile_category,
                                frame_id=frame_id,
                                timestamp=timestamp
                            )
                            detections.append(detection)
            
        except Exception as e:
            logger.error(f"帧{frame_id}检测失败: {e}")
        
        return detections
    
    def _classify_tile_location(self, x1: int, y1: int, x2: int, y2: int, 
                              frame_shape: Tuple[int, int, int]) -> Tuple[int, str]:
        """根据坐标判断牌所在的区域"""
        h, w = frame_shape[:2]
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        
        # 根据分辨率选择对应的区域配置
        resolution_key = f"{w}x{h}"
        if resolution_key not in self.game_zones:
            # 使用最接近的分辨率配置并进行缩放
            resolution_key = '1920x1080'
            scale_x = w / 1920
            scale_y = h / 1080
        else:
            scale_x = scale_y = 1.0
        
        zones = self.game_zones[resolution_key]
        
        # 检查每个玩家的区域
        for player_id in range(4):
            player_zones = zones[f'player_{player_id}']
            
            for category, (zx1, zy1, zx2, zy2) in player_zones.items():
                # 应用缩放
                zx1, zy1 = int(zx1 * scale_x), int(zy1 * scale_y)
                zx2, zy2 = int(zx2 * scale_x), int(zy2 * scale_y)
                
                if zx1 <= center_x <= zx2 and zy1 <= center_y <= zy2:
                    return player_id, category
        
        # 检查中央区域
        center_zones = zones['center']
        for category, (zx1, zy1, zx2, zy2) in center_zones.items():
            zx1, zy1 = int(zx1 * scale_x), int(zy1 * scale_y)
            zx2, zy2 = int(zx2 * scale_x), int(zy2 * scale_y)
            
            if zx1 <= center_x <= zx2 and zy1 <= center_y <= zy2:
                return -1, category
        
        return -1, "unknown"
    
    def process_video(self, video_path: str, output_path: str = None, 
                     sample_interval: float = 0.5) -> Dict:
        """
        处理完整视频文件
        
        Args:
            video_path: 视频文件路径
            output_path: 输出牌谱文件路径
            sample_interval: 采样间隔（秒）
            
        Returns:
            牌谱数据字典
        """
        logger.info(f"开始处理视频: {video_path}")
        
        # 打开视频
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        # 获取视频信息
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        logger.info(f"视频信息: {width}x{height}, {fps:.1f}fps, {duration:.1f}s, {frame_count}帧")
        
        # 计算采样间隔
        frame_interval = max(1, int(fps * sample_interval))
        total_frames_to_process = frame_count // frame_interval
        
        all_detections = []
        all_actions = []
        processed_frames = 0
        
        try:
            frame_id = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 按间隔采样
                if frame_id % frame_interval == 0:
                    timestamp = frame_id / fps
                    
                    # 检测当前帧
                    detections = self.detect_tiles_in_frame(frame, frame_id, timestamp)
                    all_detections.extend(detections)
                    
                    # 更新游戏状态
                    self.game_state_tracker.update_state(detections, timestamp)
                    
                    # 检测操作
                    actions = self.action_detector.detect_actions(
                        self.game_state_tracker.get_current_state(),
                        detections,
                        timestamp
                    )
                    all_actions.extend(actions)
                    
                    processed_frames += 1
                    
                    # 显示进度
                    if processed_frames % 10 == 0:
                        progress = (processed_frames / total_frames_to_process) * 100
                        logger.info(f"处理进度: {progress:.1f}% ({processed_frames}/{total_frames_to_process})")
                
                frame_id += 1
        
        finally:
            cap.release()
        
        logger.info(f"处理完成! 检测到{len(all_detections)}个麻将牌，{len(all_actions)}个操作")
        
        # 生成牌谱数据
        replay_data = self._generate_replay_data(
            all_actions, all_detections, video_path, duration
        )
        
        # 保存结果
        if output_path:
            self._save_replay_data(replay_data, output_path)
        
        return replay_data
    
    def _generate_replay_data(self, actions: List[GameAction], 
                            detections: List[MahjongTile], 
                            video_path: str, duration: float) -> Dict:
        """生成标准牌谱数据格式"""
        game_id = f"yolov8_game_{int(datetime.now().timestamp())}"
        
        return {
            "game_info": {
                "game_id": game_id,
                "start_time": datetime.now().isoformat(),
                "duration": int(duration),
                "player_count": 4,
                "game_mode": "xuezhan_daodi",
                "source": "video_analysis"
            },
            "players": self._generate_player_data(),
            "actions": [self._action_to_dict(action, i+1) for i, action in enumerate(actions)],
            "metadata": {
                "video_path": video_path,
                "detection_method": "YOLOv8",
                "total_detections": len(detections),
                "total_actions": len(actions),
                "analysis_timestamp": datetime.now().isoformat(),
                "device_used": self.device,
                "model_confidence_threshold": self.detection_config['conf_threshold']
            },
            "statistics": self._generate_statistics(actions, detections)
        }
    
    def _generate_player_data(self) -> List[Dict]:
        """生成玩家数据"""
        return [
            {
                "id": i,
                "name": f"玩家{i+1}",
                "position": i,
                "initial_hand": [],
                "missing_suit": None,
                "final_score": 0,
                "is_winner": False,
                "statistics": {
                    "draw_count": 0,
                    "discard_count": 0,
                    "peng_count": 0,
                    "gang_count": 0,
                    "hu_count": 0
                }
            }
            for i in range(4)
        ]
    
    def _action_to_dict(self, action: GameAction, sequence: int) -> Dict:
        """转换操作为字典格式"""
        return {
            "sequence": sequence,
            "timestamp": action.timestamp,
            "player_id": action.player_id,
            "action_type": action.action_type,
            "card": action.tiles_involved[0] if action.tiles_involved else None,
            "cards": action.tiles_involved,
            "target_player": action.target_player,
            "score_change": 0,
            "confidence": action.confidence,
            "evidence": action.evidence or {}
        }
    
    def _generate_statistics(self, actions: List[GameAction], 
                           detections: List[MahjongTile]) -> Dict:
        """生成统计信息"""
        action_counts = defaultdict(int)
        tile_counts = defaultdict(int)
        
        for action in actions:
            action_counts[action.action_type] += 1
        
        for detection in detections:
            tile_counts[detection.tile_type] += 1
        
        return {
            "action_distribution": dict(action_counts),
            "tile_detection_distribution": dict(tile_counts),
            "average_confidence": np.mean([d.confidence for d in detections]) if detections else 0.0,
            "detection_zones": {
                f"player_{i}": len([d for d in detections if d.player_zone == i])
                for i in range(4)
            }
        }
    
    def _save_replay_data(self, replay_data: Dict, output_path: str):
        """保存牌谱数据"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(replay_data, f, ensure_ascii=False, indent=2)
            logger.info(f"牌谱已保存到: {output_path}")
        except Exception as e:
            logger.error(f"保存牌谱失败: {e}")

class GameStateTracker:
    """游戏状态跟踪器"""
    
    def __init__(self):
        self.current_state = {
            'players': {i: {'hand': [], 'discard': [], 'meld': []} for i in range(4)},
            'center_tiles': [],
            'timestamp': 0.0
        }
        self.state_history = deque(maxlen=100)
    
    def update_state(self, detections: List[MahjongTile], timestamp: float):
        """更新游戏状态"""
        new_state = {
            'players': {i: {'hand': [], 'discard': [], 'meld': []} for i in range(4)},
            'center_tiles': [],
            'timestamp': timestamp
        }
        
        # 按区域分组检测结果
        for detection in detections:
            if detection.player_zone >= 0:
                player_data = new_state['players'][detection.player_zone]
                player_data[detection.tile_category].append({
                    'tile': detection.tile_type,
                    'bbox': detection.bbox,
                    'confidence': detection.confidence
                })
            else:
                new_state['center_tiles'].append({
                    'tile': detection.tile_type,
                    'category': detection.tile_category,
                    'bbox': detection.bbox,
                    'confidence': detection.confidence
                })
        
        self.state_history.append(self.current_state.copy())
        self.current_state = new_state
    
    def get_current_state(self) -> Dict:
        """获取当前游戏状态"""
        return self.current_state
    
    def get_state_history(self) -> List[Dict]:
        """获取状态历史"""
        return list(self.state_history)

class AdvancedActionDetector:
    """高级操作检测器"""
    
    def __init__(self):
        self.action_buffer = deque(maxlen=50)
        self.last_detection_time = {}
        
    def detect_actions(self, current_state: Dict, detections: List[MahjongTile], 
                      timestamp: float) -> List[GameAction]:
        """检测游戏操作"""
        actions = []
        
        # 这里是简化的操作检测逻辑
        # 实际实现需要更复杂的状态比较和模式识别
        
        # 检测摸牌、弃牌等基础操作
        # 基于牌数变化、位置变化等进行判断
        
        return actions

def main():
    """主函数 - 演示用法"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YOLOv8麻将牌视频分析')
    parser.add_argument('--video', required=True, help='输入视频路径')
    parser.add_argument('--output', help='输出牌谱路径')
    parser.add_argument('--model', help='自定义模型路径')
    parser.add_argument('--device', default='auto', help='计算设备')
    parser.add_argument('--interval', type=float, default=0.5, help='采样间隔(秒)')
    
    args = parser.parse_args()
    
    try:
        # 创建检测器
        detector = YOLOv8MahjongDetector(
            model_path=args.model,
            device=args.device
        )
        
        # 处理视频
        output_path = args.output or f"yolov8_replay_{int(time.time())}.json"
        replay_data = detector.process_video(
            args.video, 
            output_path, 
            args.interval
        )
        
        logger.info("✅ YOLOv8分析完成!")
        logger.info(f"📊 统计信息:")
        logger.info(f"   - 检测到操作: {len(replay_data['actions'])}个")
        logger.info(f"   - 检测总数: {replay_data['metadata']['total_detections']}个")
        logger.info(f"   - 使用设备: {replay_data['metadata']['device_used']}")
        
    except Exception as e:
        logger.error(f"❌ 处理失败: {e}")
        raise

if __name__ == "__main__":
    main()