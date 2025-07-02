#!/usr/bin/env python3
"""
麻将牌识别模型训练
使用深度学习识别腾讯欢乐麻将中的麻将牌
"""

import tensorflow as tf
from tensorflow import keras
import numpy as np
import cv2
import os
import json
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt

class MahjongTileRecognitionModel:
    """麻将牌识别模型"""
    
    def __init__(self, img_size=(64, 64)):
        self.img_size = img_size
        self.model = None
        self.label_encoder = LabelEncoder()
        
        # 麻将牌类别 (万子1-9, 条子1-9, 筒子1-9)
        self.tile_classes = []
        for suit in ['wan', 'tiao', 'tong']:
            for value in range(1, 10):
                self.tile_classes.append(f"{suit}_{value}")
        
        self.label_encoder.fit(self.tile_classes)
    
    def create_model(self):
        """创建CNN模型"""
        model = keras.Sequential([
            # 第一层卷积
            keras.layers.Conv2D(32, (3, 3), activation='relu', 
                              input_shape=(*self.img_size, 3)),
            keras.layers.MaxPooling2D((2, 2)),
            keras.layers.Dropout(0.25),
            
            # 第二层卷积
            keras.layers.Conv2D(64, (3, 3), activation='relu'),
            keras.layers.MaxPooling2D((2, 2)),
            keras.layers.Dropout(0.25),
            
            # 第三层卷积
            keras.layers.Conv2D(128, (3, 3), activation='relu'),
            keras.layers.MaxPooling2D((2, 2)),
            keras.layers.Dropout(0.25),
            
            # 全连接层
            keras.layers.Flatten(),
            keras.layers.Dense(512, activation='relu'),
            keras.layers.Dropout(0.5),
            keras.layers.Dense(len(self.tile_classes), activation='softmax')
        ])
        
        model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        self.model = model
        return model
    
    def preprocess_image(self, image_path):
        """预处理图像"""
        img = cv2.imread(str(image_path))
        if img is None:
            return None
        
        # 调整大小
        img = cv2.resize(img, self.img_size)
        
        # 归一化
        img = img.astype(np.float32) / 255.0
        
        return img
    
    def load_training_data(self, data_dir):
        """加载训练数据"""
        data_dir = Path(data_dir)
        images = []
        labels = []
        
        print("加载训练数据...")
        
        for tile_class in self.tile_classes:
            class_dir = data_dir / tile_class
            if not class_dir.exists():
                print(f"警告: 找不到类别目录 {class_dir}")
                continue
            
            image_files = list(class_dir.glob("*.jpg")) + list(class_dir.glob("*.png"))
            print(f"类别 {tile_class}: {len(image_files)} 张图片")
            
            for img_file in image_files:
                img = self.preprocess_image(img_file)
                if img is not None:
                    images.append(img)
                    labels.append(tile_class)
        
        if not images:
            raise ValueError("没有找到训练图片!")
        
        # 转换为numpy数组
        X = np.array(images)
        y = self.label_encoder.transform(labels)
        y = keras.utils.to_categorical(y, len(self.tile_classes))
        
        print(f"加载完成: {len(X)} 张图片, {len(self.tile_classes)} 个类别")
        return X, y
    
    def train(self, data_dir, epochs=50, batch_size=32, validation_split=0.2):
        """训练模型"""
        # 加载数据
        X, y = self.load_training_data(data_dir)
        
        # 分割训练集和验证集
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42
        )
        
        print(f"训练集: {len(X_train)} 张, 验证集: {len(X_val)} 张")
        
        # 创建模型
        if self.model is None:
            self.create_model()
        
        # 数据增强
        datagen = keras.preprocessing.image.ImageDataGenerator(
            rotation_range=10,
            width_shift_range=0.1,
            height_shift_range=0.1,
            zoom_range=0.1,
            horizontal_flip=False,  # 麻将牌不适合水平翻转
            fill_mode='nearest'
        )
        
        # 回调函数
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_accuracy',
                patience=10,
                restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-6
            ),
            keras.callbacks.ModelCheckpoint(
                'best_mahjong_model.h5',
                monitor='val_accuracy',
                save_best_only=True
            )
        ]
        
        # 训练模型
        history = self.model.fit(
            datagen.flow(X_train, y_train, batch_size=batch_size),
            steps_per_epoch=len(X_train) // batch_size,
            epochs=epochs,
            validation_data=(X_val, y_val),
            callbacks=callbacks,
            verbose=1
        )
        
        return history
    
    def predict_tile(self, image):
        """预测单张麻将牌"""
        if isinstance(image, (str, Path)):
            image = self.preprocess_image(image)
        
        if image is None:
            return None, 0.0
        
        # 添加batch维度
        image = np.expand_dims(image, axis=0)
        
        # 预测
        predictions = self.model.predict(image)
        predicted_class = np.argmax(predictions[0])
        confidence = predictions[0][predicted_class]
        
        # 转换为类别名称
        tile_class = self.label_encoder.inverse_transform([predicted_class])[0]
        suit, value = tile_class.split('_')
        
        return {
            'suit': suit,
            'value': int(value),
            'confidence': float(confidence),
            'tile_class': tile_class
        }, confidence
    
    def save_model(self, model_path='mahjong_tile_model.h5'):
        """保存模型"""
        if self.model is not None:
            self.model.save(model_path)
            
            # 保存标签编码器
            label_mapping = {
                'classes': self.tile_classes,
                'label_encoder': self.label_encoder.classes_.tolist()
            }
            
            with open(model_path.replace('.h5', '_labels.json'), 'w') as f:
                json.dump(label_mapping, f, indent=2)
            
            print(f"模型已保存到: {model_path}")
    
    def load_model(self, model_path='mahjong_tile_model.h5'):
        """加载模型"""
        self.model = keras.models.load_model(model_path)
        
        # 加载标签编码器
        label_file = model_path.replace('.h5', '_labels.json')
        if os.path.exists(label_file):
            with open(label_file, 'r') as f:
                label_mapping = json.load(f)
                self.label_encoder.classes_ = np.array(label_mapping['label_encoder'])
        
        print(f"模型已从 {model_path} 加载")

def create_sample_training_data():
    """创建示例训练数据目录结构"""
    base_dir = Path("training_data")
    base_dir.mkdir(exist_ok=True)
    
    suits = ['wan', 'tiao', 'tong']
    values = range(1, 10)
    
    print("创建训练数据目录结构...")
    for suit in suits:
        for value in values:
            class_dir = base_dir / f"{suit}_{value}"
            class_dir.mkdir(exist_ok=True)
            
            # 创建README文件说明如何收集数据
            readme_file = class_dir / "README.md"
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(f"""# {suit}_{value} 麻将牌图片数据

## 收集说明
1. 将{value}{{'wan': '万', 'tiao': '条', 'tong': '筒'}[suit]}的图片放在此目录
2. 图片格式: JPG 或 PNG
3. 建议每个类别至少100张图片
4. 图片尺寸不限，程序会自动调整为64x64

## 数据收集方法
1. 从腾讯欢乐麻将录像中截取麻将牌图片
2. 使用自动化脚本批量提取
3. 手动标注和分类

## 注意事项
- 确保图片清晰
- 包含不同角度和光照条件
- 避免模糊或遮挡的图片
""")
    
    print(f"训练数据目录已创建: {base_dir}")
    print("请将对应的麻将牌图片放入相应的子目录中")

def main():
    """主函数"""
    # 创建示例目录结构
    create_sample_training_data()
    
    # 训练模型示例
    model = MahjongTileRecognitionModel()
    
    try:
        # 如果有训练数据，开始训练
        if Path("training_data").exists():
            print("开始训练模型...")
            model.create_model()
            print("模型结构:")
            model.model.summary()
            
            # 注意: 需要实际的训练数据才能运行
            # history = model.train("training_data", epochs=10)
            # model.save_model()
            
        print("\n=== 使用说明 ===")
        print("1. 收集麻将牌图片数据到 training_data/ 目录")
        print("2. 运行训练: python train_tile_recognition.py")
        print("3. 训练完成后可以用于视频分析")
        
    except Exception as e:
        print(f"错误: {e}")
        print("请先收集训练数据")

if __name__ == "__main__":
    main()