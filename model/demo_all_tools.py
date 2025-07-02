#!/usr/bin/env python3
"""
手牌推导工具集综合演示
展示如何使用所有5个工具文件
"""

import subprocess
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def demo_all_tools():
    """演示所有工具的使用"""
    
    print("🎯 麻将手牌推导工具集综合演示")
    print("=" * 60)
    
    # 工具1: 原理演示
    print("\n1️⃣ 【原理演示工具】simple_hand_verification.py")
    print("   用途: 理解手牌推导的基本原理")
    print("   运行: python simple_hand_verification.py")
    print("-" * 40)
    
    try:
        result = subprocess.run(['python', 'simple_hand_verification.py'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ 运行成功！部分输出:")
            lines = result.stdout.split('\n')[:10]  # 显示前10行
            for line in lines:
                print(f"   {line}")
            print("   ...")
        else:
            print(f"❌ 运行失败: {result.stderr}")
    except Exception as e:
        print(f"❌ 无法运行: {e}")
    
    # 工具2: 可行性分析
    print("\n2️⃣ 【可行性分析工具】improved_hand_reconstruction.py")
    print("   用途: 评估数据质量和推导可行性")
    print("   运行: python improved_hand_reconstruction.py")
    print("-" * 40)
    
    try:
        result = subprocess.run(['python', 'improved_hand_reconstruction.py'], 
                              capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            print("✅ 运行成功！关键输出:")
            lines = result.stdout.split('\n')
            for line in lines:
                if any(keyword in line for keyword in ['评分', '等级', '推荐方法', '可行性']):
                    print(f"   {line}")
        else:
            print(f"❌ 运行失败: {result.stderr}")
    except Exception as e:
        print(f"❌ 无法运行: {e}")
    
    # 工具3: 创建和使用主工具
    print("\n3️⃣ 【主推导工具】hand_deduction_tool.py")
    print("   用途: 实际的手牌推导工作")
    print("   步骤: 创建模板 → 填入数据 → 运行推导")
    print("-" * 40)
    
    # 创建模板
    try:
        result = subprocess.run(['python', 'hand_deduction_tool.py', '--create_template'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ 模板创建成功!")
            print(f"   {result.stdout.strip()}")
            
            # 检查模板内容
            if Path('game_data_template.json').exists():
                print("\n📋 数据模板内容预览:")
                with open('game_data_template.json', 'r', encoding='utf-8') as f:
                    template = json.load(f)
                    
                print("   玩家数量:", len(template.get('players', {})))
                for player_id, player_data in template.get('players', {}).items():
                    print(f"   玩家{player_id}: {player_data.get('name')}")
                    print(f"     最终手牌: {len(player_data.get('final_hand', []))}张")
                    print(f"     操作记录: {len(player_data.get('actions', []))}条")
            
            # 使用模板进行推导
            print("\n🔄 使用模板数据进行推导...")
            result2 = subprocess.run(['python', 'hand_deduction_tool.py', '--input', 'game_data_template.json'], 
                                   capture_output=True, text=True, timeout=15)
            if result2.returncode == 0:
                print("✅ 推导成功！结果摘要:")
                lines = result2.stdout.split('\n')
                for line in lines:
                    if any(keyword in line for keyword in ['推导成功', '推导失败', '成功率', '初始手牌']):
                        print(f"   {line}")
            else:
                print(f"❌ 推导失败: {result2.stderr}")
        else:
            print(f"❌ 模板创建失败: {result.stderr}")
    except Exception as e:
        print(f"❌ 无法运行: {e}")
    
    # 工具4: 复杂分析器（如果有牌谱文件）
    print("\n4️⃣ 【复杂分析工具】hand_reconstruction.py")
    print("   用途: 深度分析现有牌谱文件")
    print("   需要: 现有的牌谱JSON文件")
    print("-" * 40)
    
    # 查找可用的牌谱文件
    replay_files = []
    for pattern in ['*.json', '../backend/*.json']:
        replay_files.extend(Path('.').glob(pattern))
        replay_files.extend(Path('../backend').glob('*.json'))
    
    replay_files = [f for f in replay_files if 'replay' in f.name.lower()]
    
    if replay_files:
        replay_file = replay_files[0]
        print(f"   找到牌谱文件: {replay_file}")
        try:
            result = subprocess.run(['python', 'hand_reconstruction.py', '--replay_file', str(replay_file)], 
                                  capture_output=True, text=True, timeout=20)
            if result.returncode == 0:
                print("✅ 分析成功！关键结果:")
                lines = result.stdout.split('\n')
                for line in lines[-10:]:  # 显示最后10行
                    if line.strip():
                        print(f"   {line}")
            else:
                print(f"❌ 分析失败: {result.stderr}")
        except Exception as e:
            print(f"❌ 无法运行: {e}")
    else:
        print("   ⚠️ 未找到牌谱文件，跳过此演示")
    
    # 总结
    print("\n" + "=" * 60)
    print("📈 工具集使用建议:")
    print("   🎯 日常使用: hand_deduction_tool.py (主工具)")
    print("   📚 学习原理: simple_hand_verification.py")
    print("   🔍 评估数据: improved_hand_reconstruction.py") 
    print("   🧪 深度分析: hand_reconstruction.py")
    print("   📋 数据模板: game_data_template.json")
    
    print("\n💡 使用流程:")
    print("   1. 先了解原理 (simple_hand_verification.py)")
    print("   2. 评估数据质量 (improved_hand_reconstruction.py)")
    print("   3. 准备数据并推导 (hand_deduction_tool.py)")
    print("   4. 深度分析 (hand_reconstruction.py)")
    
    print("\n📞 获取帮助:")
    print("   python hand_deduction_tool.py --help")
    print("   查看 README_hand_deduction.md")

if __name__ == "__main__":
    demo_all_tools()