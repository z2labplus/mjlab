#!/usr/bin/env python3
"""
牌谱导入脚本
用于导入之前导出的牌谱文件到游戏系统中
"""

import requests
import json
import sys
import os

# API基础URL
BASE_URL = "http://localhost:8000/api/mahjong"

def test_api_connection():
    """测试API连接"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API连接正常")
            return True
        else:
            print("❌ API连接失败")
            return False
    except Exception as e:
        print(f"❌ API连接错误: {e}")
        return False

def import_game_record(filename):
    """导入牌谱文件"""
    try:
        # 检查文件是否存在
        if not os.path.exists(filename):
            print(f"❌ 文件不存在: {filename}")
            return False
        
        # 读取牌谱文件
        print(f"📖 正在读取牌谱文件: {filename}")
        with open(filename, 'r', encoding='utf-8') as f:
            game_record = json.load(f)
        
        print(f"✅ 牌谱文件读取成功")
        print(f"📊 牌谱信息:")
        if 'game_info' in game_record:
            game_info = game_record['game_info']
            print(f"   🎮 游戏ID: {game_info.get('game_id', 'N/A')}")
            print(f"   ⏰ 开始时间: {game_info.get('start_time', 'N/A')}")
            print(f"   👥 玩家数量: {game_info.get('player_count', 'N/A')}")
            print(f"   🎯 游戏模式: {game_info.get('game_mode', 'N/A')}")
        
        if 'actions' in game_record:
            print(f"   📈 操作总数: {len(game_record['actions'])}")
        
        # 发送导入请求
        print(f"\n📡 正在导入牌谱到服务器...")
        response = requests.post(
            f"{BASE_URL}/import-game-record",
            json={'game_record': game_record}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✅ 牌谱导入成功！")
                print("💡 你现在可以在前端界面查看导入的牌谱")
                print("🌐 前端地址: http://localhost:3000")
                return True
            else:
                print(f"❌ 导入失败: {result.get('message', '未知错误')}")
                return False
        else:
            print(f"❌ 导入请求失败: {response.status_code}")
            print(f"   响应内容: {response.text}")
            return False
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON格式错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 导入错误: {e}")
        return False

def list_available_records():
    """列出当前目录下的牌谱文件"""
    print("📁 当前目录下的牌谱文件:")
    record_files = []
    
    for filename in os.listdir('.'):
        if filename.startswith('game_record_') and filename.endswith('.json'):
            record_files.append(filename)
    
    if record_files:
        for i, filename in enumerate(record_files, 1):
            # 尝试读取文件信息
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    game_info = data.get('game_info', {})
                    start_time = game_info.get('start_time', 'N/A')
                    player_count = game_info.get('player_count', 'N/A')
                    actions_count = len(data.get('actions', []))
                    
                print(f"   {i}. {filename}")
                print(f"      ⏰ 时间: {start_time}")
                print(f"      👥 玩家: {player_count}人")
                print(f"      📈 操作: {actions_count}次")
                print("")
            except:
                print(f"   {i}. {filename} (无法读取详细信息)")
        
        return record_files
    else:
        print("   📭 没有找到牌谱文件")
        print("   💡 请先运行 simulate_xuezhan_game.py 生成牌谱")
        return []

def main():
    """主函数"""
    print("🀄 血战麻将牌谱导入工具 🀄")
    print("=" * 50)
    
    # 测试API连接
    if not test_api_connection():
        print("💡 请确保后端服务正在运行: python start_server.py")
        return
    
    # 如果命令行提供了文件名
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        print(f"📁 指定导入文件: {filename}")
        if import_game_record(filename):
            print("🎉 导入完成！")
        return
    
    # 列出可用的牌谱文件
    available_files = list_available_records()
    
    if not available_files:
        return
    
    # 让用户选择要导入的文件
    try:
        choice = input(f"\n请选择要导入的牌谱文件 (1-{len(available_files)})，或输入'q'退出: ")
        
        if choice.lower() == 'q':
            print("👋 再见！")
            return
        
        choice_num = int(choice)
        if 1 <= choice_num <= len(available_files):
            selected_file = available_files[choice_num - 1]
            print(f"\n📁 选择导入: {selected_file}")
            
            if import_game_record(selected_file):
                print("\n🎉 导入完成！")
                print("💡 现在可以在前端查看导入的牌谱了")
            else:
                print("\n❌ 导入失败")
        else:
            print("❌ 无效的选择")
            
    except ValueError:
        print("❌ 请输入有效的数字")
    except KeyboardInterrupt:
        print("\n👋 用户取消操作")

if __name__ == "__main__":
    main() 