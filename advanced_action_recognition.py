#!/usr/bin/env python3
"""
高级麻将操作识别系统
处理复杂的麻将操作检测和游戏逻辑分析
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque
import json

logger = logging.getLogger(__name__)

class ActionType(Enum):
    """操作类型枚举"""
    DRAW = "draw"           # 摸牌
    DISCARD = "discard"     # 弃牌
    PENG = "peng"          # 碰牌
    GANG = "gang"          # 杠牌
    HU = "hu"              # 胡牌
    MISSING_SUIT = "missing_suit"  # 定缺
    PASS = "pass"          # 过牌

class GangType(Enum):
    """杠牌类型"""
    MING_GANG = "ming_gang"  # 明杠(直杠)
    AN_GANG = "an_gang"      # 暗杠
    JIA_GANG = "jia_gang"    # 加杠

@dataclass
class GameState:
    """游戏状态"""
    player_hands: Dict[int, List[str]] = field(default_factory=dict)
    player_discards: Dict[int, List[str]] = field(default_factory=dict)
    player_melds: Dict[int, List[Dict]] = field(default_factory=dict)
    current_player: int = 0
    deck_remaining: int = 108
    game_phase: str = "playing"  # "dealing", "playing", "finished"
    turn_count: int = 0

@dataclass
class ActionCandidate:
    """操作候选"""
    action_type: ActionType
    player_id: int
    confidence: float
    evidence: Dict
    timestamp: float
    tiles_involved: List[str] = field(default_factory=list)

class AdvancedActionRecognizer:
    """高级操作识别器"""
    
    def __init__(self):
        self.state_history = deque(maxlen=50)  # 保存最近50个状态
        self.action_buffer = deque(maxlen=20)   # 操作缓冲区
        self.game_rules = MahjongRules()
        
        # 视觉特征检测器
        self.visual_detectors = {
            'highlight_detector': HighlightDetector(),
            'motion_detector': MotionDetector(),
            'ui_detector': UIElementDetector(),
            'text_detector': TextDetector()
        }
        
        # 操作模式识别
        self.action_patterns = self._initialize_action_patterns()
    
    def _initialize_action_patterns(self) -> Dict:
        """初始化操作模式"""
        return {
            'draw_patterns': [
                {'hand_count_change': +1, 'motion_area': 'deck_to_hand'},
                {'highlight_change': 'hand_area', 'duration': (0.5, 2.0)}
            ],
            'discard_patterns': [
                {'hand_count_change': -1, 'motion_area': 'hand_to_discard'},
                {'new_tile_in_discard': True, 'timing': 'after_draw'}
            ],
            'peng_patterns': [
                {'hand_count_change': -2, 'meld_count_change': +1},
                {'ui_prompt': 'peng_button', 'source_discard': True}
            ],
            'gang_patterns': [
                {'hand_count_change': [-1, -3, -4], 'meld_count_change': +1},
                {'ui_prompt': 'gang_button', 'special_highlight': True}
            ]
        }
    
    def analyze_frame_sequence(self, frames: List[np.ndarray], 
                             timestamps: List[float]) -> List[ActionCandidate]:
        """分析帧序列识别操作"""
        candidates = []
        
        for i, (frame, timestamp) in enumerate(zip(frames, timestamps)):
            # 多维度特征提取
            features = self._extract_comprehensive_features(frame, timestamp)
            
            # 状态更新
            current_state = self._update_game_state(features)
            
            # 操作检测
            frame_candidates = self._detect_actions_in_frame(
                current_state, features, timestamp
            )
            
            candidates.extend(frame_candidates)
            
            # 保存状态历史
            self.state_history.append({
                'timestamp': timestamp,
                'state': current_state,
                'features': features
            })
        
        # 后处理和验证
        validated_actions = self._validate_and_merge_candidates(candidates)
        
        return validated_actions
    
    def _extract_comprehensive_features(self, frame: np.ndarray, 
                                      timestamp: float) -> Dict:
        """提取综合特征"""
        features = {
            'timestamp': timestamp,
            'frame_shape': frame.shape,
            'visual_features': {},
            'motion_features': {},
            'ui_features': {},
            'text_features': {}
        }
        
        # 视觉特征检测
        for detector_name, detector in self.visual_detectors.items():
            try:
                detector_features = detector.extract_features(frame)
                features[detector_name.replace('_detector', '_features')] = detector_features
            except Exception as e:
                logger.warning(f"{detector_name} 特征提取失败: {e}")
                features[detector_name.replace('_detector', '_features')] = {}
        
        return features
    
    def _detect_actions_in_frame(self, state: GameState, features: Dict, 
                               timestamp: float) -> List[ActionCandidate]:
        """在单帧中检测操作"""
        candidates = []
        
        # 检测各种操作类型
        for action_type in ActionType:
            action_candidates = self._detect_specific_action(
                action_type, state, features, timestamp
            )
            candidates.extend(action_candidates)
        
        return candidates
    
    def _detect_specific_action(self, action_type: ActionType, state: GameState,
                              features: Dict, timestamp: float) -> List[ActionCandidate]:
        """检测特定类型的操作"""
        candidates = []
        
        if action_type == ActionType.DRAW:
            candidates.extend(self._detect_draw_action(state, features, timestamp))
        elif action_type == ActionType.DISCARD:
            candidates.extend(self._detect_discard_action(state, features, timestamp))
        elif action_type == ActionType.PENG:
            candidates.extend(self._detect_peng_action(state, features, timestamp))
        elif action_type == ActionType.GANG:
            candidates.extend(self._detect_gang_action(state, features, timestamp))
        elif action_type == ActionType.HU:
            candidates.extend(self._detect_hu_action(state, features, timestamp))
        
        return candidates
    
    def _detect_draw_action(self, state: GameState, features: Dict, 
                          timestamp: float) -> List[ActionCandidate]:
        """检测摸牌操作"""
        candidates = []
        
        # 检测摸牌的视觉特征
        motion_features = features.get('motion_features', {})
        ui_features = features.get('ui_features', {})
        
        # 1. 检测从牌堆到手牌的运动
        if motion_features.get('deck_to_hand_motion', False):
            for player_id in range(4):
                confidence = motion_features.get('motion_confidence', 0.0)
                
                candidate = ActionCandidate(
                    action_type=ActionType.DRAW,
                    player_id=player_id,
                    confidence=confidence,
                    evidence={
                        'motion_detected': True,
                        'motion_direction': 'deck_to_hand',
                        'visual_cues': motion_features
                    },
                    timestamp=timestamp
                )
                candidates.append(candidate)
        
        # 2. 检测手牌区域高亮
        highlight_features = features.get('visual_features', {})
        if highlight_features.get('hand_area_highlighted', False):
            highlighted_player = highlight_features.get('highlighted_player', -1)
            if highlighted_player >= 0:
                candidate = ActionCandidate(
                    action_type=ActionType.DRAW,
                    player_id=highlighted_player,
                    confidence=0.7,
                    evidence={
                        'highlight_detected': True,
                        'highlight_area': 'hand',
                        'visual_cues': highlight_features
                    },
                    timestamp=timestamp
                )
                candidates.append(candidate)
        
        return candidates
    
    def _detect_discard_action(self, state: GameState, features: Dict,
                             timestamp: float) -> List[ActionCandidate]:
        """检测弃牌操作"""
        candidates = []
        
        motion_features = features.get('motion_features', {})
        
        # 检测从手牌到弃牌区的运动
        if motion_features.get('hand_to_discard_motion', False):
            player_id = motion_features.get('motion_player', -1)
            if player_id >= 0:
                
                # 尝试识别弃的牌
                tiles_involved = self._identify_discarded_tile(features, player_id)
                
                candidate = ActionCandidate(
                    action_type=ActionType.DISCARD,
                    player_id=player_id,
                    confidence=0.8,
                    evidence={
                        'motion_detected': True,
                        'motion_direction': 'hand_to_discard',
                        'discard_area_change': True
                    },
                    timestamp=timestamp,
                    tiles_involved=tiles_involved
                )
                candidates.append(candidate)
        
        return candidates
    
    def _detect_peng_action(self, state: GameState, features: Dict,
                          timestamp: float) -> List[ActionCandidate]:
        """检测碰牌操作"""
        candidates = []
        
        ui_features = features.get('ui_features', {})
        text_features = features.get('text_features', {})
        
        # 检测"碰"按钮或文字提示
        if (ui_features.get('peng_button_visible', False) or 
            text_features.get('peng_text_detected', False)):
            
            # 确定执行碰牌的玩家
            active_player = self._determine_active_player(features)
            
            if active_player >= 0:
                # 识别碰的牌
                peng_tile = self._identify_peng_tile(features, state)
                
                candidate = ActionCandidate(
                    action_type=ActionType.PENG,
                    player_id=active_player,
                    confidence=0.85,
                    evidence={
                        'ui_prompt_detected': True,
                        'peng_button': ui_features.get('peng_button_visible', False),
                        'text_detected': text_features.get('peng_text_detected', False)
                    },
                    timestamp=timestamp,
                    tiles_involved=[peng_tile] if peng_tile else []
                )
                candidates.append(candidate)
        
        return candidates
    
    def _detect_gang_action(self, state: GameState, features: Dict,
                          timestamp: float) -> List[ActionCandidate]:
        """检测杠牌操作"""
        candidates = []
        
        ui_features = features.get('ui_features', {})
        text_features = features.get('text_features', {})
        
        # 检测杠牌提示
        if (ui_features.get('gang_button_visible', False) or
            text_features.get('gang_text_detected', False)):
            
            active_player = self._determine_active_player(features)
            
            if active_player >= 0:
                # 识别杠的牌和杠的类型
                gang_tile, gang_type = self._identify_gang_details(features, state)
                
                candidate = ActionCandidate(
                    action_type=ActionType.GANG,
                    player_id=active_player,
                    confidence=0.85,
                    evidence={
                        'ui_prompt_detected': True,
                        'gang_type': gang_type.value if gang_type else 'unknown',
                        'visual_cues': ui_features
                    },
                    timestamp=timestamp,
                    tiles_involved=[gang_tile] if gang_tile else []
                )
                candidates.append(candidate)
        
        return candidates
    
    def _detect_hu_action(self, state: GameState, features: Dict,
                        timestamp: float) -> List[ActionCandidate]:
        """检测胡牌操作"""
        candidates = []
        
        ui_features = features.get('ui_features', {})
        text_features = features.get('text_features', {})
        
        # 检测胡牌特殊效果和提示
        hu_indicators = [
            ui_features.get('hu_button_visible', False),
            text_features.get('hu_text_detected', False),
            ui_features.get('win_animation_detected', False),
            ui_features.get('score_change_detected', False)
        ]
        
        if any(hu_indicators):
            active_player = self._determine_active_player(features)
            
            if active_player >= 0:
                # 确定胡牌类型（自摸/点炮）
                hu_type = self._determine_hu_type(features, state)
                hu_tile = self._identify_hu_tile(features, state)
                
                candidate = ActionCandidate(
                    action_type=ActionType.HU,
                    player_id=active_player,
                    confidence=0.9,
                    evidence={
                        'win_detected': True,
                        'hu_type': hu_type,
                        'ui_indicators': hu_indicators,
                        'visual_effects': ui_features
                    },
                    timestamp=timestamp,
                    tiles_involved=[hu_tile] if hu_tile else []
                )
                candidates.append(candidate)
        
        return candidates
    
    def _validate_and_merge_candidates(self, candidates: List[ActionCandidate]) -> List[ActionCandidate]:
        """验证和合并操作候选"""
        if not candidates:
            return []
        
        # 按时间排序
        candidates.sort(key=lambda x: x.timestamp)
        
        # 去重和合并
        merged_candidates = []
        current_group = [candidates[0]]
        
        for candidate in candidates[1:]:
            # 如果时间间隔小于阈值，认为是同一个操作的不同检测
            if (candidate.timestamp - current_group[-1].timestamp < 2.0 and
                candidate.action_type == current_group[-1].action_type and
                candidate.player_id == current_group[-1].player_id):
                current_group.append(candidate)
            else:
                # 处理当前组
                merged_candidate = self._merge_candidate_group(current_group)
                if merged_candidate:
                    merged_candidates.append(merged_candidate)
                current_group = [candidate]
        
        # 处理最后一组
        if current_group:
            merged_candidate = self._merge_candidate_group(current_group)
            if merged_candidate:
                merged_candidates.append(merged_candidate)
        
        # 游戏逻辑验证
        validated_candidates = self._validate_game_logic(merged_candidates)
        
        return validated_candidates
    
    def _merge_candidate_group(self, group: List[ActionCandidate]) -> Optional[ActionCandidate]:
        """合并候选组"""
        if not group:
            return None
        
        if len(group) == 1:
            return group[0]
        
        # 选择置信度最高的作为基础
        best_candidate = max(group, key=lambda x: x.confidence)
        
        # 合并证据
        merged_evidence = {}
        for candidate in group:
            merged_evidence.update(candidate.evidence)
        
        # 合并涉及的牌
        all_tiles = []
        for candidate in group:
            all_tiles.extend(candidate.tiles_involved)
        
        return ActionCandidate(
            action_type=best_candidate.action_type,
            player_id=best_candidate.player_id,
            confidence=min(1.0, best_candidate.confidence + 0.1 * (len(group) - 1)),
            evidence=merged_evidence,
            timestamp=best_candidate.timestamp,
            tiles_involved=list(set(all_tiles))
        )
    
    def _validate_game_logic(self, candidates: List[ActionCandidate]) -> List[ActionCandidate]:
        """验证游戏逻辑"""
        validated = []
        
        for candidate in candidates:
            if self.game_rules.is_valid_action(candidate, self.state_history):
                validated.append(candidate)
            else:
                logger.debug(f"操作验证失败: {candidate.action_type} by 玩家{candidate.player_id}")
        
        return validated
    
    # 辅助方法
    def _update_game_state(self, features: Dict) -> GameState:
        """更新游戏状态"""
        # 这里应该基于视觉特征更新游戏状态
        # 简化实现
        return GameState()
    
    def _determine_active_player(self, features: Dict) -> int:
        """确定当前活跃玩家"""
        highlight_features = features.get('visual_features', {})
        return highlight_features.get('highlighted_player', 0)
    
    def _identify_discarded_tile(self, features: Dict, player_id: int) -> List[str]:
        """识别弃的牌"""
        # 实际实现需要分析弃牌区域的变化
        return []
    
    def _identify_peng_tile(self, features: Dict, state: GameState) -> Optional[str]:
        """识别碰的牌"""
        # 实际实现需要分析最近的弃牌
        return None
    
    def _identify_gang_details(self, features: Dict, state: GameState) -> Tuple[Optional[str], Optional[GangType]]:
        """识别杠的详细信息"""
        return None, None
    
    def _determine_hu_type(self, features: Dict, state: GameState) -> str:
        """确定胡牌类型"""
        return "zimo"  # 简化返回
    
    def _identify_hu_tile(self, features: Dict, state: GameState) -> Optional[str]:
        """识别胡牌"""
        return None

# 特征检测器类
class HighlightDetector:
    """高亮检测器"""
    def extract_features(self, frame: np.ndarray) -> Dict:
        # 检测高亮区域
        return {'hand_area_highlighted': False, 'highlighted_player': -1}

class MotionDetector:
    """运动检测器"""
    def extract_features(self, frame: np.ndarray) -> Dict:
        # 检测运动轨迹
        return {'deck_to_hand_motion': False, 'hand_to_discard_motion': False}

class UIElementDetector:
    """UI元素检测器"""
    def extract_features(self, frame: np.ndarray) -> Dict:
        # 检测按钮和UI元素
        return {
            'peng_button_visible': False,
            'gang_button_visible': False,
            'hu_button_visible': False
        }

class TextDetector:
    """文字检测器"""
    def extract_features(self, frame: np.ndarray) -> Dict:
        # OCR文字识别
        return {
            'peng_text_detected': False,
            'gang_text_detected': False,
            'hu_text_detected': False
        }

class MahjongRules:
    """麻将规则验证器"""
    def is_valid_action(self, candidate: ActionCandidate, state_history: deque) -> bool:
        """验证操作是否符合麻将规则"""
        # 实现麻将规则验证逻辑
        return True

def main():
    """测试函数"""
    recognizer = AdvancedActionRecognizer()
    
    # 模拟帧序列
    frames = [np.zeros((720, 1280, 3), dtype=np.uint8) for _ in range(10)]
    timestamps = [i * 0.5 for i in range(10)]
    
    # 分析操作
    actions = recognizer.analyze_frame_sequence(frames, timestamps)
    
    print(f"检测到 {len(actions)} 个操作")
    for action in actions:
        print(f"- {action.action_type.value} by 玩家{action.player_id}, 置信度: {action.confidence:.2f}")

if __name__ == "__main__":
    main()