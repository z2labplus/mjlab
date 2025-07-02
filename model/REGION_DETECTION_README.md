# 麻将区域检测 YOLOv8 训练指南

本指南将帮你使用 X-AnyLabeling 标注的数据训练 YOLOv8 模型，检测麻将游戏中的 5 个区域：`up`, `down`, `left`, `right`, `wind`。

## 📋 目录结构

```
/root/claude/hmjai/model/
├── all_labeled_images/               # X-AnyLabeling标注数据
│   ├── frame_000001.jpg
│   ├── frame_000001.json
│   └── ...
├── convert_xanylabeling_to_yolo.py  # 数据格式转换
├── train_region_detector.py        # 模型训练
├── test_region_detector.py         # 模型测试
├── run_region_training.py          # 一键训练流水线
└── REGION_DETECTION_README.md      # 本文档
```

## 🚀 快速开始

### 方法一：一键训练（推荐）

```bash
# 1. 安装依赖
pip install ultralytics opencv-python torch torchvision

# 2. 进入model目录
cd /root/claude/hmjai/model

# 3. 一键训练（使用默认参数）
python run_region_training.py

# 4. 自定义参数训练
python run_region_training.py --model_size s --epochs 200 --batch 32
```

### 方法二：分步执行

#### 步骤 1：转换数据格式
```bash
python convert_xanylabeling_to_yolo.py \
    --source ./all_labeled_images \
    --output ./yolo_dataset \
    --train_ratio 0.8
```

#### 步骤 2：训练模型
```bash
python train_region_detector.py \
    --dataset ./yolo_dataset \
    --model_size n \
    --epochs 100 \
    --batch 16
```

#### 步骤 3：测试模型
```bash
python test_region_detector.py \
    --model runs/train/mahjong_regions_*/weights/best.pt \
    --source test_image.jpg \
    --conf 0.5
```

## ⚙️ 参数说明

### 模型大小选择
- `n` (nano): 最快，文件最小 (~6MB)，准确率较低
- `s` (small): 平衡选择 (~22MB)，速度和准确率适中
- `m` (medium): 推荐选择 (~52MB)，准确率较高
- `l` (large): 高准确率 (~131MB)，速度较慢
- `x` (xlarge): 最高准确率 (~218MB)，速度最慢

### 训练参数
- `--epochs`: 训练轮数，建议 100-300
- `--batch`: 批大小，根据 GPU 内存调整（4-32）
- `--imgsz`: 图像尺寸，默认 640
- `--device`: 设备选择，auto/cpu/cuda

### 检测参数
- `--conf`: 置信度阈值，0.1-0.9
- `--interval`: 视频采样间隔

## 📊 训练监控

### 查看训练进度
```bash
# 实时查看训练日志
tail -f runs/train/mahjong_regions_*/train.log

# 使用 TensorBoard（如果可用）
tensorboard --logdir runs/train
```

### 训练结果文件
```
runs/train/mahjong_regions_YYYYMMDD_HHMMSS/
├── weights/
│   ├── best.pt          # 最佳模型
│   └── last.pt          # 最后一轮模型
├── results.png          # 训练曲线
├── confusion_matrix.png # 混淆矩阵
├── F1_curve.png        # F1曲线
└── args.yaml           # 训练参数
```

## 🎯 模型评估

### 评估指标说明
- **mAP50**: 在 IoU=0.5 时的平均精度
- **mAP50-95**: 在 IoU=0.5-0.95 时的平均精度
- **Precision**: 精确率
- **Recall**: 召回率

### 仅评估模型
```bash
python train_region_detector.py \
    --eval_only \
    --model_path runs/train/mahjong_regions_*/weights/best.pt
```

## 🧪 模型测试

### 测试单张图片
```bash
python test_region_detector.py \
    --model runs/train/mahjong_regions_*/weights/best.pt \
    --source test_image.jpg \
    --output result_image.jpg \
    --conf 0.5
```

### 测试视频
```bash
python test_region_detector.py \
    --model runs/train/mahjong_regions_*/weights/best.pt \
    --source test_video.mp4 \
    --output result_video.mp4 \
    --interval 30 \
    --analysis
```

## 📈 性能优化建议

### 提高准确率
1. **增加训练数据**：标注更多样本
2. **数据增强**：旋转、缩放、亮度调整
3. **使用更大模型**：从 n → s → m → l
4. **增加训练轮数**：100 → 200 → 300
5. **调整学习率**：使用学习率调度器

### 提高速度
1. **使用小模型**：n 或 s
2. **降低图像分辨率**：640 → 416 → 320
3. **模型量化**：FP16 或 INT8
4. **模型蒸馏**：大模型教小模型

## 🔧 常见问题解决

### 1. GPU 内存不足
```bash
# 减小批大小
python train_region_detector.py --batch 8

# 或使用 CPU
python train_region_detector.py --device cpu
```

### 2. 训练不收敛
```bash
# 降低学习率
# 检查数据标注质量
# 增加训练数据量
```

### 3. 检测结果不准确
```bash
# 调整置信度阈值
python test_region_detector.py --conf 0.3

# 使用更大的模型
python train_region_detector.py --model_size m
```

### 4. 数据转换失败
```bash
# 检查 JSON 文件格式
# 确保图片和标注文件对应
# 检查类别名称是否正确
```

## 📝 自定义配置

### 修改类别名称
编辑 `convert_xanylabeling_to_yolo.py` 中的 `class_names`：
```python
self.class_names = ['up', 'down', 'left', 'right', 'wind']
```

### 修改颜色方案
编辑 `test_region_detector.py` 中的 `colors`：
```python
self.colors = {
    'up': (0, 255, 0),      # 绿色
    'down': (0, 0, 255),    # 红色
    # ...
}
```

## 🚀 部署模型

### 导出为 ONNX
```bash
python train_region_detector.py \
    --export \
    --model_path runs/train/mahjong_regions_*/weights/best.pt
```

### 集成到现有系统
```python
from ultralytics import YOLO

# 加载模型
model = YOLO('path/to/best.pt')

# 推理
results = model('image.jpg', conf=0.5)

# 处理结果
for result in results:
    boxes = result.boxes
    for box in boxes:
        cls = int(box.cls)
        conf = float(box.conf)
        xyxy = box.xyxy[0].tolist()
        print(f"Region {cls}: {conf:.3f} at {xyxy}")
```

## 📞 技术支持

如果遇到问题，请检查：
1. Python 环境是否正确安装
2. GPU 驱动和 CUDA 版本
3. 数据路径是否正确
4. 标注数据格式是否符合要求

## 🎉 预期结果

成功训练后，你将获得：
- 可以检测 5 个麻将区域的 YOLOv8 模型
- mAP50 达到 85%+ 的检测精度
- 支持实时视频检测的推理速度
- 完整的训练和测试流水线

训练完成后，模型可以集成到你的麻将视频分析系统中，自动识别游戏区域并进行后续的牌谱分析！