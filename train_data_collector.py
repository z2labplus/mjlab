#!/usr/bin/env python3
"""
麻将牌训练数据收集器
从游戏录像中提取麻将牌图片用于YOLOv8训练
"""

import cv2
import numpy as np
import os
import json
from pathlib import Path
import argparse
import logging
from typing import List, Tuple, Dict
from dataclasses import dataclass
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TileAnnotation:
    """麻将牌标注数据"""
    x_center: float  # YOLO格式：中心点x坐标(相对)
    y_center: float  # YOLO格式：中心点y坐标(相对)
    width: float     # YOLO格式：宽度(相对)
    height: float    # YOLO格式：高度(相对)
    class_id: int    # 类别ID
    tile_name: str   # 牌名称

class MahjongTrainingDataCollector:
    """麻将训练数据收集器"""
    
    def __init__(self, output_dir: str = "training_data"):
        self.output_dir = Path(output_dir)
        self.setup_directories()
        
        # 麻将牌类别映射
        self.tile_classes = self._create_tile_classes()
        self.class_to_id = {name: i for i, name in enumerate(self.tile_classes)}
        
        # 手动标注参数
        self.current_frame = None
        self.current_annotations = []
        self.current_class_id = 0
        self.frame_count = 0
        
    def setup_directories(self):
        """创建训练数据目录结构"""
        dirs = ['images/train', 'images/val', 'labels/train', 'labels/val']
        for dir_name in dirs:
            (self.output_dir / dir_name).mkdir(parents=True, exist_ok=True)
        logger.info(f"创建训练数据目录: {self.output_dir}")
    
    def _create_tile_classes(self) -> List[str]:
        """创建麻将牌类别列表"""
        classes = []
        
        # 万字牌
        for i in range(1, 10):
            classes.append(f"{i}万")
        
        # 条子牌
        for i in range(1, 10):
            classes.append(f"{i}条")
            
        # 筒子牌
        for i in range(1, 10):
            classes.append(f"{i}筒")
        
        return classes
    
    def extract_frames_from_video(self, video_path: str, 
                                frame_interval: int = 30,
                                max_frames: int = 500) -> List[str]:
        """从视频中提取关键帧"""
        logger.info(f"从视频提取帧: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")
        
        frame_paths = []
        frame_id = 0
        extracted_count = 0
        
        while extracted_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_id % frame_interval == 0:
                # 保存帧
                frame_filename = f"frame_{int(time.time())}_{frame_id:06d}.jpg"
                frame_path = self.output_dir / "images" / "train" / frame_filename
                
                cv2.imwrite(str(frame_path), frame)
                frame_paths.append(str(frame_path))
                extracted_count += 1
                
                if extracted_count % 50 == 0:
                    logger.info(f"已提取 {extracted_count} 帧")
            
            frame_id += 1
        
        cap.release()
        logger.info(f"提取完成，共 {len(frame_paths)} 帧")
        return frame_paths
    
    def manual_annotation_tool(self, image_path: str):
        """手动标注工具"""
        self.current_frame = cv2.imread(image_path)
        if self.current_frame is None:
            logger.error(f"无法加载图像: {image_path}")
            return
        
        self.current_annotations = []
        clone = self.current_frame.copy()
        
        cv2.namedWindow('Annotation Tool', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Annotation Tool', 1200, 800)
        cv2.setMouseCallback('Annotation Tool', self._mouse_callback)
        
        logger.info("=== 麻将牌标注工具 ===")
        logger.info("操作指南:")
        logger.info("1. 鼠标左键拖拽框选麻将牌")
        logger.info("2. 数字键1-9选择万字牌，Q-I选择条子牌，A-K选择筒子牌")
        logger.info("3. 空格键：下一张图片")
        logger.info("4. S键：保存当前标注")
        logger.info("5. C键：清除当前标注")
        logger.info("6. ESC键：退出")
        logger.info("=== 当前类别信息 ===")
        for i, tile_name in enumerate(self.tile_classes):
            logger.info(f"类别{i}: {tile_name}")
        
        self.drawing = False
        self.start_point = None
        
        while True:
            display_frame = clone.copy()
            
            # 显示已标注的框
            for ann in self.current_annotations:
                h, w = self.current_frame.shape[:2]
                x_center = int(ann.x_center * w)
                y_center = int(ann.y_center * h)
                width = int(ann.width * w)
                height = int(ann.height * h)
                
                x1 = x_center - width // 2
                y1 = y_center - height // 2
                x2 = x_center + width // 2
                y2 = y_center + height // 2
                
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(display_frame, ann.tile_name, (x1, y1-10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # 显示当前选择的类别
            current_tile = self.tile_classes[self.current_class_id]
            cv2.putText(display_frame, f"Current: {current_tile}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.putText(display_frame, f"Annotations: {len(self.current_annotations)}", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            
            cv2.imshow('Annotation Tool', display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == 27:  # ESC
                break
            elif key == ord(' '):  # 空格：下一张
                return True
            elif key == ord('s'):  # 保存标注
                self._save_annotations(image_path)
                logger.info(f"已保存 {len(self.current_annotations)} 个标注")
            elif key == ord('c'):  # 清除标注
                self.current_annotations = []
                logger.info("已清除所有标注")
            else:
                # 处理类别选择
                self._handle_class_selection(key)
        
        cv2.destroyAllWindows()
        return False
    
    def _mouse_callback(self, event, x, y, flags, param):
        """鼠标回调函数"""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.start_point = (x, y)
        
        elif event == cv2.EVENT_LBUTTONUP:
            if self.drawing and self.start_point:
                self.drawing = False
                end_point = (x, y)
                self._add_annotation(self.start_point, end_point)
    
    def _add_annotation(self, start_point: Tuple[int, int], end_point: Tuple[int, int]):
        """添加标注"""
        x1, y1 = start_point
        x2, y2 = end_point
        
        # 确保坐标正确
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)
        
        # 转换为YOLO格式
        h, w = self.current_frame.shape[:2]
        x_center = (x1 + x2) / 2 / w
        y_center = (y1 + y2) / 2 / h
        width = (x2 - x1) / w
        height = (y2 - y1) / h
        
        annotation = TileAnnotation(
            x_center=x_center,
            y_center=y_center,
            width=width,
            height=height,
            class_id=self.current_class_id,
            tile_name=self.tile_classes[self.current_class_id]
        )
        
        self.current_annotations.append(annotation)
        logger.info(f"添加标注: {annotation.tile_name}")
    
    def _handle_class_selection(self, key):
        """处理类别选择"""
        # 万字牌 1-9
        if ord('1') <= key <= ord('9'):
            self.current_class_id = key - ord('1')
        # 条子牌 Q-I (1-9条)
        elif key in [ord('q'), ord('w'), ord('e'), ord('r'), ord('t'), 
                     ord('y'), ord('u'), ord('i'), ord('o')]:
            mapping = {'q': 0, 'w': 1, 'e': 2, 'r': 3, 't': 4, 
                      'y': 5, 'u': 6, 'i': 7, 'o': 8}
            self.current_class_id = 9 + mapping[chr(key)]
        # 筒子牌 A-K (1-9筒)
        elif key in [ord('a'), ord('s'), ord('d'), ord('f'), ord('g'), 
                     ord('h'), ord('j'), ord('k'), ord('l')]:
            mapping = {'a': 0, 's': 1, 'd': 2, 'f': 3, 'g': 4, 
                      'h': 5, 'j': 6, 'k': 7, 'l': 8}
            self.current_class_id = 18 + mapping[chr(key)]
        
        current_tile = self.tile_classes[self.current_class_id]
        logger.info(f"切换到类别: {current_tile}")
    
    def _save_annotations(self, image_path: str):
        """保存标注到YOLO格式文件"""
        # 生成标签文件路径
        image_path = Path(image_path)
        label_path = self.output_dir / "labels" / image_path.parent.name / (image_path.stem + ".txt")
        
        # 写入YOLO格式标注
        with open(label_path, 'w') as f:
            for ann in self.current_annotations:
                f.write(f"{ann.class_id} {ann.x_center:.6f} {ann.y_center:.6f} "
                       f"{ann.width:.6f} {ann.height:.6f}\n")
    
    def create_dataset_yaml(self):
        """创建数据集配置文件"""
        yaml_content = f"""# YOLOv8麻将牌数据集配置
path: {self.output_dir.absolute()}
train: images/train
val: images/val

# 类别数量
nc: {len(self.tile_classes)}

# 类别名称
names: {self.tile_classes}
"""
        
        yaml_path = self.output_dir / "dataset.yaml"
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        
        logger.info(f"数据集配置文件已保存: {yaml_path}")
    
    def split_dataset(self, train_ratio: float = 0.8):
        """分割训练集和验证集"""
        import shutil
        import random
        
        train_images = list((self.output_dir / "images" / "train").glob("*.jpg"))
        random.shuffle(train_images)
        
        split_index = int(len(train_images) * train_ratio)
        val_images = train_images[split_index:]
        
        logger.info(f"移动 {len(val_images)} 张图片到验证集")
        
        for img_path in val_images:
            # 移动图片
            val_img_path = self.output_dir / "images" / "val" / img_path.name
            shutil.move(str(img_path), str(val_img_path))
            
            # 移动对应的标签文件
            label_path = self.output_dir / "labels" / "train" / (img_path.stem + ".txt")
            if label_path.exists():
                val_label_path = self.output_dir / "labels" / "val" / (img_path.stem + ".txt")
                shutil.move(str(label_path), str(val_label_path))

def main():
    parser = argparse.ArgumentParser(description='麻将牌训练数据收集')
    parser.add_argument('--mode', choices=['extract', 'annotate'], required=True, 
                       help='操作模式：extract(提取帧) 或 annotate(标注)')
    parser.add_argument('--video', help='输入视频路径（extract模式）')
    parser.add_argument('--images', help='图片目录路径（annotate模式）')
    parser.add_argument('--output', default='training_data', help='输出目录')
    parser.add_argument('--interval', type=int, default=30, help='帧提取间隔')
    parser.add_argument('--max_frames', type=int, default=500, help='最大提取帧数')
    
    args = parser.parse_args()
    
    collector = MahjongTrainingDataCollector(args.output)
    
    if args.mode == 'extract':
        if not args.video:
            logger.error("extract模式需要指定视频路径")
            return
        
        frame_paths = collector.extract_frames_from_video(
            args.video, args.interval, args.max_frames
        )
        logger.info(f"提取完成，共 {len(frame_paths)} 帧")
        
    elif args.mode == 'annotate':
        if args.images:
            image_dir = Path(args.images)
        else:
            image_dir = collector.output_dir / "images" / "train"
        
        image_files = list(image_dir.glob("*.jpg"))
        if not image_files:
            logger.error(f"在 {image_dir} 中没有找到图片文件")
            return
        
        logger.info(f"开始标注，共 {len(image_files)} 张图片")
        
        for i, img_path in enumerate(image_files):
            logger.info(f"标注进度: {i+1}/{len(image_files)} - {img_path.name}")
            
            should_continue = collector.manual_annotation_tool(str(img_path))
            if not should_continue:
                break
        
        # 分割数据集
        collector.split_dataset()
        
        # 创建配置文件
        collector.create_dataset_yaml()
        
        logger.info("标注完成！")

if __name__ == "__main__":
    main()