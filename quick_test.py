#!/usr/bin/env python3
"""
快速测试脚本 - 验证YOLOv8麻将检测系统
"""

import cv2
import numpy as np
import sys
from pathlib import Path
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def check_dependencies():
    """检查依赖包"""
    logger.info("🔍 检查依赖包...")
    
    try:
        import torch
        logger.info(f"✅ PyTorch: {torch.__version__}")
        logger.info(f"   CUDA可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            logger.info(f"   GPU数量: {torch.cuda.device_count()}")
            logger.info(f"   当前GPU: {torch.cuda.current_device()}")
    except ImportError:
        logger.error("❌ PyTorch未安装")
        return False
    
    try:
        from ultralytics import YOLO
        logger.info("✅ Ultralytics YOLO")
    except ImportError:
        logger.error("❌ Ultralytics未安装，请运行: pip install ultralytics")
        return False
    
    try:
        import cv2
        logger.info(f"✅ OpenCV: {cv2.__version__}")
    except ImportError:
        logger.error("❌ OpenCV未安装")
        return False
    
    return True

def test_yolo_model():
    """测试YOLO模型加载"""
    logger.info("\n🧪 测试YOLO模型...")
    
    try:
        from ultralytics import YOLO
        
        # 尝试加载预训练模型
        model = YOLO('yolov8n.pt')  # 自动下载nano模型
        logger.info("✅ YOLOv8模型加载成功")
        
        # 测试推理
        test_image = np.zeros((640, 640, 3), dtype=np.uint8)
        results = model(test_image, verbose=False)
        logger.info("✅ 模型推理测试成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ YOLO模型测试失败: {e}")
        return False

def test_video_reading(video_path: str):
    """测试视频读取"""
    logger.info(f"\n📹 测试视频读取: {video_path}")
    
    if not Path(video_path).exists():
        logger.error(f"❌ 视频文件不存在: {video_path}")
        return False
    
    try:
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            logger.error("❌ 无法打开视频文件")
            return False
        
        # 获取视频信息
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        
        logger.info(f"✅ 视频信息:")
        logger.info(f"   分辨率: {width}x{height}")
        logger.info(f"   帧率: {fps:.1f} FPS")
        logger.info(f"   总帧数: {frame_count}")
        logger.info(f"   时长: {duration:.1f} 秒")
        
        # 读取第一帧
        ret, frame = cap.read()
        if ret:
            logger.info("✅ 成功读取视频帧")
        else:
            logger.error("❌ 无法读取视频帧")
            return False
        
        cap.release()
        return True
        
    except Exception as e:
        logger.error(f"❌ 视频读取测试失败: {e}")
        return False

def quick_detection_test(video_path: str = None):
    """快速检测测试"""
    logger.info("\n🚀 运行快速检测测试...")
    
    try:
        # 导入我们的检测器
        from yolov8_mahjong_detector import YOLOv8MahjongDetector
        
        # 创建检测器
        detector = YOLOv8MahjongDetector()
        logger.info("✅ 麻将检测器创建成功")
        
        if video_path and Path(video_path).exists():
            # 测试视频的前几帧
            cap = cv2.VideoCapture(video_path)
            
            for i in range(3):  # 测试前3帧
                ret, frame = cap.read()
                if not ret:
                    break
                
                logger.info(f"   测试第{i+1}帧...")
                detections = detector.detect_tiles_in_frame(frame, i, i * 0.5)
                logger.info(f"   检测到 {len(detections)} 个对象")
                
                # 显示检测结果详情
                for det in detections[:3]:  # 只显示前3个
                    logger.info(f"     - {det.tile_type}: 置信度{det.confidence:.2f}, 区域P{det.player_zone}")
            
            cap.release()
        else:
            # 使用测试图像
            test_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
            detections = detector.detect_tiles_in_frame(test_frame)
            logger.info(f"✅ 测试图像检测完成，检测到 {len(detections)} 个对象")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 检测测试失败: {e}")
        logger.error("   可能的原因:")
        logger.error("   1. 依赖包未正确安装")
        logger.error("   2. GPU内存不足")
        logger.error("   3. 模型下载失败")
        return False

def installation_guide():
    """安装指南"""
    logger.info("\n📋 安装指南:")
    logger.info("1. 安装基础依赖:")
    logger.info("   pip install ultralytics opencv-python torch torchvision")
    logger.info("")
    logger.info("2. 如果有NVIDIA GPU，安装CUDA版本:")
    logger.info("   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118")
    logger.info("")
    logger.info("3. 验证安装:")
    logger.info("   python quick_test.py")
    logger.info("")
    logger.info("4. 处理视频:")
    logger.info("   python yolov8_mahjong_detector.py --video your_video.mp4")

def main():
    """主测试函数"""
    logger.info("🎯 YOLOv8麻将检测系统 - 快速测试")
    logger.info("=" * 50)
    
    # 检查命令行参数
    video_path = None
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        logger.info(f"测试视频: {video_path}")
    
    # 执行测试步骤
    steps = [
        ("依赖检查", lambda: check_dependencies()),
        ("YOLO模型测试", lambda: test_yolo_model()),
    ]
    
    if video_path:
        steps.append(("视频读取测试", lambda: test_video_reading(video_path)))
    
    steps.append(("快速检测测试", lambda: quick_detection_test(video_path)))
    
    # 运行所有测试
    all_passed = True
    for step_name, step_func in steps:
        try:
            success = step_func()
            if not success:
                all_passed = False
                break
        except Exception as e:
            logger.error(f"❌ {step_name}失败: {e}")
            all_passed = False
            break
    
    logger.info("\n" + "=" * 50)
    if all_passed:
        logger.info("🎉 所有测试通过！系统准备就绪")
        logger.info("\n下一步:")
        logger.info("1. 准备训练数据:")
        logger.info("   python train_data_collector.py --mode extract --video your_video.mp4")
        logger.info("2. 标注数据:")
        logger.info("   python train_data_collector.py --mode annotate")
        logger.info("3. 处理完整视频:")
        logger.info("   python yolov8_mahjong_detector.py --video your_video.mp4 --output replay.json")
    else:
        logger.error("❌ 测试失败，请检查安装")
        installation_guide()

if __name__ == "__main__":
    main()