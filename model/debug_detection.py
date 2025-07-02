#!/usr/bin/env python3
"""
调试检测结果，分析为什么模型无法检测到麻将牌
"""

import cv2
import numpy as np
from pathlib import Path
import logging
import argparse
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DetectionDebugger:
    """检测调试器"""
    
    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """加载模型"""
        try:
            from ultralytics import YOLO
            self.model = YOLO(str(self.model_path))
            logger.info(f"✅ 模型加载成功: {self.model_path}")
        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            raise
    
    def test_multiple_thresholds(self, image_path: Path, thresholds: List[float] = None):
        """测试多个置信度阈值"""
        if thresholds is None:
            thresholds = [0.01, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5]
        
        logger.info(f"🔍 测试多个置信度阈值: {image_path.name}")
        
        results_summary = []
        
        for threshold in thresholds:
            results = self.model(str(image_path), conf=threshold, verbose=False)
            
            detections = 0
            for result in results:
                if result.boxes is not None:
                    detections = len(result.boxes)
                    break
            
            results_summary.append({
                'threshold': threshold,
                'detections': detections
            })
            
            logger.info(f"  置信度 {threshold:.2f}: {detections} 个检测")
        
        return results_summary
    
    def visualize_low_confidence_detections(self, image_path: Path, threshold: float = 0.01):
        """可视化低置信度检测结果"""
        logger.info(f"🎨 可视化低置信度检测 (threshold={threshold}): {image_path.name}")
        
        # 读取图像
        image = cv2.imread(str(image_path))
        if image is None:
            logger.error(f"无法读取图像: {image_path}")
            return None
        
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 运行检测
        results = self.model(str(image_path), conf=threshold, verbose=False)
        
        # 绘制检测结果
        annotated_image = image_rgb.copy()
        
        detection_info = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for i in range(len(boxes)):
                    # 获取坐标和信息
                    x1, y1, x2, y2 = boxes.xyxy[i].cpu().numpy()
                    conf = float(boxes.conf[i].cpu().numpy())
                    cls = int(boxes.cls[i].cpu().numpy())
                    
                    # 颜色根据置信度变化
                    if conf >= 0.5:
                        color = (0, 255, 0)  # 绿色 - 高置信度
                    elif conf >= 0.25:
                        color = (255, 255, 0)  # 黄色 - 中置信度
                    else:
                        color = (255, 0, 0)  # 红色 - 低置信度
                    
                    # 绘制边界框
                    cv2.rectangle(annotated_image, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                    
                    # 添加标签
                    label = f"cls_{cls}_{conf:.2f}"
                    cv2.putText(annotated_image, label, (int(x1), int(y1)-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                    
                    detection_info.append({
                        'bbox': [x1, y1, x2, y2],
                        'confidence': conf,
                        'class': cls,
                        'size': f"{int(x2-x1)}x{int(y2-y1)}"
                    })
        
        # 保存可视化结果
        output_path = image_path.parent / f"debug_{image_path.stem}_conf{threshold}.jpg"
        cv2.imwrite(str(output_path), cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
        
        logger.info(f"✅ 可视化结果保存: {output_path}")
        logger.info(f"📊 检测统计: {len(detection_info)} 个对象")
        
        for i, info in enumerate(detection_info):
            logger.info(f"  检测{i+1}: 置信度={info['confidence']:.3f}, 尺寸={info['size']}, 类别={info['class']}")
        
        return annotated_image, detection_info
    
    def analyze_training_vs_real_images(self, training_image_dir: Path, real_image_path: Path):
        """分析训练图像与真实图像的差异"""
        logger.info("🔍 分析训练数据与真实图像的差异...")
        
        # 分析真实图像
        real_image = cv2.imread(str(real_image_path))
        real_rgb = cv2.cvtColor(real_image, cv2.COLOR_BGR2RGB)
        
        logger.info(f"真实图像: {real_image_path.name}")
        logger.info(f"  尺寸: {real_image.shape[1]}x{real_image.shape[0]}")
        logger.info(f"  亮度: {np.mean(real_rgb):.1f}")
        
        # 分析训练图像样本
        training_images = list(training_image_dir.glob("*.jpg"))[:5]  # 分析前5张
        
        logger.info(f"\n训练图像样本分析:")
        for train_img_path in training_images:
            train_img = cv2.imread(str(train_img_path))
            if train_img is not None:
                train_rgb = cv2.cvtColor(train_img, cv2.COLOR_BGR2RGB)
                logger.info(f"  {train_img_path.name}: 尺寸={train_img.shape[1]}x{train_img.shape[0]}, 亮度={np.mean(train_rgb):.1f}")
    
    def suggest_improvements(self, image_path: Path):
        """提供改进建议"""
        logger.info("💡 改进建议:")
        
        # 测试多个阈值
        results = self.test_multiple_thresholds(image_path)
        
        max_detections = max(r['detections'] for r in results)
        best_threshold = None
        
        for r in results:
            if r['detections'] == max_detections and max_detections > 0:
                best_threshold = r['threshold']
                break
        
        if max_detections == 0:
            logger.info("1. ❗ 模型完全无法检测到目标，建议:")
            logger.info("   - 检查训练数据质量")
            logger.info("   - 使用真实游戏截图作为背景进行合成")
            logger.info("   - 调整麻将牌的外观使其更接近真实游戏")
            logger.info("   - 考虑使用更多真实标注数据")
        else:
            logger.info(f"2. ✅ 在置信度 {best_threshold} 时检测到 {max_detections} 个对象")
            logger.info("   建议降低置信度阈值或改进训练数据")
        
        return best_threshold

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='调试检测结果')
    parser.add_argument('--model', default='runs/train/simple_mahjong_tiles_n/weights/best.pt',
                       help='模型路径')
    parser.add_argument('--image', required=True,
                       help='要调试的图像路径')
    parser.add_argument('--training_dir', default='simple_synthetic_dataset/images',
                       help='训练图像目录')
    
    args = parser.parse_args()
    
    # 检查文件
    model_path = Path(args.model)
    image_path = Path(args.image)
    training_dir = Path(args.training_dir)
    
    if not model_path.exists():
        logger.error(f"❌ 模型文件不存在: {model_path}")
        return
    
    if not image_path.exists():
        logger.error(f"❌ 图像文件不存在: {image_path}")
        return
    
    # 创建调试器
    debugger = DetectionDebugger(str(model_path))
    
    # 1. 测试多个置信度阈值
    logger.info("=" * 50)
    logger.info("🔍 步骤1: 测试多个置信度阈值")
    results = debugger.test_multiple_thresholds(image_path)
    
    # 2. 可视化低置信度检测
    logger.info("=" * 50)
    logger.info("🎨 步骤2: 可视化低置信度检测")
    debugger.visualize_low_confidence_detections(image_path, 0.01)
    debugger.visualize_low_confidence_detections(image_path, 0.1)
    
    # 3. 分析训练数据vs真实数据
    if training_dir.exists():
        logger.info("=" * 50)
        logger.info("📊 步骤3: 分析训练数据与真实图像差异")
        debugger.analyze_training_vs_real_images(training_dir, image_path)
    
    # 4. 提供改进建议
    logger.info("=" * 50)
    logger.info("💡 步骤4: 改进建议")
    best_threshold = debugger.suggest_improvements(image_path)
    
    logger.info("=" * 50)
    logger.info("✅ 调试完成!")
    logger.info(f"📁 查看生成的调试图像: debug_{image_path.stem}_conf*.jpg")

if __name__ == "__main__":
    main()