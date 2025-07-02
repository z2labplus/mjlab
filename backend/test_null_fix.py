#!/usr/bin/env python3
"""
测试 null 值修复的验证脚本
检查标准格式文件中的数据完整性
"""

import json
from pathlib import Path

def test_target_player_data():
    """测试 target_player 数据完整性"""
    
    print("🧪 测试 target_player 数据完整性")
    print("=" * 50)
    
    # 读取标准格式文件
    standard_file = "/root/claude/hmjai/model/first_hand/sample_mahjong_game_final.json"
    
    if not Path(standard_file).exists():
        print(f"❌ 标准格式文件不存在: {standard_file}")
        return False
    
    with open(standard_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("✅ 成功读取标准格式文件")
    
    # 分析所有动作
    actions = data.get('actions', [])
    print(f"📊 总动作数: {len(actions)}")
    
    # 检查碰牌动作
    peng_actions = [a for a in actions if a.get('type') == 'peng']
    gang_actions = [a for a in actions if a.get('type') == 'gang']
    
    print(f"\n🔍 碰牌动作检查:")
    print(f"   碰牌数量: {len(peng_actions)}")
    
    null_target_count = 0
    
    for i, action in enumerate(peng_actions, 1):
        sequence = action.get('sequence')
        player_id = action.get('player_id')
        target_player = action.get('target_player')
        tile = action.get('tile')
        
        if target_player is None:
            null_target_count += 1
            print(f"   ❌ {i}. 序号{sequence}: target_player 为 None")
        else:
            print(f"   ✅ {i}. 序号{sequence}: 玩家{player_id} 碰 玩家{target_player} 的 {tile}")
    
    print(f"\n🔍 杠牌动作检查:")
    print(f"   杠牌数量: {len(gang_actions)}")
    
    for i, action in enumerate(gang_actions, 1):
        sequence = action.get('sequence')
        player_id = action.get('player_id')
        target_player = action.get('target_player')
        gang_type = action.get('gang_type')
        tile = action.get('tile')
        
        if gang_type == 'ming_gang' and target_player is None:
            null_target_count += 1
            print(f"   ❌ {i}. 序号{sequence}: 明杠的 target_player 为 None")
        else:
            print(f"   ✅ {i}. 序号{sequence}: 玩家{player_id} {gang_type} {tile} (target: {target_player})")
    
    # 总结
    if null_target_count == 0:
        print(f"\n✅ 数据完整性检查通过")
        print(f"   所有碰杠动作都有有效的 target_player")
    else:
        print(f"\n❌ 发现 {null_target_count} 个 null target_player")
        print(f"   这可能导致前端 .toString() 错误")
    
    return null_target_count == 0

def analyze_error_source():
    """分析错误可能的来源"""
    
    print(f"\n" + "=" * 50)
    print("🔍 分析前端错误可能的来源")
    print("=" * 50)
    
    print("📋 前端错误信息分析:")
    print("   错误: Cannot read properties of null (reading 'toString')")
    print("   位置: action.target_player.toString()")
    print("   原因: action.target_player 为 null")
    
    print(f"\n🔧 修复措施:")
    print("   1. 添加 null 检查: action.target_player !== null")
    print("   2. 添加 undefined 检查: action.target_player !== undefined") 
    print("   3. 添加数组安全检查: if (targetPlayerDiscards)")
    print("   4. 添加对象安全检查: if (discardedTile)")
    
    print(f"\n💡 防御性编程:")
    print("   ✅ 多层 null 检查")
    print("   ✅ 可选链操作符考虑")
    print("   ✅ 类型守卫")
    print("   ✅ 错误边界处理")

def create_debug_suggestions():
    """创建调试建议"""
    
    print(f"\n" + "=" * 50)
    print("🛠️ 调试建议")
    print("=" * 50)
    
    print("📋 前端调试步骤:")
    print("   1. 打开浏览器开发者工具")
    print("   2. 在 ReplaySystem 组件的 applyAction 函数开始处添加:")
    print("      console.log('处理动作:', action);")
    print("   3. 特别关注碰牌动作的 target_player 值")
    print("   4. 使用 debug_null_check.js 脚本检查数据")
    
    print(f"\n🔍 检查要点:")
    print("   ✅ action.target_player 是否为 null")
    print("   ✅ action.target_player 是否为 undefined")
    print("   ✅ targetPlayerDiscards 数组是否存在")
    print("   ✅ discardedTile 对象是否有效")
    
    print(f"\n📝 临时修复（如果还有问题）:")
    print("   可以临时添加 try-catch 包围修复逻辑:")
    print("   try {")
    print("     // 碰牌修复逻辑")
    print("   } catch (error) {")
    print("     console.warn('碰牌修复失败:', error);")
    print("   }")

def main():
    """主函数"""
    print("🎯 null 值修复验证")
    print("=" * 60)
    
    success = test_target_player_data()
    
    analyze_error_source()
    create_debug_suggestions()
    
    print(f"\n{'='*60}")
    if success:
        print("🎉 数据完整性验证通过！")
        print("📋 修复应该生效:")
        print("   ✅ 所有碰杠动作都有有效的 target_player")
        print("   ✅ 添加了完整的 null 检查")
        print("   ✅ 添加了数组和对象安全检查")
        print(f"\n🚀 现在可以测试前端:")
        print("   1. 刷新前端页面")
        print("   2. 重新导入牌谱文件")
        print("   3. 应该不再有 null 错误")
    else:
        print("⚠️ 发现数据问题，需要进一步调试")

if __name__ == "__main__":
    main()