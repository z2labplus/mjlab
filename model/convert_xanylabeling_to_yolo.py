#!/usr/bin/env python3
"""
将X-AnyLabeling的JSON标注转换为YOLOv8格式
支持多边形标注转换为边界框
"""

import json
import os
import shutil
from pathlib import Path
import numpy as np
import cv2
from typing import List, Tuple, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class XAnyLabelingToYOLO:
    """X-AnyLabeling到YOLO格式转换器"""
    
    def __init__(self, source_dir: str, output_dir: str):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        
        # 定义类别映射
        self.class_names = ['up', 'down', 'left', 'right', 'wind']
        self.class_to_id = {name: i for i, name in enumerate(self.class_names)}
        
        logger.info(f"类别映射: {self.class_to_id}")
        
        # 创建输出目录结构
        self.setup_directories()
        
    def setup_directories(self):
        """创建输出目录结构"""
        dirs = [
            'images/train',
            'images/val', 
            'labels/train',
            'labels/val'
        ]
        
        for dir_name in dirs:
            (self.output_dir / dir_name).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"创建输出目录: {self.output_dir}")
    
    def polygon_to_bbox(self, points: List[List[float]]) -> Tuple[float, float, float, float]:
        """
        将多边形坐标转换为边界框
        
        Args:
            points: 多边形顶点坐标 [[x1,y1], [x2,y2], ...]
            
        Returns:
            (x_min, y_min, x_max, y_max)
        """
        if not points:
            return 0, 0, 0, 0
        
        x_coords = [point[0] for point in points]
        y_coords = [point[1] for point in points]
        
        x_min = min(x_coords)
        x_max = max(x_coords)
        y_min = min(y_coords)
        y_max = max(y_coords)
        
        return x_min, y_min, x_max, y_max
    
    def bbox_to_yolo_format(self, bbox: Tuple[float, float, float, float], 
                           img_width: int, img_height: int) -> Tuple[float, float, float, float]:
        """
        将边界框转换为YOLO格式
        
        Args:
            bbox: (x_min, y_min, x_max, y_max)
            img_width: 图像宽度
            img_height: 图像高度
            
        Returns:
            (x_center, y_center, width, height) - 相对坐标
        """
        x_min, y_min, x_max, y_max = bbox
        
        # 计算中心点和宽高
        x_center = (x_min + x_max) / 2
        y_center = (y_min + y_max) / 2
        width = x_max - x_min
        height = y_max - y_min
        
        # 转换为相对坐标
        x_center_rel = x_center / img_width
        y_center_rel = y_center / img_height
        width_rel = width / img_width
        height_rel = height / img_height
        
        return x_center_rel, y_center_rel, width_rel, height_rel
    
    def convert_single_file(self, json_path: Path) -> bool:
        """
        转换单个JSON文件
        
        Args:
            json_path: JSON文件路径
            
        Returns:
            转换是否成功
        """
        try:
            # 读取JSON文件
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 获取图像信息
            img_width = data['imageWidth']
            img_height = data['imageHeight']
            img_name = data['imagePath']
            
            # 检查对应的图像文件是否存在
            img_path = json_path.parent / img_name
            if not img_path.exists():
                logger.warning(f"图像文件不存在: {img_path}")
                return False
            
            # 处理标注
            annotations = []
            for shape in data.get('shapes', []):
                label = shape['label']
                points = shape['points']
                
                # 检查类别是否在我们的映射中
                if label not in self.class_to_id:
                    logger.warning(f"未知类别: {label}, 跳过")
                    continue
                
                class_id = self.class_to_id[label]
                
                # 转换多边形为边界框
                bbox = self.polygon_to_bbox(points)
                
                # 转换为YOLO格式
                yolo_bbox = self.bbox_to_yolo_format(bbox, img_width, img_height)
                
                # 验证边界框有效性
                if all(0 <= coord <= 1 for coord in yolo_bbox) and yolo_bbox[2] > 0 and yolo_bbox[3] > 0:
                    annotations.append((class_id, *yolo_bbox))
                else:
                    logger.warning(f"无效的边界框: {yolo_bbox}, 跳过")
            
            if not annotations:
                logger.warning(f"文件 {json_path.name} 没有有效的标注")
                return False
            
            # 生成输出文件名
            base_name = json_path.stem
            txt_filename = f"{base_name}.txt"
            
            return {
                'img_path': img_path,
                'img_name': img_name,
                'txt_filename': txt_filename,
                'annotations': annotations
            }
            
        except Exception as e:
            logger.error(f"转换文件 {json_path} 失败: {e}")
            return False
    
    def convert_all_files(self, train_ratio: float = 0.8):
        """
        转换所有文件并分割训练/验证集
        
        Args:
            train_ratio: 训练集比例
        """
        # 获取所有JSON文件
        json_files = list(self.source_dir.glob('*.json'))
        logger.info(f"找到 {len(json_files)} 个JSON文件")
        
        if not json_files:
            logger.error("没有找到JSON文件!")
            return
        
        # 转换所有文件
        converted_data = []
        for json_path in json_files:
            result = self.convert_single_file(json_path)
            if result:
                converted_data.append(result)
        
        logger.info(f"成功转换 {len(converted_data)} 个文件")
        
        if not converted_data:
            logger.error("没有成功转换的文件!")
            return
        
        # 随机打乱并分割数据集
        import random
        random.shuffle(converted_data)
        
        split_idx = int(len(converted_data) * train_ratio)
        train_data = converted_data[:split_idx]
        val_data = converted_data[split_idx:]
        
        logger.info(f"数据集分割: 训练集 {len(train_data)} 个, 验证集 {len(val_data)} 个")
        
        # 保存训练集
        self._save_dataset(train_data, 'train')
        
        # 保存验证集
        self._save_dataset(val_data, 'val')
        
        # 创建数据集配置文件
        self.create_dataset_yaml()
        
        logger.info("数据转换完成!")
    
    def _save_dataset(self, data_list: List[Dict], split: str):
        """保存数据集"""
        for data in data_list:
            # 复制图像文件
            src_img = data['img_path']
            dst_img = self.output_dir / 'images' / split / data['img_name']
            shutil.copy2(src_img, dst_img)
            
            # 创建标签文件
            txt_path = self.output_dir / 'labels' / split / data['txt_filename']
            with open(txt_path, 'w') as f:
                for annotation in data['annotations']:
                    class_id, x_center, y_center, width, height = annotation
                    f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
    
    def create_dataset_yaml(self):
        """创建数据集配置文件"""
        yaml_content = f"""# 麻将区域检测数据集配置
path: {self.output_dir.absolute()}
train: images/train
val: images/val

# 类别数量
nc: {len(self.class_names)}

# 类别名称
names: {self.class_names}
"""
        
        yaml_path = self.output_dir / 'dataset.yaml'
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        
        logger.info(f"数据集配置文件已保存: {yaml_path}")
    
    def validate_conversion(self):
        """验证转换结果"""
        train_imgs = len(list((self.output_dir / 'images' / 'train').glob('*.jpg')))
        train_labels = len(list((self.output_dir / 'labels' / 'train').glob('*.txt')))
        val_imgs = len(list((self.output_dir / 'images' / 'val').glob('*.jpg')))
        val_labels = len(list((self.output_dir / 'labels' / 'val').glob('*.txt')))
        
        logger.info("=== 转换结果验证 ===")
        logger.info(f"训练集: {train_imgs} 张图片, {train_labels} 个标签文件")
        logger.info(f"验证集: {val_imgs} 张图片, {val_labels} 个标签文件")
        
        # 检查标签文件内容
        if train_labels > 0:
            sample_label = list((self.output_dir / 'labels' / 'train').glob('*.txt'))[0]
            logger.info(f"标签文件样例 ({sample_label.name}):")
            with open(sample_label, 'r') as f:
                lines = f.readlines()[:3]  # 显示前3行
                for line in lines:
                    logger.info(f"  {line.strip()}")
        
        return train_imgs == train_labels and val_imgs == val_labels

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='X-AnyLabeling到YOLO格式转换')
    parser.add_argument('--source', default='./all_labeled_images',
                       help='X-AnyLabeling标注数据目录')
    parser.add_argument('--output', default='./yolo_dataset',
                       help='YOLO格式输出目录')
    parser.add_argument('--train_ratio', type=float, default=0.8,
                       help='训练集比例')
    
    args = parser.parse_args()
    
    logger.info("🔄 开始转换X-AnyLabeling数据到YOLO格式")
    logger.info(f"源目录: {args.source}")
    logger.info(f"输出目录: {args.output}")
    
    # 创建转换器
    converter = XAnyLabelingToYOLO(args.source, args.output)
    
    # 执行转换
    converter.convert_all_files(args.train_ratio)
    
    # 验证结果
    if converter.validate_conversion():
        logger.info("✅ 数据转换成功!")
    else:
        logger.error("❌ 数据转换可能存在问题，请检查")

if __name__ == "__main__":
    main()