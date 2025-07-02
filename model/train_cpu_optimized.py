#!/usr/bin/env python3
"""
CPU优化的麻将区域检测训练脚本
专为CPU环境优化，减少内存使用和提高训练效率
"""

import sys
import argparse
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='CPU优化的YOLOv8训练')
    parser.add_argument('--dataset', default='./yolo_dataset', help='数据集路径')
    parser.add_argument('--model_size', default='n', choices=['n', 's'], help='模型大小(推荐n或s)')
    parser.add_argument('--epochs', type=int, default=50, help='训练轮数(CPU建议50-100)')
    parser.add_argument('--batch', type=int, default=8, help='批大小(CPU建议4-8)')
    
    args = parser.parse_args()
    
    logger.info("🚀 CPU优化训练模式")
    logger.info("=" * 50)
    
    # 检查数据集
    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        logger.error(f"数据集不存在: {dataset_path}")
        return
    
    try:
        from ultralytics import YOLO
        import torch
        
        # 确认使用CPU
        logger.info("💻 强制使用CPU训练")
        torch.set_num_threads(4)  # 限制CPU线程数
        
        # 加载模型
        model_name = f"yolov8{args.model_size}.pt"
        logger.info(f"📦 加载模型: {model_name}")
        model = YOLO(model_name)
        
        # CPU优化的训练参数
        train_args = {
            'data': str(dataset_path / 'dataset.yaml'),
            'epochs': args.epochs,
            'imgsz': 480,  # 降低图像尺寸加速训练
            'batch': args.batch,
            'workers': 2,  # 减少workers
            'device': 'cpu',
            'patience': 15,
            'save_period': 20,
            'val': True,
            'plots': True,
            'verbose': True,
            'name': f'mahjong_regions_cpu_{args.model_size}',
            'project': 'runs/train',
            'optimizer': 'AdamW',  # 使用AdamW优化器
            'lr0': 0.001,  # 较小的学习率
            'warmup_epochs': 3,
            'mosaic': 0.0,  # 关闭mosaic增强减少内存使用
            'mixup': 0.0,   # 关闭mixup
            'copy_paste': 0.0,  # 关闭copy_paste
        }
        
        logger.info("⚙️ CPU优化配置:")
        logger.info(f"   图像尺寸: {train_args['imgsz']} (降低以提高速度)")
        logger.info(f"   批大小: {train_args['batch']}")
        logger.info(f"   Workers: {train_args['workers']}")
        logger.info(f"   数据增强: 简化 (提高训练速度)")
        
        logger.info("🚀 开始CPU训练...")
        logger.info("⏰ 预计时间: 30-60分钟 (取决于数据量)")
        
        # 开始训练
        results = model.train(**train_args)
        
        print("--------------")
        print(results)
        print(dir(results))
        
        logger.info("✅ 训练完成!")
        save_dir = Path(train_args['project']) / train_args['name']
        logger.info(f"📂 结果保存在: {save_dir}")
        
        # 快速验证
        best_model = save_dir / 'weights' / 'best.pt'
        if best_model.exists():
            logger.info(f"🎯 最佳模型: {best_model}")
            
            # 加载最佳模型进行验证
            best_model_obj = YOLO(str(best_model))
            val_results = best_model_obj.val(data=str(dataset_path / 'dataset.yaml'))
            
            logger.info("📊 验证结果:")
            logger.info(f"   mAP50: {val_results.box.map50:.4f}")
            logger.info(f"   mAP50-95: {val_results.box.map:.4f}")
        
        logger.info("🎉 CPU训练流程完成!")
        
    except ImportError:
        logger.error("❌ 请安装ultralytics: pip install ultralytics")
    except Exception as e:
        logger.error(f"❌ 训练失败: {e}")
        logger.error("💡 建议:")
        logger.error("   1. 减少batch size: --batch 4")
        logger.error("   2. 减少epochs: --epochs 30")
        logger.error("   3. 使用最小模型: --model_size n")

if __name__ == "__main__":
    main()