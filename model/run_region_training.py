#!/usr/bin/env python3
"""
麻将区域检测训练快速启动脚本
一键完成从数据转换到模型训练的全流程
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class RegionTrainingPipeline:
    """区域检测训练流水线"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.source_dir = self.base_dir / "all_labeled_images"
        self.dataset_dir = self.base_dir / "yolo_dataset"
        
    def check_dependencies(self):
        """检查依赖"""
        logger.info("🔍 检查依赖...")
        
        required_packages = ['ultralytics', 'opencv-python', 'torch', 'torchvision']
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                logger.info(f"✅ {package}")
            except ImportError:
                missing_packages.append(package)
                logger.error(f"❌ {package}")
        
        if missing_packages:
            logger.error(f"缺少依赖包: {', '.join(missing_packages)}")
            logger.info("请运行: pip install ultralytics opencv-python torch torchvision")
            return False
        
        return True
    
    def check_data(self):
        """检查数据"""
        logger.info("📊 检查训练数据...")
        
        if not self.source_dir.exists():
            logger.error(f"源数据目录不存在: {self.source_dir}")
            return False
        
        # 统计文件
        json_files = list(self.source_dir.glob("*.json"))
        jpg_files = list(self.source_dir.glob("*.jpg"))
        
        logger.info(f"找到 {len(json_files)} 个JSON标注文件")
        logger.info(f"找到 {len(jpg_files)} 个JPG图片文件")
        
        if len(json_files) == 0:
            logger.error("没有找到JSON标注文件!")
            return False
        
        if len(jpg_files) == 0:
            logger.error("没有找到图片文件!")
            return False
        
        if len(json_files) != len(jpg_files):
            logger.warning(f"标注文件和图片文件数量不匹配: {len(json_files)} vs {len(jpg_files)}")
        
        return True
    
    def convert_data(self):
        """转换数据格式"""
        logger.info("🔄 转换数据格式...")
        
        cmd = [
            sys.executable, "convert_xanylabeling_to_yolo.py",
            "--source", str(self.source_dir),
            "--output", str(self.dataset_dir),
            "--train_ratio", "0.8"
        ]
        
        try:
            result = subprocess.run(cmd, cwd=self.base_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ 数据转换成功")
                logger.info(result.stdout)
                return True
            else:
                logger.error("❌ 数据转换失败")
                logger.error(result.stderr)
                return False
                
        except Exception as e:
            logger.error(f"❌ 数据转换失败: {e}")
            return False
    
    def train_model(self, model_size='n', epochs=100, batch=16):
        """训练模型"""
        logger.info(f"🚀 开始训练模型 (大小: {model_size}, 轮数: {epochs})...")
        
        cmd = [
            sys.executable, "train_region_detector.py",
            "--dataset", str(self.dataset_dir),
            "--model_size", model_size,
            "--epochs", str(epochs),
            "--batch", str(batch),
            "--device", "cpu"  # 明确指定使用CPU，避免auto的问题
        ]
        
        try:
            # 实时显示输出
            process = subprocess.Popen(cmd, cwd=self.base_dir, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.STDOUT,
                                     text=True, bufsize=1, universal_newlines=True)
            
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
            
            return_code = process.poll()
            
            if return_code == 0:
                logger.info("✅ 模型训练成功")
                return True
            else:
                logger.error("❌ 模型训练失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 模型训练失败: {e}")
            return False
    
    def find_best_model(self):
        """查找最佳模型"""
        runs_dir = self.base_dir / "runs" / "train"
        
        if not runs_dir.exists():
            return None
        
        # 查找最新的训练结果
        train_dirs = [d for d in runs_dir.iterdir() if d.is_dir() and d.name.startswith('mahjong_regions')]
        
        if not train_dirs:
            return None
        
        # 按修改时间排序，获取最新的
        latest_dir = sorted(train_dirs, key=lambda x: x.stat().st_mtime, reverse=True)[0]
        best_model = latest_dir / "weights" / "best.pt"
        
        return best_model if best_model.exists() else None
    
    def test_model(self, test_source=None):
        """测试模型"""
        logger.info("🧪 测试训练好的模型...")
        
        # 查找模型
        best_model = self.find_best_model()
        if not best_model:
            logger.error("没有找到训练好的模型")
            return False
        
        logger.info(f"使用模型: {best_model}")
        
        # 如果没有指定测试源，使用验证集的第一张图片
        if not test_source:
            val_images = list((self.dataset_dir / "images" / "val").glob("*.jpg"))
            if val_images:
                test_source = str(val_images[0])
            else:
                logger.error("没有找到测试图片")
                return False
        
        cmd = [
            sys.executable, "test_region_detector.py",
            "--model", str(best_model),
            "--source", test_source,
            "--conf", "0.5"
        ]
        
        try:
            result = subprocess.run(cmd, cwd=self.base_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ 模型测试成功")
                logger.info(result.stdout)
                return True
            else:
                logger.error("❌ 模型测试失败")
                logger.error(result.stderr)
                return False
                
        except Exception as e:
            logger.error(f"❌ 模型测试失败: {e}")
            return False
    
    def run_full_pipeline(self, model_size='n', epochs=100, batch=16, test_source=None):
        """运行完整流水线"""
        logger.info("🎯 开始麻将区域检测训练流水线")
        logger.info("=" * 60)
        
        steps = [
            ("检查依赖", self.check_dependencies),
            ("检查数据", self.check_data),
            ("转换数据", self.convert_data),
            ("训练模型", lambda: self.train_model(model_size, epochs, batch)),
            ("测试模型", lambda: self.test_model(test_source))
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n📋 步骤: {step_name}")
            logger.info("-" * 30)
            
            success = step_func()
            
            if not success:
                logger.error(f"❌ 步骤 '{step_name}' 失败，流水线停止")
                return False
            
            logger.info(f"✅ 步骤 '{step_name}' 完成")
        
        logger.info("\n🎉 训练流水线完成!")
        
        # 显示结果信息
        best_model = self.find_best_model()
        if best_model:
            logger.info(f"📂 最佳模型路径: {best_model}")
            logger.info(f"📊 训练结果目录: {best_model.parent.parent}")
        
        return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='麻将区域检测训练流水线')
    parser.add_argument('--model_size', default='n', choices=['n', 's', 'm', 'l', 'x'],
                       help='模型大小 (n=最快, x=最准确)')
    parser.add_argument('--epochs', type=int, default=100,
                       help='训练轮数')
    parser.add_argument('--batch', type=int, default=16,
                       help='批大小')
    parser.add_argument('--test_source', 
                       help='测试图片/视频路径')
    parser.add_argument('--step', choices=['convert', 'train', 'test', 'full'],
                       default='full', help='执行特定步骤')
    
    args = parser.parse_args()
    
    # 创建流水线
    pipeline = RegionTrainingPipeline()
    
    if args.step == 'convert':
        pipeline.convert_data()
    elif args.step == 'train':
        pipeline.train_model(args.model_size, args.epochs, args.batch)
    elif args.step == 'test':
        pipeline.test_model(args.test_source)
    else:  # full
        pipeline.run_full_pipeline(args.model_size, args.epochs, args.batch, args.test_source)

if __name__ == "__main__":
    main()