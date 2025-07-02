#!/usr/bin/env python3
"""
简化版麻将牌检测训练脚本
专为Windows CPU训练优化，不依赖区域检测
"""

import os
import sys
import shutil
import random
from pathlib import Path
import logging
import argparse
from typing import List, Dict
import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleTileTrainer:
    """简化版麻将牌训练器"""
    
    def __init__(self, synthetic_data_dir: str, output_dir: str):
        self.synthetic_data_dir = Path(synthetic_data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据集分割比例
        self.train_ratio = 0.8
        self.val_ratio = 0.2
        
        # 设置输出目录结构
        self.setup_output_directories()
    
    def setup_output_directories(self):
        """设置输出目录结构"""
        dirs = [
            'images/train', 'images/val',
            'labels/train', 'labels/val'
        ]
        
        for dir_name in dirs:
            (self.output_dir / dir_name).mkdir(parents=True, exist_ok=True)
    
    def prepare_training_data(self):
        """准备训练数据"""
        logger.info("📁 准备训练数据...")
        
        # 检查合成数据目录
        synthetic_images_dir = self.synthetic_data_dir / "images"
        synthetic_labels_dir = self.synthetic_data_dir / "labels"
        
        if not synthetic_images_dir.exists():
            logger.error(f"❌ 合成数据图像目录不存在: {synthetic_images_dir}")
            return False
        
        if not synthetic_labels_dir.exists():
            logger.error(f"❌ 合成数据标注目录不存在: {synthetic_labels_dir}")
            return False
        
        # 收集所有数据
        all_data = []
        for img_file in synthetic_images_dir.glob("*.jpg"):
            label_file = synthetic_labels_dir / f"{img_file.stem}.txt"
            
            if label_file.exists():
                all_data.append({
                    'image_path': img_file,
                    'label_path': label_file
                })
        
        if not all_data:
            logger.error("❌ 没有找到有效的训练数据")
            return False
        
        logger.info(f"📊 找到 {len(all_data)} 张训练图像")
        
        # 打乱数据
        random.shuffle(all_data)
        
        # 分割训练集和验证集
        split_idx = int(len(all_data) * self.train_ratio)
        train_data = all_data[:split_idx]
        val_data = all_data[split_idx:]
        
        logger.info(f"训练集: {len(train_data)} 张")
        logger.info(f"验证集: {len(val_data)} 张")
        
        # 复制文件
        self._copy_data_to_output(train_data, 'train')
        self._copy_data_to_output(val_data, 'val')
        
        # 创建数据集配置
        self._create_dataset_config()
        
        logger.info("✅ 训练数据准备完成")
        return True
    
    def _copy_data_to_output(self, data_list: List[Dict], split: str):
        """复制数据到输出目录"""
        for data in data_list:
            # 复制图像
            src_img = data['image_path']
            dst_img = self.output_dir / "images" / split / src_img.name
            shutil.copy2(src_img, dst_img)
            
            # 复制标签
            src_label = data['label_path']
            dst_label = self.output_dir / "labels" / split / src_label.name
            shutil.copy2(src_label, dst_label)
    
    def _create_dataset_config(self):
        """创建数据集配置文件"""
        # 从合成数据的配置中读取类别信息
        synthetic_config_path = self.synthetic_data_dir / "dataset.yaml"
        
        if synthetic_config_path.exists():
            with open(synthetic_config_path, 'r', encoding='utf-8') as f:
                synthetic_config = yaml.safe_load(f)
            
            tile_classes = synthetic_config.get('names', [])
        else:
            # 默认类别
            tile_classes = self._get_default_tile_classes()
        
        config = {
            'path': str(self.output_dir.absolute()),
            'train': 'images/train',
            'val': 'images/val',
            'nc': len(tile_classes),
            'names': tile_classes
        }
        
        config_path = self.output_dir / "dataset.yaml"
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        
        logger.info(f"📄 数据集配置已保存: {config_path}")
        logger.info(f"📊 类别数: {len(tile_classes)}")
    
    def _get_default_tile_classes(self) -> List[str]:
        """获取默认的麻将牌类别"""
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
        
        # 字牌
        zi_tiles = ['东', '南', '西', '北', '中', '发', '白', '梅']
        classes.extend(zi_tiles)
        
        return classes
    
    def train_model(self, model_size: str = 'n', epochs: int = 60, batch_size: int = 4):
        """训练麻将牌检测模型"""
        logger.info("🚀 开始训练麻将牌检测模型...")
        
        try:
            from ultralytics import YOLO
            import torch
            
            # Windows CPU优化设置
            logger.info("💻 使用CPU训练模式（Windows优化）")
            torch.set_num_threads(4)
            
            # Windows CPU特殊优化
            if hasattr(torch, 'set_num_interop_threads'):
                torch.set_num_interop_threads(2)
            
            # 加载模型
            model = YOLO(f'yolov8{model_size}.pt')
            
            # Windows CPU优化训练参数
            train_args = {
                'data': str(self.output_dir / 'dataset.yaml'),
                'epochs': epochs,
                'imgsz': 416,  # 进一步降低图像尺寸
                'batch': batch_size,
                'workers': 0,  # Windows建议使用0
                'device': 'cpu',
                'patience': 10,  # 提早停止
                'save_period': 20,
                'val': True,
                'plots': True,
                'verbose': True,
                'name': f'simple_mahjong_tiles_{model_size}',
                'project': 'runs/train',
                'optimizer': 'AdamW',
                'lr0': 0.001,
                'warmup_epochs': 3,
                'mosaic': 0.2,  # 进一步减少数据增强
                'mixup': 0.0,
                'copy_paste': 0.0,
                'cache': False,  # 不缓存到内存
                'rect': False,  # 关闭矩形训练
                'cos_lr': True,  # 使用余弦学习率
            }
            
            logger.info("⚙️ Windows CPU训练配置:")
            for key, value in train_args.items():
                logger.info(f"   {key}: {value}")
            
            logger.info("🕐 预计训练时间: 20-40分钟（取决于数据量和CPU性能）")
            
            # 开始训练
            results = model.train(**train_args)
            
            # 获取最佳模型路径
            runs_dir = Path('runs/train')
            latest_dir = max(runs_dir.glob(f'simple_mahjong_tiles_{model_size}*'), 
                           key=lambda x: x.stat().st_mtime, default=None)
            
            if latest_dir:
                best_model_path = latest_dir / 'weights' / 'best.pt'
                logger.info(f"✅ 训练完成！最佳模型: {best_model_path}")
                
                # 快速验证
                if best_model_path.exists():
                    self._validate_model(str(best_model_path))
                
                return str(best_model_path)
            else:
                logger.warning("⚠️ 无法找到训练结果目录")
                return None
                
        except ImportError:
            logger.error("❌ 请安装ultralytics: pip install ultralytics")
            return None
        except Exception as e:
            logger.error(f"❌ 训练失败: {e}")
            return None
    
    def _validate_model(self, model_path: str):
        """验证训练好的模型"""
        try:
            from ultralytics import YOLO
            
            model = YOLO(model_path)
            results = model.val(data=str(self.output_dir / 'dataset.yaml'))
            
            logger.info("📊 模型验证结果:")
            logger.info(f"   mAP50: {results.box.map50:.4f}")
            logger.info(f"   mAP50-95: {results.box.map:.4f}")
            
        except Exception as e:
            logger.warning(f"模型验证失败: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='简化版麻将牌检测训练')
    parser.add_argument('--synthetic_data', default='./simple_synthetic_dataset',
                       help='合成数据目录')
    parser.add_argument('--output', default='./training_dataset',
                       help='训练数据集输出目录')
    parser.add_argument('--model_size', default='n', choices=['n', 's'],
                       help='模型大小（CPU推荐n）')
    parser.add_argument('--epochs', type=int, default=60,
                       help='训练轮数（CPU推荐50-80）')
    parser.add_argument('--batch', type=int, default=4,
                       help='批大小（CPU推荐2-4）')
    parser.add_argument('--prepare_only', action='store_true',
                       help='仅准备数据，不训练')
    
    args = parser.parse_args()
    
    # 检查依赖
    try:
        import ultralytics
        import torch
        import yaml
        logger.info("✅ 依赖检查通过")
    except ImportError as e:
        logger.error(f"❌ 缺少依赖: {e}")
        logger.error("请安装: pip install ultralytics PyYAML")
        return
    
    # 创建训练器
    trainer = SimpleTileTrainer(args.synthetic_data, args.output)
    
    # 准备数据
    if not trainer.prepare_training_data():
        return
    
    if args.prepare_only:
        logger.info("✅ 数据准备完成，跳过训练")
        return
    
    # 训练模型
    best_model = trainer.train_model(args.model_size, args.epochs, args.batch)
    
    if best_model:
        logger.info("🎉 麻将牌检测模型训练完成！")
        logger.info(f"📂 最佳模型: {best_model}")
        logger.info("📋 使用模型:")
        logger.info("   from ultralytics import YOLO")
        logger.info(f"   model = YOLO('{best_model}')")
        logger.info("   results = model('game_screenshot.jpg')")
    else:
        logger.error("❌ 模型训练失败")

if __name__ == "__main__":
    main()