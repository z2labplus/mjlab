# 🎯 YOLO + 操作识别整合方案

## 🔍 为什么需要YOLO？

### YOLO的核心优势

1. **同时定位和识别**
   ```python
   # 传统方案需要两步
   regions = detect_tile_regions(frame)  # 步骤1: 定位
   tiles = classify_tiles(regions)       # 步骤2: 识别
   
   # YOLO一步完成
   detections = yolo_model(frame)        # 同时完成定位+识别
   ```

2. **处理复杂场景**
   - ✅ 牌的位置变化（手牌重新排列）
   - ✅ 部分遮挡（手指遮挡部分牌面）
   - ✅ 多张牌同时检测
   - ✅ 不同大小和角度的牌

3. **实时性能**
   - YOLOv5: ~100 FPS
   - YOLOv8: ~120 FPS  
   - 适合视频实时分析

## 🏗️ 整体架构设计

```
录像视频 → 帧提取 → YOLO检测 → 操作识别 → 游戏逻辑 → 牌谱生成
    ↓         ↓        ↓         ↓         ↓         ↓
   MP4      Frame   Detection  Action   Validation  JSON
```

### 三层识别架构

#### 第一层：YOLO目标检测
```python
class YOLODetector:
    """检测和识别麻将牌位置"""
    def detect(self, frame):
        # 输出: [(x1,y1,x2,y2), tile_type, confidence]
        return detections
```

#### 第二层：操作识别
```python
class ActionRecognizer:
    """基于牌的变化识别操作"""
    def recognize_action(self, prev_state, curr_state):
        # 输出: 操作类型、执行玩家、涉及的牌
        return actions
```

#### 第三层：游戏逻辑验证
```python
class GameLogicValidator:
    """验证操作是否符合麻将规则"""
    def validate(self, action, game_state):
        # 输出: 是否有效 + 修正建议
        return is_valid, corrections
```

## 🎮 麻将操作识别详细方案

### 1. 摸牌检测 (Draw)

#### 视觉特征
```python
def detect_draw_action(prev_frame, curr_frame):
    """检测摸牌操作"""
    
    # 1. 手牌数量变化检测
    prev_hand_count = count_hand_tiles(prev_frame, player_id)
    curr_hand_count = count_hand_tiles(curr_frame, player_id)
    
    if curr_hand_count > prev_hand_count:
        # 2. 运动轨迹分析
        motion_vector = detect_motion(prev_frame, curr_frame)
        if motion_vector.direction == "deck_to_hand":
            
            # 3. 新增牌识别
            new_tile = identify_new_tile(prev_frame, curr_frame, player_id)
            
            return DrawAction(
                player_id=player_id,
                tile=new_tile,
                confidence=calculate_confidence([hand_count, motion, tile_id])
            )
```

#### 关键技术点
- **牌数统计**: 基于YOLO检测结果统计每个区域的牌数
- **运动检测**: 光流法检测从牌堆到手牌的运动
- **新牌识别**: 对比前后帧差异，识别新增的牌

### 2. 弃牌检测 (Discard)

#### 视觉特征
```python
def detect_discard_action(frame_sequence):
    """检测弃牌操作"""
    
    # 1. 弃牌区域变化
    discard_area_change = detect_discard_area_change(frame_sequence)
    
    # 2. 手牌到弃牌区运动
    motion_detected = detect_hand_to_discard_motion(frame_sequence)
    
    # 3. 识别弃的具体牌
    if discard_area_change and motion_detected:
        discarded_tile = identify_discarded_tile(frame_sequence)
        
        return DiscardAction(
            player_id=get_active_player(frame_sequence),
            tile=discarded_tile,
            timestamp=get_discard_timestamp(frame_sequence)
        )
```

#### 实现细节
- **区域监控**: 监控四个弃牌区域的变化
- **牌面识别**: 识别新出现在弃牌区的牌
- **时序分析**: 确保弃牌发生在摸牌之后

### 3. 碰牌检测 (Peng)

#### 多重验证机制
```python
def detect_peng_action(frame_sequence, ui_elements):
    """检测碰牌操作"""
    
    evidence = []
    
    # 1. UI按钮检测
    if ui_elements.peng_button_clicked:
        evidence.append(("ui_button", 0.9))
    
    # 2. 文字识别
    if detect_text_in_frame(frame_sequence, "碰"):
        evidence.append(("text_detection", 0.8))
    
    # 3. 手牌变化分析
    hand_change = analyze_hand_changes(frame_sequence)
    if hand_change.type == "meld_formed":
        evidence.append(("hand_analysis", 0.7))
    
    # 4. 音效检测（可选）
    if detect_peng_sound(audio_track):
        evidence.append(("audio", 0.6))
    
    # 综合判断
    total_confidence = calculate_weighted_confidence(evidence)
    
    if total_confidence > 0.7:
        return PengAction(
            player_id=identify_peng_player(frame_sequence),
            tile=identify_peng_tile(frame_sequence),
            source_player=identify_source_player(frame_sequence),
            confidence=total_confidence
        )
```

### 4. 杠牌检测 (Gang)

#### 杠牌类型识别
```python
def detect_gang_action(frame_sequence, game_state):
    """检测杠牌操作"""
    
    # 1. 基础杠牌检测
    gang_detected = detect_basic_gang_indicators(frame_sequence)
    
    if gang_detected:
        # 2. 分析杠牌类型
        gang_type = classify_gang_type(frame_sequence, game_state)
        
        if gang_type == GangType.MING_GANG:
            # 明杠：需要来源玩家
            source_player = identify_gang_source(frame_sequence)
            tile_count_change = -3  # 手牌减少3张
            
        elif gang_type == GangType.AN_GANG:
            # 暗杠：自己的4张牌
            source_player = None
            tile_count_change = -4  # 手牌减少4张
            
        elif gang_type == GangType.JIA_GANG:
            # 加杠：在已有的碰基础上加一张
            source_player = None
            tile_count_change = -1  # 手牌减少1张
        
        return GangAction(
            player_id=get_gang_player(frame_sequence),
            tile=identify_gang_tile(frame_sequence),
            gang_type=gang_type,
            source_player=source_player,
            hand_change=tile_count_change
        )
```

### 5. 胡牌检测 (Hu)

#### 胜利状态识别
```python
def detect_hu_action(frame_sequence, game_state):
    """检测胡牌操作"""
    
    # 1. 胜利特效检测
    win_effects = detect_win_effects(frame_sequence)
    
    # 2. 分数变化检测
    score_changes = detect_score_changes(frame_sequence)
    
    # 3. 胡牌类型分析
    hu_type = determine_hu_type(frame_sequence, game_state)
    
    # 4. 胡牌检验
    if win_effects.detected and score_changes.detected:
        
        winner = identify_winner(frame_sequence, score_changes)
        hu_tile = identify_hu_tile(frame_sequence, winner)
        
        return HuAction(
            player_id=winner,
            tile=hu_tile,
            hu_type=hu_type,  # "zimo" or "dianpao"
            dianpao_player=get_dianpao_player(frame_sequence) if hu_type == "dianpao" else None,
            score_changes=score_changes.values
        )
```

## 🛠️ 技术实现要点

### 1. YOLO模型训练

#### 数据集准备
```bash
# 目录结构
mahjong_dataset/
├── images/
│   ├── train/
│   ├── val/
│   └── test/
├── labels/
│   ├── train/
│   ├── val/
│   └── test/
└── data.yaml
```

#### 标注格式 (YOLO格式)
```
# 每个图片对应一个txt文件
# 格式: class_id center_x center_y width height
0 0.5 0.3 0.1 0.15    # 1万牌
1 0.7 0.3 0.1 0.15    # 2万牌
...
```

#### 训练脚本
```python
# 使用YOLOv5训练
python train.py --data mahjong.yaml --weights yolov5s.pt --epochs 100
```

### 2. 实时处理流水线

```python
class RealtimeProcessor:
    def __init__(self):
        self.yolo_detector = YOLODetector("mahjong_model.pt")
        self.action_recognizer = ActionRecognizer()
        self.state_tracker = GameStateTracker()
    
    def process_video_stream(self, video_path):
        cap = cv2.VideoCapture(video_path)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 1. YOLO检测
            detections = self.yolo_detector.detect(frame)
            
            # 2. 更新游戏状态
            game_state = self.state_tracker.update(detections)
            
            # 3. 识别操作
            actions = self.action_recognizer.detect_actions(
                game_state, frame
            )
            
            # 4. 保存结果
            for action in actions:
                self.save_action(action)
```

### 3. 多模态融合

```python
class MultiModalDetector:
    """融合多种检测方式"""
    
    def detect_action(self, frame, audio=None, ui_state=None):
        # 视觉检测
        visual_score = self.visual_detector.detect(frame)
        
        # 音频检测（可选）
        audio_score = self.audio_detector.detect(audio) if audio else 0
        
        # UI状态检测
        ui_score = self.ui_detector.detect(ui_state) if ui_state else 0
        
        # 加权融合
        final_score = (
            0.7 * visual_score + 
            0.2 * audio_score + 
            0.1 * ui_score
        )
        
        return final_score > 0.6
```

## 📊 性能优化策略

### 1. 模型优化
- **模型压缩**: 使用知识蒸馏减小模型大小
- **量化加速**: INT8量化提升推理速度
- **TensorRT**: GPU加速推理

### 2. 处理优化
- **关键帧提取**: 只处理有变化的帧
- **区域裁剪**: 只处理游戏区域，忽略无关部分
- **多线程**: 并行处理多个检测任务

### 3. 准确率提升
- **时序一致性**: 利用前后帧信息验证检测结果
- **规则约束**: 用麻将规则过滤不合理的检测
- **置信度阈值**: 动态调整检测阈值

## 🎯 最终效果预期

### 识别准确率目标
- **麻将牌识别**: 95%+
- **摸牌检测**: 90%+
- **弃牌检测**: 92%+
- **碰杠检测**: 85%+
- **胡牌检测**: 95%+

### 处理性能目标
- **实时处理**: 30 FPS
- **延迟**: <100ms
- **内存占用**: <2GB

这套整合方案将YOLO的强大检测能力与精细的操作识别结合，为腾讯欢乐麻将录像转牌谱提供了完整的技术解决方案！