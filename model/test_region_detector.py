#!/usr/bin/env python3
"""
麻将区域检测器推理测试脚本
使用训练好的模型检测视频中的区域
"""

import cv2
import numpy as np
from pathlib import Path
import logging
import json
from datetime import datetime
from typing import List, Dict, Tuple
from ultralytics import YOLO
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MahjongRegionDetector:
    """麻将区域检测器"""
    
    def __init__(self, model_path: str, conf_threshold: float = 0.5):
        self.model_path = Path(model_path)
        self.conf_threshold = conf_threshold
        
        # 区域名称映射
        self.region_names = ['up', 'down', 'left', 'right', 'wind']
        
        # 加载模型
        self.load_model()
        
        # 可视化配置
        self.colors = {
            'up': (0, 255, 0),      # 绿色
            'down': (0, 0, 255),    # 红色
            'left': (255, 0, 0),    # 蓝色
            'right': (255, 255, 0), # 青色
            'wind': (255, 0, 255)   # 洋红色
        }
    
    def load_model(self):
        """加载训练好的模型"""
        logger.info(f"🤖 加载模型: {self.model_path}")
        
        try:
            self.model = YOLO(str(self.model_path))
            logger.info("✅ 模型加载成功")
            
            # 显示模型信息
            logger.info(f"   置信度阈值: {self.conf_threshold}")
            logger.info(f"   支持的区域: {self.region_names}")
            
        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            raise
    
    def detect_regions_in_frame(self, frame: np.ndarray) -> List[Dict]:
        """
        在单帧中检测区域
        
        Args:
            frame: 输入图像
            
        Returns:
            检测结果列表
        """
        try:
            # YOLO推理
            results = self.model(frame, conf=self.conf_threshold, verbose=False)
            
            detections = []
            
            if results and len(results) > 0:
                result = results[0]
                
                if result.boxes is not None:
                    boxes = result.boxes.xyxy.cpu().numpy()
                    confs = result.boxes.conf.cpu().numpy()
                    classes = result.boxes.cls.cpu().numpy()
                    
                    for box, conf, cls in zip(boxes, confs, classes):
                        x1, y1, x2, y2 = map(int, box)
                        class_id = int(cls)
                        
                        if class_id < len(self.region_names):
                            region_name = self.region_names[class_id]
                            
                            detection = {
                                'region': region_name,
                                'confidence': float(conf),
                                'bbox': [x1, y1, x2, y2],
                                'center': [(x1 + x2) // 2, (y1 + y2) // 2],
                                'area': (x2 - x1) * (y2 - y1)
                            }
                            detections.append(detection)
            
            return detections
            
        except Exception as e:
            logger.error(f"区域检测失败: {e}")
            return []
    
    def draw_detections(self, frame: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """
        在图像上绘制检测结果
        
        Args:
            frame: 输入图像
            detections: 检测结果
            
        Returns:
            标注后的图像
        """
        annotated_frame = frame.copy()
        
        for det in detections:
            region = det['region']
            confidence = det['confidence']
            x1, y1, x2, y2 = det['bbox']
            
            # 获取颜色
            color = self.colors.get(region, (128, 128, 128))
            
            # 绘制边界框
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            
            # 绘制标签
            label = f"{region}: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            
            # 标签背景
            cv2.rectangle(annotated_frame, 
                         (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), 
                         color, -1)
            
            # 标签文字
            cv2.putText(annotated_frame, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return annotated_frame
    
    def test_single_image(self, image_path: str, output_path: str = None) -> Dict:
        """
        测试单张图像
        
        Args:
            image_path: 图像路径
            output_path: 输出路径
            
        Returns:
            检测结果
        """
        logger.info(f"🖼️  测试图像: {image_path}")
        
        # 读取图像
        frame = cv2.imread(image_path)
        if frame is None:
            logger.error(f"无法读取图像: {image_path}")
            return {}
        
        # 检测区域
        detections = self.detect_regions_in_frame(frame)
        
        # 绘制结果
        annotated_frame = self.draw_detections(frame, detections)
        
        # 保存结果
        if output_path:
            cv2.imwrite(output_path, annotated_frame)
            logger.info(f"结果已保存: {output_path}")
        
        # 显示检测结果
        logger.info(f"检测到 {len(detections)} 个区域:")
        for det in detections:
            logger.info(f"  - {det['region']}: 置信度 {det['confidence']:.3f}")
        
        return {
            'image_path': image_path,
            'detections': detections,
            'annotated_frame': annotated_frame
        }
    
    def test_video(self, video_path: str, output_path: str = None, 
                   sample_interval: int = 30) -> Dict:
        """
        测试视频
        
        Args:
            video_path: 视频路径
            output_path: 输出视频路径
            sample_interval: 采样间隔（帧）
            
        Returns:
            检测统计结果
        """
        logger.info(f"🎬 测试视频: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"无法打开视频: {video_path}")
            return {}
        
        # 获取视频信息
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        logger.info(f"视频信息: {width}x{height}, {fps}fps, {total_frames}帧")
        
        # 设置输出视频写入器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = None
        if output_path:
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # 统计信息
        frame_count = 0
        detection_stats = {region: 0 for region in self.region_names}
        all_detections = []
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 按间隔采样处理
                if frame_count % sample_interval == 0:
                    # 检测区域
                    detections = self.detect_regions_in_frame(frame)
                    
                    # 统计检测结果
                    for det in detections:
                        detection_stats[det['region']] += 1
                    
                    # 记录检测结果
                    all_detections.append({
                        'frame': frame_count,
                        'timestamp': frame_count / fps,
                        'detections': detections
                    })
                    
                    # 绘制检测结果
                    annotated_frame = self.draw_detections(frame, detections)
                    
                    # 显示进度
                    if frame_count % (sample_interval * 10) == 0:
                        progress = frame_count / total_frames * 100
                        logger.info(f"处理进度: {progress:.1f}%")
                else:
                    annotated_frame = frame
                
                # 写入输出视频
                if out is not None:
                    out.write(annotated_frame)
                
                frame_count += 1
            
        finally:
            cap.release()
            if out is not None:
                out.release()
        
        logger.info("✅ 视频处理完成")
        logger.info("📊 检测统计:")
        for region, count in detection_stats.items():
            logger.info(f"  {region}: {count} 次")
        
        return {
            'video_path': video_path,
            'total_frames': total_frames,
            'processed_frames': len(all_detections),
            'detection_stats': detection_stats,
            'all_detections': all_detections
        }
    
    def analyze_region_stability(self, detections_history: List[Dict]) -> Dict:
        """
        分析区域检测的稳定性
        
        Args:
            detections_history: 历史检测结果
            
        Returns:
            稳定性分析结果
        """
        region_positions = {region: [] for region in self.region_names}
        
        # 收集每个区域的位置信息
        for frame_data in detections_history:
            detected_regions = {det['region']: det['center'] for det in frame_data['detections']}
            
            for region in self.region_names:
                if region in detected_regions:
                    region_positions[region].append(detected_regions[region])
                else:
                    region_positions[region].append(None)
        
        # 计算稳定性指标
        stability_analysis = {}
        
        for region, positions in region_positions.items():
            valid_positions = [pos for pos in positions if pos is not None]
            
            if len(valid_positions) > 1:
                # 计算位置变化
                position_changes = []
                for i in range(1, len(valid_positions)):
                    prev_pos = valid_positions[i-1]
                    curr_pos = valid_positions[i]
                    change = np.sqrt((curr_pos[0] - prev_pos[0])**2 + (curr_pos[1] - prev_pos[1])**2)
                    position_changes.append(change)
                
                stability_analysis[region] = {
                    'detection_rate': len(valid_positions) / len(positions),
                    'avg_position': [np.mean([pos[0] for pos in valid_positions]),
                                   np.mean([pos[1] for pos in valid_positions])],
                    'position_variance': np.var(position_changes) if position_changes else 0,
                    'max_movement': max(position_changes) if position_changes else 0
                }
            else:
                stability_analysis[region] = {
                    'detection_rate': len(valid_positions) / len(positions),
                    'avg_position': valid_positions[0] if valid_positions else None,
                    'position_variance': 0,
                    'max_movement': 0
                }
        
        return stability_analysis

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='麻将区域检测器测试')
    parser.add_argument('--model', required=True, help='模型路径')
    parser.add_argument('--source', required=True, help='输入源（图片或视频路径）')
    parser.add_argument('--output', help='输出路径')
    parser.add_argument('--conf', type=float, default=0.5, help='置信度阈值')
    parser.add_argument('--interval', type=int, default=30, help='视频采样间隔')
    parser.add_argument('--analysis', action='store_true', help='进行稳定性分析')
    
    args = parser.parse_args()
    
    # 创建检测器
    detector = MahjongRegionDetector(args.model, args.conf)
    
    source_path = Path(args.source)
    
    if source_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
        # 图片测试
        output_path = args.output or f"output_{source_path.stem}_result{source_path.suffix}"
        result = detector.test_single_image(str(source_path), output_path)
        
    elif source_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv']:
        # 视频测试
        output_path = args.output or f"output_{source_path.stem}_result.mp4"
        result = detector.test_video(str(source_path), output_path, args.interval)
        
        # 稳定性分析
        if args.analysis and 'all_detections' in result:
            logger.info("📈 进行稳定性分析...")
            stability = detector.analyze_region_stability(result['all_detections'])
            
            logger.info("稳定性分析结果:")
            for region, stats in stability.items():
                logger.info(f"  {region}:")
                logger.info(f"    检测率: {stats['detection_rate']:.2%}")
                logger.info(f"    位置方差: {stats['position_variance']:.2f}")
                logger.info(f"    最大移动: {stats['max_movement']:.2f}")
    else:
        logger.error("不支持的文件格式")

if __name__ == "__main__":
    main()