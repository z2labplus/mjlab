#!/usr/bin/env python3
"""
麻将牌检测完整训练流水线
一键运行从合成数据生成到模型训练的完整过程
"""

import os
import sys
import logging
import argparse
from pathlib import Path
import subprocess

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MahjongTileTrainingPipeline:
    """麻将牌训练完整流水线"""
    
    def __init__(self):
        self.model_dir = Path(__file__).parent
        self.svg_dir = self.model_dir.parent / "frontend" / "public" / "assets" / "mahjong"
        self.background_dir = self.model_dir / "all_labeled_images"
        self.synthetic_dir = self.model_dir / "synthetic_dataset"
        self.real_data_dir = self.model_dir / "real_tile_dataset"
        self.combined_dir = self.model_dir / "combined_tile_dataset"
        
    def check_dependencies(self):
        """检查依赖包"""
        logger.info("🔍 检查依赖包...")
        
        required_packages = ['cairosvg', 'pillow', 'opencv-python', 'ultralytics', 'PyYAML']
        missing_packages = []
        
        for package in required_packages:
            try:
                if package == 'pillow':
                    import PIL
                elif package == 'opencv-python':
                    import cv2
                elif package == 'PyYAML':
                    import yaml
                else:
                    __import__(package)
                logger.info(f"  ✅ {package}")
            except ImportError:
                missing_packages.append(package)
                logger.warning(f"  ❌ {package}")
        
        if missing_packages:
            logger.error("❌ 缺少依赖包，请安装:")
            logger.error(f"   pip install {' '.join(missing_packages)}")
            return False
        
        logger.info("✅ 所有依赖包已安装")
        return True
    
    def check_data_directories(self):
        """检查数据目录"""
        logger.info("📁 检查数据目录...")
        
        # 检查SVG目录
        if not self.svg_dir.exists():
            logger.error(f"❌ SVG目录不存在: {self.svg_dir}")
            return False
        
        svg_files = list(self.svg_dir.glob("*.svg"))
        if not svg_files:
            logger.error(f"❌ SVG目录中没有SVG文件: {self.svg_dir}")
            return False
        
        logger.info(f"  ✅ SVG文件: {len(svg_files)} 个")
        
        # 检查背景图像目录
        if not self.background_dir.exists():
            logger.error(f"❌ 背景图像目录不存在: {self.background_dir}")
            logger.error("   请确保 all_labeled_images 目录存在并包含游戏截图和JSON标注")
            return False
        
        bg_images = list(self.background_dir.glob("*.jpg"))
        json_files = list(self.background_dir.glob("*.json"))
        
        if not bg_images:
            logger.error(f"❌ 背景图像目录中没有JPG文件: {self.background_dir}")
            return False
        
        logger.info(f"  ✅ 背景图像: {len(bg_images)} 个")
        logger.info(f"  ✅ JSON标注: {len(json_files)} 个")
        
        return True
    
    def generate_synthetic_data(self, num_per_bg=3):
        """生成合成数据"""
        logger.info("🎨 开始生成合成数据...")
        
        try:
            from mahjong_tile_generator import MahjongTileGenerator
            from synthetic_data_generator import SyntheticDataGenerator
            
            # 创建牌生成器
            tiles_generator = MahjongTileGenerator(str(self.svg_dir), "./temp_tiles")
            
            # 创建合成数据生成器
            synthetic_generator = SyntheticDataGenerator(
                str(self.background_dir),
                tiles_generator,
                str(self.synthetic_dir)
            )
            
            # 生成数据集
            synthetics = synthetic_generator.generate_dataset(num_per_bg)
            
            logger.info(f"✅ 合成数据生成完成: {len(synthetics)} 张图像")
            return True
            
        except Exception as e:
            logger.error(f"❌ 合成数据生成失败: {e}")
            return False
    
    def prepare_real_data(self):
        """准备真实数据（如果有的话）"""
        logger.info("📋 准备真实标注数据...")
        
        # 这里可以添加真实数据的处理逻辑
        # 目前假设没有真实的麻将牌标注数据
        self.real_data_dir.mkdir(exist_ok=True)
        (self.real_data_dir / "images").mkdir(exist_ok=True)
        (self.real_data_dir / "labels").mkdir(exist_ok=True)
        
        logger.info("✅ 真实数据目录已准备（当前为空）")
        return True
    
    def train_model(self, model_size='n', epochs=80, batch_size=8):
        """训练模型"""
        logger.info("🚀 开始训练麻将牌检测模型...")
        
        try:
            from train_mahjong_tiles import MahjongTileTrainingPipeline
            
            # 创建训练流水线
            pipeline = MahjongTileTrainingPipeline(
                str(self.real_data_dir),
                str(self.synthetic_dir),
                str(self.combined_dir)
            )
            
            # 合并数据集
            train_count, val_count = pipeline.merge_datasets(synthetic_ratio=0.8)
            
            if train_count == 0:
                logger.error("❌ 没有可用的训练数据")
                return False
            
            # 训练模型
            best_model = pipeline.train_model(model_size, epochs, batch_size)
            
            if best_model:
                logger.info(f"✅ 模型训练完成: {best_model}")
                return True
            else:
                logger.error("❌ 模型训练失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 训练过程失败: {e}")
            return False
    
    def run_complete_pipeline(self, num_per_bg=3, model_size='n', epochs=80, batch_size=6):
        """运行完整的训练流水线"""
        logger.info("🎯 开始麻将牌检测完整训练流水线")
        logger.info("=" * 60)
        
        # 1. 检查依赖
        if not self.check_dependencies():
            return False
        
        # 2. 检查数据
        if not self.check_data_directories():
            return False
        
        # 3. 生成合成数据
        if not self.generate_synthetic_data(num_per_bg):
            return False
        
        # 4. 准备真实数据
        if not self.prepare_real_data():
            return False
        
        # 5. 训练模型
        if not self.train_model(model_size, epochs, batch_size):
            return False
        
        logger.info("🎉 完整训练流水线执行成功！")
        logger.info("📂 检查以下目录:")
        logger.info(f"   合成数据: {self.synthetic_dir}")
        logger.info(f"   组合数据: {self.combined_dir}")
        logger.info(f"   训练结果: runs/train/")
        
        return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='麻将牌检测完整训练流水线')
    parser.add_argument('--num_per_bg', type=int, default=3,
                       help='每张背景图生成的合成图像数量')
    parser.add_argument('--model_size', default='n', choices=['n', 's', 'm'],
                       help='模型大小 (n=最小最快, s=中等, m=较大)')
    parser.add_argument('--epochs', type=int, default=80,
                       help='训练轮数（CPU推荐50-80）')
    parser.add_argument('--batch', type=int, default=6,
                       help='批大小（CPU推荐4-6）')
    parser.add_argument('--synthetic_only', action='store_true',
                       help='仅生成合成数据，不训练')
    parser.add_argument('--train_only', action='store_true',
                       help='仅训练（假设合成数据已存在）')
    
    args = parser.parse_args()
    
    # 创建流水线
    pipeline = MahjongTileTrainingPipeline()
    
    if args.synthetic_only:
        # 仅生成合成数据
        logger.info("🎨 仅生成合成数据模式")
        if pipeline.check_dependencies() and pipeline.check_data_directories():
            pipeline.generate_synthetic_data(args.num_per_bg)
    elif args.train_only:
        # 仅训练
        logger.info("🚀 仅训练模式")
        pipeline.prepare_real_data()
        pipeline.train_model(args.model_size, args.epochs, args.batch)
    else:
        # 完整流水线
        pipeline.run_complete_pipeline(
            args.num_per_bg,
            args.model_size, 
            args.epochs,
            args.batch
        )

if __name__ == "__main__":
    main()