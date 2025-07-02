# 腾讯欢乐麻将录像转牌谱技术方案

## 🎯 总体目标
从腾讯欢乐麻将游戏录像中自动提取牌谱数据，生成可在网站中回放的JSON格式牌谱文件。

## 📋 技术方案概述

### 方案选择对比

| 方案 | 技术难度 | 准确率 | 开发周期 | 推荐度 |
|------|----------|--------|----------|--------|
| 计算机视觉识别 | ⭐⭐⭐⭐ | 85-95% | 2-3周 | ⭐⭐⭐⭐⭐ |
| OCR文字识别 | ⭐⭐⭐ | 70-85% | 1-2周 | ⭐⭐⭐ |
| 手动标注辅助 | ⭐⭐ | 99% | 4-6周 | ⭐⭐ |

**推荐方案**: 计算机视觉识别 + 深度学习

## 🚀 实施步骤

### 阶段一：数据准备与环境搭建 (3-5天)

#### 1.1 环境配置
```bash
# 安装Python依赖
pip install opencv-python tensorflow numpy scikit-learn
pip install pytesseract pillow matplotlib
pip install ffmpeg-python

# 安装系统依赖
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim
sudo apt-get install ffmpeg

# macOS:
brew install tesseract tesseract-lang
brew install ffmpeg
```

#### 1.2 录像数据收集
```bash
# 创建数据目录
mkdir -p data/{raw_videos,training_images,processed_frames}

# 收集要求:
# - 录像格式: MP4, AVI, MOV
# - 分辨率: 1280x720 或更高
# - 帧率: 30fps 或更高
# - 时长: 完整一局游戏 (10-30分钟)
# - 数量: 至少10个不同的游戏录像
```

#### 1.3 界面区域标定
- 分析腾讯欢乐麻将界面布局
- 标记关键区域坐标:
  - 四个玩家手牌区域
  - 弃牌堆区域
  - 碰杠牌显示区域
  - 操作提示区域
  - 分数显示区域
  - 玩家名称区域

### 阶段二：麻将牌识别模型训练 (7-10天)

#### 2.1 训练数据收集
```python
# 运行数据收集脚本
python collect_training_data.py --video_dir data/raw_videos
```

**数据收集策略:**
- 从录像中自动提取麻将牌图片
- 每种牌型至少收集200张图片
- 包含不同光照、角度、清晰度的样本
- 总计约5400张图片 (27种牌型 × 200张)

#### 2.2 数据标注与预处理
```python
# 自动标注脚本
python auto_label_tiles.py

# 手动验证和修正
python manual_review.py
```

#### 2.3 模型训练
```python
# 训练麻将牌识别模型
python train_tile_recognition.py --epochs 100 --batch_size 32

# 预期结果:
# - 训练准确率: >95%
# - 验证准确率: >90%
# - 模型大小: <50MB
```

### 阶段三：视频分析系统开发 (5-7天)

#### 3.1 视频预处理
```python
class VideoPreprocessor:
    def extract_keyframes(self, video_path):
        """提取关键帧"""
        # 检测场景变化
        # 提取操作发生时刻的帧
        
    def stabilize_video(self, video_path):
        """视频稳定化处理"""
        # 减少晃动影响
        # 提高识别准确率
```

#### 3.2 游戏状态跟踪
```python
class GameStateTracker:
    def __init__(self):
        self.current_state = {
            'player_hands': [[] for _ in range(4)],
            'discard_piles': [[] for _ in range(4)],
            'melds': [[] for _ in range(4)],
            'current_player': 0,
            'deck_remaining': 108
        }
    
    def update_state(self, action):
        """根据识别的操作更新游戏状态"""
        pass
```

#### 3.3 操作检测与识别
```python
# 关键技术点:
1. 动作检测: 识别摸牌、弃牌、碰杠等操作
2. 牌型识别: 使用训练好的CNN模型
3. 时序分析: 确保操作的逻辑正确性
4. 异常处理: 处理识别错误和模糊情况
```

### 阶段四：牌谱生成与验证 (3-5天)

#### 4.1 牌谱数据结构
```json
{
  "game_info": {
    "game_id": "video_game_123456",
    "start_time": "2024-01-15T14:30:00",
    "duration": 1800,
    "player_count": 4,
    "game_mode": "xuezhan_daodi"
  },
  "players": [
    {
      "id": 0,
      "name": "玩家1",
      "position": 0,
      "initial_hand": ["1万", "2万", "3万", ...],
      "missing_suit": "万",
      "final_score": 150,
      "is_winner": true
    }
  ],
  "actions": [
    {
      "sequence": 1,
      "timestamp": "2024-01-15T14:30:05",
      "player_id": 0,
      "action_type": "draw",
      "card": "5万",
      "score_change": 0
    }
  ]
}
```

#### 4.2 数据验证与校正
```python
class ReplayValidator:
    def validate_game_logic(self, replay_data):
        """验证游戏逻辑正确性"""
        # 检查牌数是否正确 (108张)
        # 验证操作序列是否合理
        # 确认胜负结果正确性
        
    def auto_correct_errors(self, replay_data):
        """自动修正明显错误"""
        # 修正识别错误的牌型
        # 补全缺失的操作
        # 调整时间戳
```

### 阶段五：系统集成与优化 (3-5天)

#### 5.1 前端集成
```typescript
// 修改现有的ReplayImporter组件
interface VideoReplayImporter {
  uploadVideo(file: File): Promise<string>;
  processVideo(videoId: string): Promise<ReplayData>;
  getProcessingStatus(videoId: string): Promise<ProcessingStatus>;
}
```

#### 5.2 批量处理系统
```python
# 批量处理多个视频
python batch_process.py --input_dir videos/ --output_dir replays/

# 并行处理支持
# 进度监控
# 错误恢复
```

## 📊 预期性能指标

### 识别准确率
- **麻将牌识别**: 90-95%
- **操作类型识别**: 85-90%
- **玩家名称识别**: 80-85%
- **整体牌谱准确率**: 80-85%

### 处理性能
- **处理速度**: 1分钟录像 → 2-5分钟处理时间
- **内存占用**: <4GB
- **模型大小**: <100MB

### 支持的录像格式
- **视频格式**: MP4, AVI, MOV
- **分辨率**: 720p 及以上
- **帧率**: 24fps 及以上
- **时长**: 5分钟 - 60分钟

## 🛠️ 核心技术实现

### 1. 视频关键帧提取
```python
def extract_action_frames(video_path):
    """提取包含操作的关键帧"""
    cap = cv2.VideoCapture(video_path)
    frames = []
    
    # 使用光流法检测运动
    # 在操作区域检测变化
    # 提取变化时刻的帧
    
    return frames
```

### 2. 麻将牌区域检测
```python
def detect_tile_regions(frame):
    """检测帧中的麻将牌区域"""
    # 使用边缘检测
    edges = cv2.Canny(frame, 50, 150)
    
    # 查找轮廓
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 筛选麻将牌大小的矩形区域
    tile_regions = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if is_tile_size(w, h):
            tile_regions.append((x, y, w, h))
    
    return tile_regions
```

### 3. 深度学习识别
```python
def recognize_tiles(tile_images):
    """批量识别麻将牌"""
    model = load_model('mahjong_tile_model.h5')
    
    predictions = []
    for img in tile_images:
        # 预处理
        processed = preprocess_tile_image(img)
        
        # 预测
        pred = model.predict(processed)
        tile_type = decode_prediction(pred)
        
        predictions.append(tile_type)
    
    return predictions
```

## 🔧 部署与使用

### 1. 快速开始
```bash
# 1. 克隆项目
git clone <repository>
cd hmjai

# 2. 安装依赖
pip install -r requirements.txt

# 3. 下载预训练模型
wget https://example.com/mahjong_model.h5

# 4. 处理单个视频
python video_analyzer.py --input game_video.mp4 --output replay.json

# 5. 在网站中导入牌谱
# 上传生成的 replay.json 文件
```

### 2. API 接口
```python
# Flask API
@app.route('/api/process_video', methods=['POST'])
def process_video():
    video_file = request.files['video']
    
    # 保存视频文件
    video_path = save_uploaded_file(video_file)
    
    # 异步处理
    task_id = process_video_async(video_path)
    
    return {'task_id': task_id, 'status': 'processing'}

@app.route('/api/get_replay/<task_id>')
def get_replay(task_id):
    result = get_processing_result(task_id)
    
    if result['status'] == 'completed':
        return result['replay_data']
    else:
        return {'status': result['status'], 'progress': result['progress']}
```

## 🚨 注意事项与限制

### 技术限制
1. **识别准确率**: 受视频质量影响较大
2. **处理时间**: 长视频处理时间较长
3. **硬件要求**: 需要GPU加速训练和推理

### 法律合规
1. **版权问题**: 确保录像来源合法
2. **隐私保护**: 处理个人信息需谨慎
3. **使用范围**: 仅用于个人学习和研究

### 质量保证
1. **人工验证**: 重要比赛需人工校对
2. **多模型投票**: 使用多个模型提高准确率
3. **渐进式改进**: 根据反馈持续优化

## 📈 项目里程碑

- **Week 1**: 环境搭建 + 数据收集
- **Week 2**: 模型训练 + 基础识别
- **Week 3**: 视频分析系统开发
- **Week 4**: 牌谱生成 + 系统集成
- **Week 5**: 测试优化 + 文档完善

## 🎉 预期成果

完成后将具备以下能力:
1. ✅ 自动处理腾讯欢乐麻将录像
2. ✅ 生成标准JSON格式牌谱
3. ✅ 在现有网站中完美回放
4. ✅ 支持批量处理多个录像
5. ✅ 提供Web界面上传和处理

这套方案将大大降低牌谱数据获取的门槛，为麻将爱好者提供便利的工具！