#!/usr/bin/env python3
"""
快速演示脚本 - 从麻将录像提取牌谱的简化实现
用于概念验证和原型测试
"""

import cv2
import numpy as np
import json
from datetime import datetime, timedelta
import os

class QuickMahjongVideoDemo:
    """快速演示版本的麻将录像分析器"""
    
    def __init__(self, video_path):
        self.video_path = video_path
        self.game_id = f"demo_game_{int(datetime.now().timestamp())}"
        
        # 模拟的识别结果 - 实际项目中需要用真实的AI模型
        self.mock_actions = [
            {"type": "missing_suit", "player": 0, "suit": "wan"},
            {"type": "missing_suit", "player": 1, "suit": "tiao"},
            {"type": "missing_suit", "player": 2, "suit": "tong"},
            {"type": "missing_suit", "player": 3, "suit": "wan"},
            {"type": "draw", "player": 0, "card": "3万"},
            {"type": "discard", "player": 0, "card": "9万"},
            {"type": "draw", "player": 1, "card": "5条"},
            {"type": "discard", "player": 1, "card": "1条"},
            {"type": "peng", "player": 2, "card": "7筒", "from_player": 1},
            {"type": "discard", "player": 2, "card": "2筒"},
            {"type": "gang", "player": 3, "card": "东", "gang_type": "ming_gang"},
            {"type": "draw", "player": 3, "card": "5万"},
            {"type": "discard", "player": 3, "card": "8万"},
            {"type": "hu", "player": 0, "card": "4万", "win_type": "zimo"}
        ]
    
    def analyze_video_structure(self):
        """分析视频基本信息"""
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {self.video_path}")
        
        # 获取视频信息
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        cap.release()
        
        print(f"📹 视频信息:")
        print(f"   文件: {self.video_path}")
        print(f"   分辨率: {width}x{height}")
        print(f"   帧率: {fps} fps")
        print(f"   时长: {duration:.1f} 秒")
        print(f"   总帧数: {frame_count}")
        
        return {
            'fps': fps,
            'duration': duration,
            'frame_count': frame_count,
            'width': width,
            'height': height
        }
    
    def extract_sample_frames(self, count=10):
        """提取示例帧用于分析"""
        cap = cv2.VideoCapture(self.video_path)
        video_info = self.analyze_video_structure()
        
        frames = []
        frame_interval = max(1, video_info['frame_count'] // count)
        
        print(f"🖼️  提取示例帧 (每{frame_interval}帧取一帧)...")
        
        for i in range(0, video_info['frame_count'], frame_interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            
            if ret:
                timestamp = i / video_info['fps']
                frames.append({
                    'frame_number': i,
                    'timestamp': timestamp,
                    'frame': frame
                })
                
                # 保存示例帧
                output_path = f"sample_frame_{i:06d}.jpg"
                cv2.imwrite(output_path, frame)
                print(f"   保存帧 {i} -> {output_path}")
        
        cap.release()
        return frames
    
    def simulate_ai_recognition(self, frames):
        """模拟AI识别过程"""
        print("🤖 模拟AI识别麻将牌和操作...")
        
        recognized_actions = []
        start_time = datetime.now()
        
        # 模拟识别每个关键时刻的操作
        for i, action_template in enumerate(self.mock_actions):
            # 计算时间戳
            progress = i / len(self.mock_actions)
            timestamp = start_time + timedelta(seconds=progress * 300)  # 假设5分钟游戏
            
            action = {
                "sequence": i + 1,
                "timestamp": timestamp.isoformat(),
                "player_id": action_template["player"],
                "action_type": action_template["type"],
                "score_change": 0
            }
            
            # 添加特定操作的额外信息
            if "card" in action_template:
                action["card"] = action_template["card"]
            
            if "suit" in action_template:
                action["missing_suit"] = action_template["suit"]
            
            if "from_player" in action_template:
                action["target_player"] = action_template["from_player"]
            
            if "gang_type" in action_template:
                action["gang_type"] = action_template["gang_type"]
            
            recognized_actions.append(action)
            print(f"   识别操作 {i+1}: {action['action_type']} by 玩家{action['player_id']}")
        
        return recognized_actions
    
    def generate_player_data(self):
        """生成玩家数据"""
        players = []
        
        # 模拟玩家数据
        player_names = ["智能AI", "麻将高手", "新手玩家", "资深老手"]
        initial_hands = [
            ["1万", "2万", "3万", "4万", "5万", "6万", "7万", "8万", "9万", "1条", "2条", "3条", "4条"],
            ["1条", "2条", "3条", "4条", "5条", "6条", "7条", "8条", "9条", "1筒", "2筒", "3筒", "4筒"],
            ["1筒", "2筒", "3筒", "4筒", "5筒", "6筒", "7筒", "8筒", "9筒", "5万", "6万", "7万", "8万"],
            ["9万", "1万", "5条", "9条", "1筒", "9筒", "2万", "8万", "3条", "7条", "4筒", "6筒", "5万"]
        ]
        
        for i in range(4):
            player = {
                "id": i,
                "name": player_names[i],
                "position": i,
                "initial_hand": initial_hands[i],
                "missing_suit": ["wan", "tiao", "tong", "wan"][i],
                "final_score": [150, -50, -50, -50][i],  # 玩家0胜利
                "is_winner": i == 0,
                "statistics": {
                    "draw_count": [8, 6, 5, 7][i],
                    "discard_count": [7, 6, 4, 6][i],
                    "peng_count": [0, 0, 1, 0][i],
                    "gang_count": [0, 0, 0, 1][i]
                }
            }
            players.append(player)
        
        return players
    
    def create_demo_replay(self):
        """创建演示牌谱"""
        print("📋 生成牌谱数据...")
        
        # 分析视频
        video_info = self.analyze_video_structure()
        
        # 提取关键帧
        frames = self.extract_sample_frames(count=5)
        
        # 模拟识别
        actions = self.simulate_ai_recognition(frames)
        
        # 生成玩家数据
        players = self.generate_player_data()
        
        # 创建牌谱数据
        replay_data = {
            "game_info": {
                "game_id": self.game_id,
                "start_time": datetime.now().isoformat(),
                "end_time": (datetime.now() + timedelta(seconds=video_info['duration'])).isoformat(),
                "duration": int(video_info['duration']),
                "player_count": 4,
                "game_mode": "xuezhan_daodi"
            },
            "players": players,
            "actions": actions,
            "metadata": {
                "source": "video_analysis_demo",
                "video_path": self.video_path,
                "video_info": video_info,
                "processing_time": datetime.now().isoformat(),
                "ai_confidence": 0.85,  # 模拟识别置信度
                "note": "这是演示数据，实际项目需要真实的AI识别"
            }
        }
        
        return replay_data
    
    def save_replay(self, replay_data, output_path=None):
        """保存牌谱文件"""
        if output_path is None:
            output_path = f"demo_replay_{self.game_id}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(replay_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 牌谱已保存: {output_path}")
        
        # 显示统计信息
        print(f"📊 牌谱统计:")
        print(f"   游戏ID: {replay_data['game_info']['game_id']}")
        print(f"   时长: {replay_data['game_info']['duration']} 秒")
        print(f"   操作数: {len(replay_data['actions'])}")
        print(f"   胜利者: {[p['name'] for p in replay_data['players'] if p['is_winner']]}")
        
        return output_path

def create_sample_video():
    """创建示例视频文件（如果不存在）"""
    sample_video = "sample_mahjong_game.mp4"
    
    if not os.path.exists(sample_video):
        print("📹 创建示例视频文件...")
        
        # 创建一个简单的测试视频
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(sample_video, fourcc, 30.0, (1280, 720))
        
        # 生成300帧 (10秒的视频)
        for i in range(300):
            # 创建一个带有文字的帧
            frame = np.zeros((720, 1280, 3), dtype=np.uint8)
            frame[:] = (0, 50, 0)  # 深绿色背景
            
            # 添加文字
            text = f"Mahjong Game Frame {i+1}"
            cv2.putText(frame, text, (400, 360), cv2.FONT_HERSHEY_SIMPLEX, 
                       2, (255, 255, 255), 3)
            
            # 模拟麻将桌面
            cv2.rectangle(frame, (200, 150), (1080, 570), (0, 100, 0), -1)
            cv2.putText(frame, "Tencent Happy Mahjong", (300, 200), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            out.write(frame)
        
        out.release()
        print(f"✅ 示例视频已创建: {sample_video}")
    
    return sample_video

def main():
    """主演示函数"""
    print("🎮 腾讯欢乐麻将录像转牌谱 - 快速演示")
    print("=" * 50)
    
    # 创建或使用示例视频
    video_path = create_sample_video()
    
    try:
        # 创建分析器
        demo = QuickMahjongVideoDemo(video_path)
        
        print("\n🚀 开始分析录像...")
        
        # 生成演示牌谱
        replay_data = demo.create_demo_replay()
        
        # 保存结果
        output_file = demo.save_replay(replay_data)
        
        print(f"\n✅ 演示完成!")
        print(f"📁 生成的文件:")
        print(f"   - 牌谱文件: {output_file}")
        print(f"   - 示例帧: sample_frame_*.jpg")
        
        print(f"\n📝 下一步:")
        print(f"   1. 将 {output_file} 导入到牌谱回放网站")
        print(f"   2. 查看生成的示例帧图片")
        print(f"   3. 基于这个框架开发真实的AI识别功能")
        
        print(f"\n🔧 实际项目需要:")
        print(f"   - 训练麻将牌识别模型")
        print(f"   - 实现真实的视频分析算法")
        print(f"   - 优化识别准确率和处理速度")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        print("请检查视频文件是否存在且格式正确")

if __name__ == "__main__":
    main()